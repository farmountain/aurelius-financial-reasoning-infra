"""Backtest management router."""
import uuid
import time
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import Optional
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

router = APIRouter(prefix="/api/v1/backtests", tags=["backtests"])

# In-memory storage for demo
_backtests_db = {}
_backtest_tasks = {}


def _run_backtest(backtest_id: str, request: BacktestRequest):
    """Run backtest in background (mock implementation)."""
    start_time = time.time()
    
    try:
        # Simulate backtest computation
        import random
        
        # Generate mock metrics
        base_return = random.uniform(5, 25)
        sharpe = random.uniform(0.8, 2.5)
        max_dd = -random.uniform(8, 20)
        win_rate = random.uniform(45, 65)
        
        metrics = BacktestMetrics(
            total_return=base_return,
            sharpe_ratio=sharpe,
            sortino_ratio=sharpe * 1.2,
            max_drawdown=max_dd,
            win_rate=win_rate,
            profit_factor=random.uniform(1.2, 2.5),
            total_trades=random.randint(50, 200),
            avg_trade=base_return / 100,
            calmar_ratio=sharpe / abs(max_dd) if max_dd != 0 else 0,
        )
        
        duration = time.time() - start_time
        
        result = BacktestResult(
            backtest_id=backtest_id,
            strategy_id=request.strategy_id,
            status="completed",
            metrics=metrics,
            start_date=request.start_date,
            end_date=request.end_date,
            completed_at=datetime.utcnow().isoformat(),
            duration_seconds=duration,
        )
        
        _backtests_db[backtest_id] = {
            "result": result,
            "request": request,
            "trades": [],
            "equity_curve": [],
        }
        _backtest_tasks[backtest_id] = "completed"
        
    except Exception as e:
        _backtests_db[backtest_id] = {
            "result": None,
            "error": str(e),
        }
        _backtest_tasks[backtest_id] = "failed"


@router.post("/run", response_model=dict)
async def run_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    """Run a backtest for a strategy."""
    backtest_id = str(uuid.uuid4())
    
    # Start backtest in background
    background_tasks.add_task(_run_backtest, backtest_id, request)
    _backtest_tasks[backtest_id] = "running"
    
    return {
        "backtest_id": backtest_id,
        "status": "running",
        "message": "Backtest started",
        "created_at": datetime.utcnow().isoformat(),
    }


@router.get("/{backtest_id}/status")
async def get_backtest_status(backtest_id: str):
    """Check status of a backtest."""
    if backtest_id not in _backtest_tasks:
        raise HTTPException(
            status_code=404,
            detail=f"Backtest {backtest_id} not found"
        )
    
    status = _backtest_tasks[backtest_id]
    result = _backtests_db.get(backtest_id, {}).get("result")
    
    response = {
        "backtest_id": backtest_id,
        "status": status,
    }
    
    if result:
        response["result"] = result
    
    return response


@router.get("/{backtest_id}", response_model=BacktestDetailResponse)
async def get_backtest(backtest_id: str):
    """Get details for a completed backtest."""
    if backtest_id not in _backtests_db:
        raise HTTPException(
            status_code=404,
            detail=f"Backtest {backtest_id} not found"
        )
    
    data = _backtests_db[backtest_id]
    
    if "error" in data:
        raise HTTPException(
            status_code=500,
            detail=f"Backtest failed: {data['error']}"
        )
    
    return BacktestDetailResponse(
        backtest=data["result"],
        trades=data.get("trades"),
        equity_curve=data.get("equity_curve"),
    )


@router.get("/", response_model=BacktestListResponse)
async def list_backtests(
    strategy_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    """List backtests, optionally filtered by strategy."""
    backtests_list = [
        data["result"] for data in _backtests_db.values()
        if data.get("result") is not None
    ]
    
    if strategy_id:
        backtests_list = [
            bt for bt in backtests_list 
            if bt.strategy_id == strategy_id
        ]
    
    total = len(backtests_list)
    paginated = backtests_list[skip:skip + limit]
    
    return BacktestListResponse(
        total=total,
        backtests=paginated,
    )
