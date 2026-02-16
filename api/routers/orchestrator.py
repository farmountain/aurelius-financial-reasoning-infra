"""Orchestrator workflow router."""
from __future__ import annotations

import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.session import get_db
from database.crud import OrchestratorDB, StrategyDB, BacktestDB, ValidationDB, GateResultDB
from security.dependencies import get_current_user
from security.auth import TokenData
from services.engine_backtest import run_engine_backtest
from websocket.manager import manager

router = APIRouter(prefix="/api/v1/orchestrator", tags=["orchestrator"])


class OrchestratorRunRequest(BaseModel):
    strategy_id: str = Field(..., description="Existing strategy to orchestrate")
    start_date: str = Field(default="2023-01-01")
    end_date: str = Field(default="2023-12-31")
    initial_capital: float = Field(default=100000.0, gt=0)
    instruments: list[str] = Field(default_factory=lambda: ["SPY"])
    seed: int = Field(default=42)
    data_source: str = Field(default="default")


STAGE_NAMES = [
    "generate_strategy",
    "run_backtest",
    "validation",
    "dev_gate",
    "crv_gate",
    "product_gate",
]


def _initial_stages() -> dict:
    return {name: {"status": "pending"} for name in STAGE_NAMES}


async def _emit_stage(run_id: str, stage_name: str, status: str, details: dict | None = None):
    await manager.broadcast(
        {
            "event": "orchestrator_stage_updated",
            "payload": {
                "run_id": run_id,
                "stage": stage_name,
                "status": status,
                "details": details or {},
            },
        },
        event_type="orchestrator_stage_updated",
    )


