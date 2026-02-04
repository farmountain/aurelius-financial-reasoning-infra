"""Schema definitions for backtest endpoints."""
from typing import Optional
from pydantic import BaseModel, Field


class BacktestRequest(BaseModel):
    """Request to run a backtest."""
    strategy_id: str = Field(..., description="ID of strategy to backtest")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    initial_capital: float = Field(
        default=100000.0,
        gt=0,
        description="Initial capital in USD"
    )
    instruments: list[str] = Field(
        default=["SPY"],
        description="List of instruments/symbols to trade"
    )


class BacktestMetrics(BaseModel):
    """Performance metrics from a backtest."""
    total_return: float = Field(..., description="Total return percentage")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    sortino_ratio: Optional[float] = Field(default=None, description="Sortino ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown percentage")
    win_rate: float = Field(..., description="Win rate percentage")
    profit_factor: float = Field(..., description="Profit factor (wins/losses)")
    total_trades: int = Field(..., description="Total number of trades")
    avg_trade: float = Field(..., description="Average trade return")
    calmar_ratio: Optional[float] = Field(default=None, description="Calmar ratio")


class BacktestResult(BaseModel):
    """Result of a completed backtest."""
    backtest_id: str = Field(..., description="Unique backtest ID")
    strategy_id: str = Field(..., description="Strategy ID that was tested")
    status: str = Field(..., description="Backtest status (completed, failed, etc)")
    metrics: BacktestMetrics = Field(..., description="Performance metrics")
    start_date: str = Field(..., description="Backtest start date")
    end_date: str = Field(..., description="Backtest end date")
    completed_at: str = Field(..., description="Completion timestamp")
    duration_seconds: float = Field(..., description="Time to complete in seconds")


class BacktestListResponse(BaseModel):
    """Response with list of backtests."""
    total: int = Field(..., description="Total number of backtests")
    backtests: list[BacktestResult] = Field(..., description="List of backtest results")


class BacktestDetailResponse(BaseModel):
    """Detailed backtest response with additional data."""
    backtest: BacktestResult = Field(..., description="Backtest result")
    trades: Optional[list[dict]] = Field(
        default=None,
        description="List of individual trades (optional)"
    )
    equity_curve: Optional[list[float]] = Field(
        default=None,
        description="Daily equity values (optional)"
    )
