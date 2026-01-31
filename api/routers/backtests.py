"""Backtest management router."""
import uuid
import time
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Depends
from typing import Optional
from sqlalchemy.orm import Session
import sys
import os

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
from database.crud import BacktestDB

router = APIRouter(prefix="/api/v1/backtests", tags=["backtests"])


def _run_backtest(backtest_id: str, request: BacktestRequest, db: Session):
    """Run backtest in background with database persistence."""
    start_time = time.time()
    
    try:
        # Update status to running
        BacktestDB.update_running(db, backtest_id)
        
        # Simulate backtest computation
        import random
        
        # Generate mock metrics
        base_return = random.uniform(5, 25)
        sharpe = random.uniform(0.8, 2.5)
        max_dd = -random.uniform(8, 20)
        win_rate = random.uniform(45, 65)
        
        metrics_dict = {
            "total_return": base_return,
            "sharpe_ratio": sharpe,
            "sortino_ratio": sharpe * 1.2,
            "max_drawdown": max_dd,
            "win_rate": win_rate,
            "profit_factor": random.uniform(1.2, 2.5),
            "total_trades": random.randint(50, 200),
            "avg_trade": base_return / 100,
            "calmar_ratio": sharpe / abs(max_dd) if max_dd != 0 else 0,
        }
        
        duration = time.time() - start_time
        
        # Update with results
        BacktestDB.update_completed(db, backtest_id, metrics_dict, duration)
        
    except Exception as e:
        BacktestDB.update_failed(db, backtest_id, str(e))


@router.post("/run", response_model=dict)
async def run_backtest(request: BacktestRequest, background_tasks: BackgroundTasks, 
                      db: Session = Depends(get_db)):
    """Run a backtest for a strategy."""
    # Create backtest record in database
    backtest_db = BacktestDB.create(db, request.strategy_id, {
        "start_date": request.start_date,
        "end_date": request.end_date,
        "initial_capital": request.initial_capital,
        "instruments": request.instruments,
    })
    
    backtest_id = backtest_db.id
    
    # Start backtest in background
    background_tasks.add_task(_run_backtest, backtest_id, request, db)
    
    return {
        "backtest_id": backtest_id,
        "status": "running",
        "message": "Backtest started",
        "created_at": datetime.utcnow().isoformat(),
    }


@router.get("/{backtest_id}/status")
async def get_backtest_status(backtest_id: str, db: Session = Depends(get_db)):
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
    }
    
    if backtest_db.status == "completed" and backtest_db.metrics:
        response["result"] = {
            "backtest_id": backtest_id,
            "strategy_id": backtest_db.strategy_id,
            "status": backtest_db.status,
            "metrics": backtest_db.metrics,
            "start_date": backtest_db.start_date,
            "end_date": backtest_db.end_date,
            "completed_at": backtest_db.completed_at.isoformat(),
            "duration_seconds": backtest_db.duration_seconds,
        }
    
    return response


@router.get("/{backtest_id}", response_model=BacktestDetailResponse)
async def get_backtest(backtest_id: str, db: Session = Depends(get_db)):
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
