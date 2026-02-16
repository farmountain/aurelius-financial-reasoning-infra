"""Validation/walk-forward router."""
import time
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Depends
from typing import Optional
from sqlalchemy.orm import Session
import sys
import os
from datetime import timedelta

# Add paths for imports
sys.path.insert(0, os.path.dirname(__file__))

from schemas.validation import (
    ValidationRequest,
    ValidationResult,
    ValidationMetrics,
    WindowResults,
    ValidationListResponse,
)
from database.session import get_db
from database.crud import ValidationDB, StrategyDB
from services.engine_backtest import run_engine_backtest
from config import settings
from security.dependencies import get_current_user
from security.auth import TokenData

router = APIRouter(prefix="/api/v1/validation", tags=["validation"])


def _run_validation(validation_id: str, request: ValidationRequest, db: Session):
    """Run walk-forward validation in background."""
    start_time = time.time()

    try:
        if not getattr(settings, "enable_truth_validation", True):
            raise RuntimeError("Truth validation execution is disabled by rollout flag")

        # Mark as running
        validation_db = ValidationDB.get(db, validation_id)
        validation_db.status = "running"
        db.commit()

        strategy = StrategyDB.get(db, request.strategy_id)
        if not strategy:
            raise RuntimeError(f"Strategy not found: {request.strategy_id}")

        strategy_dict = {
            "id": strategy.id,
            "strategy_type": strategy.strategy_type,
            "parameters": strategy.parameters or {},
        }

        # Parse dates
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(request.end_date, "%Y-%m-%d")
        total_days = (end_date - start_date).days

        # Calculate number of windows
        window_step = request.window_size_days
        num_windows = max(1, (total_days - request.train_size_days) // window_step)

        windows: list[dict] = []
        degradations: list[float] = []

        for i in range(num_windows):
            offset = i * window_step

            train_start = start_date + timedelta(days=offset)
            train_end = train_start + timedelta(days=request.train_size_days)
            test_start = train_end
            test_end = test_start + timedelta(days=request.window_size_days)

            if test_end > end_date:
                break

            train_result = run_engine_backtest(
                strategy=strategy_dict,
                request_data={
                    "start_date": train_start.strftime("%Y-%m-%d"),
                    "end_date": train_end.strftime("%Y-%m-%d"),
                    "initial_capital": request.initial_capital,
                    "instruments": [strategy.parameters.get("symbol", "SPY")],
                },
                run_replay_check=False,
            )

            test_result = run_engine_backtest(
                strategy=strategy_dict,
                request_data={
                    "start_date": test_start.strftime("%Y-%m-%d"),
                    "end_date": test_end.strftime("%Y-%m-%d"),
                    "initial_capital": request.initial_capital,
                    "instruments": [strategy.parameters.get("symbol", "SPY")],
                },
                run_replay_check=False,
            )

            train_sharpe = float(train_result.metrics.get("sharpe_ratio", 0.0))
            test_sharpe = float(test_result.metrics.get("sharpe_ratio", 0.0))
            degradation = ((train_sharpe - test_sharpe) / abs(train_sharpe) * 100.0) if train_sharpe != 0 else 0.0
            degradations.append(degradation)

            window = {
                "window_id": i,
                "train_start": train_start.strftime("%Y-%m-%d"),
                "train_end": train_end.strftime("%Y-%m-%d"),
                "test_start": test_start.strftime("%Y-%m-%d"),
                "test_end": test_end.strftime("%Y-%m-%d"),
                "train_sharpe": train_sharpe,
                "test_sharpe": test_sharpe,
                "train_return": float(train_result.metrics.get("total_return", 0.0)),
                "test_return": float(test_result.metrics.get("total_return", 0.0)),
                "train_drawdown": float(train_result.metrics.get("max_drawdown", 0.0)),
                "test_drawdown": float(test_result.metrics.get("max_drawdown", 0.0)),
                "degradation": degradation,
                "train_run_identity": train_result.run_identity,
                "test_run_identity": test_result.run_identity,
            }
            windows.append(window)

        if not windows:
            raise RuntimeError("No validation windows were generated for the requested period")

        # Calculate summary metrics
        avg_degradation = sum(degradations) / len(degradations) if degradations else 0
        stability_score = max(0, 100 - (avg_degradation * 1.2))
        passed = stability_score >= 75.0

        duration = time.time() - start_time

        metrics = {
            "num_windows": len(windows),
            "avg_train_sharpe": sum(w["train_sharpe"] for w in windows) / len(windows),
            "avg_test_sharpe": sum(w["test_sharpe"] for w in windows) / len(windows),
            "avg_degradation": avg_degradation,
            "stability_score": stability_score,
            "passed": passed,
        }

        # Update database
        ValidationDB.update_completed(db, validation_id, windows, metrics, duration)

    except Exception as e:
        ValidationDB.update_failed(db, validation_id, str(e))


@router.post("/run", response_model=dict)
async def run_validation(request: ValidationRequest, background_tasks: BackgroundTasks,
                        current_user: TokenData = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    """Run walk-forward validation for a strategy."""
    # Create validation record in database
    validation_db = ValidationDB.create(db, request.strategy_id, {
        "start_date": request.start_date,
        "end_date": request.end_date,
        "window_size_days": request.window_size_days,
        "train_size_days": request.train_size_days,
        "initial_capital": request.initial_capital,
    })

    validation_id = validation_db.id

    background_tasks.add_task(_run_validation, validation_id, request, db)

    return {
        "validation_id": validation_id,
        "status": "running",
        "message": "Validation started",
        "created_at": datetime.utcnow().isoformat(),
    }


@router.get("/{validation_id}/status")
async def get_validation_status(
    validation_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check status of a validation."""
    validation_db = ValidationDB.get(db, validation_id)

    if not validation_db:
        raise HTTPException(
            status_code=404,
            detail=f"Validation {validation_id} not found"
        )

    response = {
        "validation_id": validation_id,
        "status": validation_db.status,
    }

    if validation_db.status == "completed" and validation_db.metrics:
        response["result"] = {
            "validation_id": validation_id,
            "strategy_id": validation_db.strategy_id,
            "status": validation_db.status,
            "windows": validation_db.windows,
            "metrics": validation_db.metrics,
            "start_date": validation_db.start_date,
            "end_date": validation_db.end_date,
            "completed_at": validation_db.completed_at.isoformat(),
            "duration_seconds": validation_db.duration_seconds,
        }

    return response


@router.get("/{validation_id}", response_model=ValidationResult)
async def get_validation(
    validation_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get details for a validation."""
    validation_db = ValidationDB.get(db, validation_id)

    if not validation_db:
        raise HTTPException(
            status_code=404,
            detail=f"Validation {validation_id} not found"
        )

    if validation_db.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Validation is {validation_db.status}"
        )

    # Convert windows from stored format
    windows = []
    for w in validation_db.windows:
        windows.append(WindowResults(**w))

    metrics = ValidationMetrics(**validation_db.metrics)

    return ValidationResult(
        validation_id=validation_id,
        strategy_id=validation_db.strategy_id,
        status=validation_db.status,
        windows=windows,
        metrics=metrics,
        start_date=validation_db.start_date,
        end_date=validation_db.end_date,
        completed_at=validation_db.completed_at.isoformat(),
        duration_seconds=validation_db.duration_seconds or 0,
    )


@router.get("/", response_model=ValidationListResponse)
async def list_validations(
    strategy_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List validations, optionally filtered by strategy."""

    if strategy_id:
        validations_db, total = ValidationDB.list_by_strategy(db, strategy_id, skip, limit)
    else:
        validations_db, total = ValidationDB.list_all(db, skip, limit)

    validations = []
    for v in validations_db:
        if v.status == "completed" and v.metrics:
            windows = []
            for w in v.windows:
                windows.append(WindowResults(**w))

            metrics = ValidationMetrics(**v.metrics)

            result = ValidationResult(
                validation_id=v.id,
                strategy_id=v.strategy_id,
                status=v.status,
                windows=windows,
                metrics=metrics,
                start_date=v.start_date,
                end_date=v.end_date,
                completed_at=v.completed_at.isoformat(),
                duration_seconds=v.duration_seconds or 0,
            )
            validations.append(result)

    return ValidationListResponse(
        total=total,
        validations=validations,
    )
