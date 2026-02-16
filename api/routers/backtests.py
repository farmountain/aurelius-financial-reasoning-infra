"""Backtest management router."""
import time
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Depends
from typing import Optional
from sqlalchemy.orm import Session
import sys
import os
import asyncio

# Add paths for imports
sys.path.insert(0, os.path.dirname(__file__))

from schemas.backtest import (
    BacktestRequest,
    BacktestResult,
    BacktestMetrics,
    BacktestListResponse,
    BacktestDetailResponse,
)
from database.session import get_db
from database.crud import BacktestDB, StrategyDB
from database.models import Backtest, Validation, GateResult
from websocket.manager import manager
from security.dependencies import get_current_user
from security.auth import TokenData
from services.engine_backtest import run_engine_backtest
from config import settings

router = APIRouter(prefix="/api/v1/backtests", tags=["backtests"])


def _run_backtest(backtest_id: str, request: BacktestRequest, db: Session):
    """Run backtest in background with database persistence."""
    start_time = time.time()

    try:
        if not getattr(settings, "enable_truth_backtests", True):
            raise RuntimeError("Truth backtest execution is disabled by rollout flag")

        # Update status to running
        BacktestDB.update_running(db, backtest_id)

        # Broadcast start event
        asyncio.create_task(manager.broadcast({
            "event": "backtest_started",
            "payload": {
                "backtest_id": backtest_id,
                "strategy_id": request.strategy_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }, event_type="backtest_started"))

        strategy = StrategyDB.get(db, request.strategy_id)
        if not strategy:
            raise RuntimeError(f"Strategy not found: {request.strategy_id}")

        strategy_dict = {
            "id": strategy.id,
            "strategy_type": strategy.strategy_type,
            "parameters": strategy.parameters or {},
        }
        request_dict = {
            "initial_capital": request.initial_capital,
            "instruments": request.instruments,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "seed": request.seed,
            "data_source": request.data_source,
        }

        run_result = run_engine_backtest(
            strategy=strategy_dict,
            request_data=request_dict,
            run_replay_check=getattr(settings, "enable_replay_check", True),
        )

        metrics_dict = run_result.metrics

        duration = time.time() - start_time

        # Update with results
        BacktestDB.update_completed(db, backtest_id, metrics_dict, duration)

        backtest_row = BacktestDB.get(db, backtest_id)
        if backtest_row:
            backtest_row.trades = run_result.trades
            backtest_row.equity_curve = run_result.equity_curve
            db.commit()

        # Broadcast completion event
        asyncio.create_task(manager.broadcast({
            "event": "backtest_completed",
            "payload": {
                "backtest_id": backtest_id,
                "strategy_id": request.strategy_id,
                "metrics": metrics_dict,
                "duration": duration,
                "timestamp": datetime.utcnow().isoformat()
            }
        }, event_type="backtest_completed"))

    except Exception as e:
        BacktestDB.update_failed(db, backtest_id, str(e))

        # Broadcast error event
        asyncio.create_task(manager.broadcast({
            "event": "backtest_failed",
            "payload": {
                "backtest_id": backtest_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        }, event_type="backtest_failed"))


@router.post("/run", response_model=dict)
async def run_backtest(request: BacktestRequest, background_tasks: BackgroundTasks,
                      current_user: TokenData = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    """Run a backtest for a strategy."""
    # Create backtest record in database
    backtest_db = BacktestDB.create(db, request.strategy_id, {
        "start_date": request.start_date,
        "end_date": request.end_date,
        "initial_capital": request.initial_capital,
        "instruments": request.instruments,
        "seed": request.seed,
        "data_source": request.data_source,
    })

    backtest_id = backtest_db.id

    # Start backtest in background
    background_tasks.add_task(_run_backtest, backtest_id, request, db)

    return {
        "backtest_id": backtest_id,
        "status": "running",
        "message": "Backtest started",
        "execution_metadata": {
            "seed": request.seed,
            "data_source": request.data_source,
        },
        "created_at": datetime.utcnow().isoformat(),
    }


@router.get("/{backtest_id}/status")
async def get_backtest_status(backtest_id: str, current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db)):
    """Check status of a backtest."""
    backtest_db = BacktestDB.get(db, backtest_id)

    if not backtest_db:
        raise HTTPException(
            status_code=404,
            detail=f"Backtest {backtest_id} not found"
        )

    response = {
        "backtest_id": backtest_id,
        "status": backtest_db.status,
        "execution_metadata": {
            "seed": backtest_db.seed,
            "data_source": backtest_db.data_source,
        },
    }

    if backtest_db.status == "completed" and backtest_db.metrics:
        response["result"] = {
            "backtest_id": backtest_id,
            "strategy_id": backtest_db.strategy_id,
            "status": backtest_db.status,
            "metrics": backtest_db.metrics,
            "execution_mode": backtest_db.metrics.get("execution_mode") if isinstance(backtest_db.metrics, dict) else None,
            "start_date": backtest_db.start_date,
            "end_date": backtest_db.end_date,
            "completed_at": backtest_db.completed_at.isoformat(),
            "duration_seconds": backtest_db.duration_seconds,
        }

    return response


@router.get("/audit/replay")
async def audit_replay(
    spec_hash: str,
    data_hash: str,
    seed: str,
    engine_version: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reconstruct run evidence from canonical run identity."""
    backtests = db.query(Backtest).filter(Backtest.status == "completed").all()

    match = None
    for bt in backtests:
        metrics = bt.metrics if isinstance(bt.metrics, dict) else {}
        run_identity = metrics.get("run_identity") if isinstance(metrics.get("run_identity"), dict) else {}
        if (
            run_identity.get("spec_hash") == spec_hash
            and run_identity.get("data_hash") == data_hash
            and str(run_identity.get("seed")) == str(seed)
            and run_identity.get("engine_version") == engine_version
        ):
            match = bt
            break

    if not match:
        raise HTTPException(status_code=404, detail="No run found for provided canonical run identity")

    latest_validation = db.query(Validation).filter(
        Validation.strategy_id == match.strategy_id,
        Validation.status == "completed",
    ).order_by(Validation.completed_at.desc()).first()

    latest_product_gate = db.query(GateResult).filter(
        GateResult.strategy_id == match.strategy_id,
        GateResult.gate_type == "product",
    ).order_by(GateResult.timestamp.desc()).first()

    return {
        "backtest_id": match.id,
        "strategy_id": match.strategy_id,
        "run_identity": match.metrics.get("run_identity") if isinstance(match.metrics, dict) else None,
        "metrics": match.metrics,
        "trades": match.trades,
        "equity_curve": match.equity_curve,
        "validation": {
            "validation_id": latest_validation.id,
            "passed": latest_validation.passed,
            "metrics": latest_validation.metrics,
        } if latest_validation else None,
        "product_gate": {
            "gate_result_id": latest_product_gate.id,
            "passed": latest_product_gate.passed,
            "results": latest_product_gate.results,
        } if latest_product_gate else None,
    }


@router.get("/{backtest_id}", response_model=BacktestDetailResponse)
async def get_backtest(
    backtest_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get details for a completed backtest."""
    backtest_db = BacktestDB.get(db, backtest_id)

    if not backtest_db:
        raise HTTPException(
            status_code=404,
            detail=f"Backtest {backtest_id} not found"
        )

    if backtest_db.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Backtest is {backtest_db.status}"
        )

    result = BacktestResult(
        backtest_id=backtest_db.id,
        strategy_id=backtest_db.strategy_id,
        status=backtest_db.status,
        metrics=BacktestMetrics(**backtest_db.metrics),
        start_date=backtest_db.start_date,
        end_date=backtest_db.end_date,
        completed_at=backtest_db.completed_at.isoformat(),
        duration_seconds=backtest_db.duration_seconds or 0,
    )

    return BacktestDetailResponse(
        backtest=result,
        trades=backtest_db.trades,
        equity_curve=backtest_db.equity_curve,
    )


@router.get("/", response_model=BacktestListResponse)
async def list_backtests(
    strategy_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List backtests, optionally filtered by strategy."""

    if strategy_id:
        backtests_db, total = BacktestDB.list_by_strategy(db, strategy_id, skip, limit)
    else:
        backtests_db, total = BacktestDB.list_all(db, skip, limit)

    backtests = []
    for bt in backtests_db:
        if bt.status == "completed" and bt.metrics:
            result = BacktestResult(
                backtest_id=bt.id,
                strategy_id=bt.strategy_id,
                status=bt.status,
                metrics=BacktestMetrics(**bt.metrics),
                start_date=bt.start_date,
                end_date=bt.end_date,
                completed_at=bt.completed_at.isoformat(),
                duration_seconds=bt.duration_seconds or 0,
            )
            backtests.append(result)

    return BacktestListResponse(
        total=total,
        backtests=backtests,
    )
