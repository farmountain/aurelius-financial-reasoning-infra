"""Schema definitions for gate endpoints."""
from typing import Optional
from pydantic import BaseModel, Field


class GateCheckRequest(BaseModel):
    """Request to run gate checks on a strategy."""
    strategy_id: str = Field(..., description="ID of strategy to check")
    backtest_id: Optional[str] = Field(
        default=None,
        description="Optional backtest ID for metrics"
    )
    validation_id: Optional[str] = Field(
        default=None,
        description="Optional validation ID for stability"
    )


class DevGateCheck(BaseModel):
    """Individual dev gate check result."""
    check_name: str = Field(..., description="Name of the check")
    passed: bool = Field(..., description="Whether check passed")
    description: str = Field(..., description="Check description")
    message: Optional[str] = Field(default=None, description="Additional message")


class DevGateResult(BaseModel):
    """Result from development gate checks."""
    strategy_id: str = Field(..., description="Strategy ID")
    gate_status: str = Field(..., description="Overall gate status")
    passed: bool = Field(..., description="Whether strategy passed all dev gate checks")
    checks: list[DevGateCheck] = Field(..., description="Individual check results")
    timestamp: str = Field(..., description="Check timestamp")


class CRVGateResult(BaseModel):
    """Result from CRV (Cumulative Risk/Reward) gate."""
    strategy_id: str = Field(..., description="Strategy ID")
    gate_status: str = Field(..., description="Overall gate status")
    passed: bool = Field(..., description="Whether strategy passed CRV gate")

    # CRV specific metrics
    min_sharpe_threshold: float = Field(..., description="Minimum Sharpe ratio required")
    max_drawdown_threshold: float = Field(..., description="Maximum drawdown allowed")
    min_return_threshold: float = Field(..., description="Minimum return required")

    actual_sharpe: float = Field(..., description="Actual Sharpe ratio")
    actual_drawdown: float = Field(..., description="Actual maximum drawdown")
    actual_return: float = Field(..., description="Actual return")

    sharpe_pass: bool = Field(..., description="Sharpe ratio check passed")
    drawdown_pass: bool = Field(..., description="Drawdown check passed")
    return_pass: bool = Field(..., description="Return check passed")

    timestamp: str = Field(..., description="Check timestamp")


class ProductGateResult(BaseModel):
    """Result from production gate (all gates combined)."""
    strategy_id: str = Field(..., description="Strategy ID")
    production_ready: bool = Field(
        ...,
        description="Whether strategy is ready for production"
    )

    dev_gate: DevGateResult = Field(..., description="Dev gate results")
    crv_gate: CRVGateResult = Field(..., description="CRV gate results")
    validation_passed: bool = Field(
        ...,
        description="Walk-forward validation passed"
    )

    recommendation: str = Field(
        ...,
        description="Production readiness recommendation"
    )
    timestamp: str = Field(..., description="Check timestamp")


class GateStatusResponse(BaseModel):
    """Response with gate check status."""
    strategy_id: str = Field(..., description="Strategy ID")
    dev_gate_passed: bool = Field(..., description="Dev gate status")
    crv_gate_passed: bool = Field(..., description="CRV gate status")
    validation_passed: bool = Field(..., description="Validation status")
    production_ready: bool = Field(..., description="Overall production readiness")
    execution_mode: Optional[str] = Field(default=None, description="Execution mode for latest run")
    promotion_block_reasons: list[str] = Field(default_factory=list, description="Reasons blocking promotion")
    maturity_label: Optional[str] = Field(default=None, description="Release maturity label")

    # Legacy-compatible gate summaries for existing dashboard surfaces
    dev_gate: Optional[dict] = Field(default=None, description="Latest dev gate summary")
    crv_gate: Optional[dict] = Field(default=None, description="Latest CRV gate summary")
    product_gate: Optional[dict] = Field(default=None, description="Latest product gate summary")

    # Canonical readiness payload
    readiness: Optional[dict] = Field(default=None, description="Promotion-readiness scorecard payload")
