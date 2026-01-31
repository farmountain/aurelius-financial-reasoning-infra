"""Schema definitions for validation endpoints."""
from typing import Optional
from pydantic import BaseModel, Field


class ValidationRequest(BaseModel):
    """Request to run walk-forward validation."""
    strategy_id: str = Field(..., description="ID of strategy to validate")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    window_size_days: int = Field(
        default=90,
        gt=30,
        description="Size of test window in days"
    )
    train_size_days: int = Field(
        default=180,
        gt=30,
        description="Size of training window in days"
    )
    initial_capital: float = Field(
        default=100000.0,
        gt=0,
        description="Initial capital in USD"
    )


class WindowResults(BaseModel):
    """Results for a single validation window."""
    window_id: int = Field(..., description="Window index (0-based)")
    train_start: str = Field(..., description="Training period start date")
    train_end: str = Field(..., description="Training period end date")
    test_start: str = Field(..., description="Test period start date")
    test_end: str = Field(..., description="Test period end date")
    train_sharpe: float = Field(..., description="Sharpe ratio on training data")
    test_sharpe: float = Field(..., description="Sharpe ratio on test data")
    train_return: float = Field(..., description="Total return on training data")
    test_return: float = Field(..., description="Total return on test data")
    train_drawdown: float = Field(..., description="Max drawdown on training data")
    test_drawdown: float = Field(..., description="Max drawdown on test data")
    degradation: float = Field(
        ...,
        description="Performance degradation from train to test (%)"
    )


class ValidationMetrics(BaseModel):
    """Summary metrics across all validation windows."""
    num_windows: int = Field(..., description="Number of windows tested")
    avg_train_sharpe: float = Field(..., description="Average training Sharpe ratio")
    avg_test_sharpe: float = Field(..., description="Average test Sharpe ratio")
    avg_degradation: float = Field(
        ...,
        description="Average degradation from train to test (%)"
    )
    stability_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall stability score (0-100)"
    )
    passed: bool = Field(
        ...,
        description="Whether validation passed (stability >= 75%)"
    )


class ValidationResult(BaseModel):
    """Result of a walk-forward validation."""
    validation_id: str = Field(..., description="Unique validation ID")
    strategy_id: str = Field(..., description="Strategy ID that was validated")
    status: str = Field(..., description="Validation status (completed, failed, etc)")
    windows: list[WindowResults] = Field(..., description="Results per window")
    metrics: ValidationMetrics = Field(..., description="Summary metrics")
    start_date: str = Field(..., description="Validation start date")
    end_date: str = Field(..., description="Validation end date")
    completed_at: str = Field(..., description="Completion timestamp")
    duration_seconds: float = Field(..., description="Time to complete in seconds")


class ValidationListResponse(BaseModel):
    """Response with list of validations."""
    total: int = Field(..., description="Total number of validations")
    validations: list[ValidationResult] = Field(..., description="List of validation results")
