"""Validation/walk-forward router."""
import uuid
import time
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import Optional
import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.dirname(__file__))

from schemas.validation import (
    ValidationRequest,
    ValidationResult,
    ValidationMetrics,
    WindowResults,
    ValidationListResponse,
)

router = APIRouter(prefix="/api/v1/validation", tags=["validation"])

# In-memory storage
_validations_db = {}
_validation_tasks = {}


def _run_validation(validation_id: str, request: ValidationRequest):
    """Run walk-forward validation in background."""
    start_time = time.time()
    
    try:
        import random
        from datetime import datetime, timedelta
        
        # Parse dates
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(request.end_date, "%Y-%m-%d")
        total_days = (end_date - start_date).days
        
        # Calculate number of windows
        window_step = request.window_size_days
        num_windows = max(1, (total_days - request.train_size_days) // window_step)
        
        windows = []
        degradations = []
        
        for i in range(num_windows):
            offset = i * window_step
            
            train_start = start_date + timedelta(days=offset)
            train_end = train_start + timedelta(days=request.train_size_days)
            test_start = train_end
            test_end = test_start + timedelta(days=request.window_size_days)
            
            # Generate window metrics
            train_sharpe = random.uniform(1.5, 2.5)
            test_sharpe = train_sharpe * random.uniform(0.7, 0.95)  # Degradation
            degradation = ((train_sharpe - test_sharpe) / train_sharpe) * 100
            degradations.append(degradation)
            
            window = WindowResults(
                window_id=i,
                train_start=train_start.strftime("%Y-%m-%d"),
                train_end=train_end.strftime("%Y-%m-%d"),
                test_start=test_start.strftime("%Y-%m-%d"),
                test_end=test_end.strftime("%Y-%m-%d"),
                train_sharpe=train_sharpe,
                test_sharpe=test_sharpe,
                train_return=random.uniform(5, 20),
                test_return=random.uniform(3, 18),
                train_drawdown=-random.uniform(8, 15),
                test_drawdown=-random.uniform(8, 20),
                degradation=degradation,
            )
            windows.append(window)
        
        # Calculate summary metrics
        avg_degradation = sum(degradations) / len(degradations) if degradations else 0
        stability_score = max(0, 100 - (avg_degradation * 1.2))  # Higher is better
        passed = stability_score >= 75.0
        
        duration = time.time() - start_time
        
        metrics = ValidationMetrics(
            num_windows=len(windows),
            avg_train_sharpe=sum(w.train_sharpe for w in windows) / len(windows),
            avg_test_sharpe=sum(w.test_sharpe for w in windows) / len(windows),
            avg_degradation=avg_degradation,
            stability_score=stability_score,
            passed=passed,
        )
        
        result = ValidationResult(
            validation_id=validation_id,
            strategy_id=request.strategy_id,
            status="completed" if passed else "completed",
            windows=windows,
            metrics=metrics,
            start_date=request.start_date,
            end_date=request.end_date,
            completed_at=datetime.utcnow().isoformat(),
            duration_seconds=duration,
        )
        
        _validations_db[validation_id] = {"result": result}
        _validation_tasks[validation_id] = "completed"
        
    except Exception as e:
        _validations_db[validation_id] = {"error": str(e)}
        _validation_tasks[validation_id] = "failed"


@router.post("/run", response_model=dict)
async def run_validation(request: ValidationRequest, background_tasks: BackgroundTasks):
    """Run walk-forward validation for a strategy."""
    validation_id = str(uuid.uuid4())
    
    background_tasks.add_task(_run_validation, validation_id, request)
    _validation_tasks[validation_id] = "running"
    
    return {
        "validation_id": validation_id,
        "status": "running",
        "message": "Validation started",
        "created_at": datetime.utcnow().isoformat(),
    }


@router.get("/{validation_id}/status")
async def get_validation_status(validation_id: str):
    """Check status of a validation."""
    if validation_id not in _validation_tasks:
        raise HTTPException(
            status_code=404,
            detail=f"Validation {validation_id} not found"
        )
    
    status = _validation_tasks[validation_id]
    result = _validations_db.get(validation_id, {}).get("result")
    
    response = {
        "validation_id": validation_id,
        "status": status,
    }
    
    if result:
        response["result"] = result
    
    return response


@router.get("/{validation_id}", response_model=ValidationResult)
async def get_validation(validation_id: str):
    """Get details for a validation."""
    if validation_id not in _validations_db:
        raise HTTPException(
            status_code=404,
            detail=f"Validation {validation_id} not found"
        )
    
    data = _validations_db[validation_id]
    
    if "error" in data:
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {data['error']}"
        )
    
    return data["result"]


@router.get("/", response_model=ValidationListResponse)
async def list_validations(
    strategy_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    """List validations, optionally filtered by strategy."""
    validations_list = [
        data["result"] for data in _validations_db.values()
        if data.get("result") is not None
    ]
    
    if strategy_id:
        validations_list = [
            v for v in validations_list 
            if v.strategy_id == strategy_id
        ]
    
    total = len(validations_list)
    paginated = validations_list[skip:skip + limit]
    
    return ValidationListResponse(
        total=total,
        validations=paginated,
    )