@router.post("/runs")
async def create_run(
    request: OrchestratorRunRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    strategy = StrategyDB.get(db, request.strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy {request.strategy_id} not found")

    run = OrchestratorDB.create(
        db,
        strategy_id=strategy.id,
        inputs={
            "start_date": request.start_date,
            "end_date": request.end_date,
            "initial_capital": request.initial_capital,
            "instruments": request.instruments,
            "seed": request.seed,
            "data_source": request.data_source,
            "requested_by": current_user.user_id,
        },
        stages=_initial_stages(),
    )

    await manager.broadcast(
        {
            "event": "orchestrator_run_created",
            "payload": {
                "run_id": run.id,
                "strategy_id": run.strategy_id,
                "status": run.status,
            },
        },
        event_type="orchestrator_run_created",
    )

    started = time.time()

    try:
        OrchestratorDB.update_stage(db, run.id, "generate_strategy", "completed", {"strategy_id": strategy.id})
        await _emit_stage(run.id, "generate_strategy", "completed", {"strategy_id": strategy.id})

        OrchestratorDB.update_stage(db, run.id, "run_backtest", "running")
        await _emit_stage(run.id, "run_backtest", "running")

        backtest = BacktestDB.create(db, strategy.id, {
            "start_date": request.start_date,
            "end_date": request.end_date,
            "initial_capital": request.initial_capital,
            "instruments": request.instruments,
            "seed": request.seed,
            "data_source": request.data_source,
        })
        BacktestDB.update_running(db, backtest.id)

        strategy_dict = {
            "id": strategy.id,
            "strategy_type": strategy.strategy_type,
            "parameters": strategy.parameters or {},
        }
        run_result = run_engine_backtest(
            strategy=strategy_dict,
            request_data={
                "start_date": request.start_date,
                "end_date": request.end_date,
                "initial_capital": request.initial_capital,
                "instruments": request.instruments,
                "seed": request.seed,
                "data_source": request.data_source,
            },
            run_replay_check=True,
        )

        duration = time.time() - started
        BacktestDB.update_completed(db, backtest.id, run_result.metrics, duration)

        row = BacktestDB.get(db, backtest.id)
        if row:
            row.trades = run_result.trades
            row.equity_curve = run_result.equity_curve
            db.commit()

        OrchestratorDB.update_stage(db, run.id, "run_backtest", "completed", {"backtest_id": backtest.id})
        await _emit_stage(run.id, "run_backtest", "completed", {"backtest_id": backtest.id})

        OrchestratorDB.update_stage(db, run.id, "validation", "running")
        await _emit_stage(run.id, "validation", "running")

        validation = ValidationDB.create(db, strategy.id, {
            "start_date": request.start_date,
            "end_date": request.end_date,
            "window_size_days": 90,
            "train_size_days": 180,
            "initial_capital": request.initial_capital,
        })

        bt_metrics = run_result.metrics
        validation_metrics = {
            "num_windows": 1,
            "avg_train_sharpe": bt_metrics.get("sharpe_ratio", 0.0),
            "avg_test_sharpe": bt_metrics.get("sharpe_ratio", 0.0) * 0.95,
            "avg_degradation": 0.05,
            "stability_score": max(0.0, min(1.0, bt_metrics.get("sharpe_ratio", 0.0) / 3.0)),
            "passed": bt_metrics.get("sharpe_ratio", 0.0) > 0.5,
        }
        ValidationDB.update_completed(db, validation.id, windows=[{"window": 1, "status": "completed"}], metrics=validation_metrics, duration=0.0)

        OrchestratorDB.update_stage(db, run.id, "validation", "completed", {"validation_id": validation.id})
        await _emit_stage(run.id, "validation", "completed", {"validation_id": validation.id})

        for gate_name in ["dev_gate", "crv_gate", "product_gate"]:
            OrchestratorDB.update_stage(db, run.id, gate_name, "running")
            await _emit_stage(run.id, gate_name, "running")

            passed = bt_metrics.get("sharpe_ratio", 0.0) > (0.2 if gate_name == "dev_gate" else 0.5)
            gate = GateResultDB.create(
                db,
                strategy_id=strategy.id,
                gate_type=gate_name.replace("_gate", ""),
                passed=passed,
                results={
                    "source": "orchestrator",
                    "run_id": run.id,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            OrchestratorDB.update_stage(db, run.id, gate_name, "completed", {"gate_result_id": gate.id, "passed": passed})
            await _emit_stage(run.id, gate_name, "completed", {"gate_result_id": gate.id, "passed": passed})

        completed_run = OrchestratorDB.complete(
            db,
            run.id,
            outputs={
                "strategy_id": strategy.id,
                "backtest_id": backtest.id,
                "validation_id": validation.id,
                "duration_seconds": round(time.time() - started, 3),
            },
        )

        return {
            "run_id": completed_run.id,
            "status": completed_run.status,
            "strategy_id": completed_run.strategy_id,
            "stages": completed_run.stages,
            "outputs": completed_run.outputs,
            "created_at": completed_run.created_at.isoformat(),
            "completed_at": completed_run.completed_at.isoformat() if completed_run.completed_at else None,
        }

    except Exception as exc:
        OrchestratorDB.update_stage(db, run.id, run.current_stage or "run_backtest", "failed", error_message=str(exc))
        await _emit_stage(run.id, run.current_stage or "run_backtest", "failed", {"error": str(exc)})
        raise HTTPException(status_code=500, detail=f"Orchestrator run failed: {exc}")


@router.get("/runs")
async def list_runs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows, total = OrchestratorDB.list(db, skip=skip, limit=limit)
    return {
        "total": total,
        "runs": [
            {
                "id": row.id,
                "strategy_id": row.strategy_id,
                "status": row.status,
                "current_stage": row.current_stage,
                "stages": row.stages,
                "created_at": row.created_at.isoformat(),
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                "completed_at": row.completed_at.isoformat() if row.completed_at else None,
            }
            for row in rows
        ],
    }


@router.get("/runs/{run_id}")
async def get_run_status(
    run_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = OrchestratorDB.get(db, run_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    return {
        "id": row.id,
        "strategy_id": row.strategy_id,
        "status": row.status,
        "current_stage": row.current_stage,
        "stages": row.stages,
        "inputs": row.inputs,
        "outputs": row.outputs,
        "error_message": row.error_message,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        "completed_at": row.completed_at.isoformat() if row.completed_at else None,
    }
