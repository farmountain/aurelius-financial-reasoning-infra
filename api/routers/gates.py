"""Gate verification router."""
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import sys
import os

# Add python package to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../python'))

from api.schemas.gate import (
    GateCheckRequest,
    DevGateCheck,
    DevGateResult,
    CRVGateResult,
    ProductGateResult,
    GateStatusResponse,
)

router = APIRouter(prefix="/api/v1/gates", tags=["gates"])


@router.post("/dev-gate", response_model=DevGateResult)
async def run_dev_gate(request: GateCheckRequest):
    """Run development gate checks on strategy."""
    
    # Mock dev gate checks
    checks = [
        DevGateCheck(
            check_name="Type Checking",
            passed=True,
            description="Mypy type checking passes",
            message="No type errors found",
        ),
        DevGateCheck(
            check_name="Linting",
            passed=True,
            description="Pylint linting passes",
            message="Code style compliant",
        ),
        DevGateCheck(
            check_name="Unit Tests",
            passed=True,
            description="All unit tests pass",
            message="73 tests passed",
        ),
        DevGateCheck(
            check_name="Determinism",
            passed=True,
            description="Strategy produces consistent results",
            message="3/3 runs identical",
        ),
    ]
    
    passed = all(check.passed for check in checks)
    gate_status = "passed" if passed else "failed"
    
    return DevGateResult(
        strategy_id=request.strategy_id,
        gate_status=gate_status,
        passed=passed,
        checks=checks,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.post("/crv-gate", response_model=CRVGateResult)
async def run_crv_gate(request: GateCheckRequest):
    """Run CRV (Cumulative Risk/Reward) gate checks."""
    
    # Set thresholds
    min_sharpe = 0.8
    max_drawdown = -25.0
    min_return = 5.0
    
    # Get actual metrics from backtest (mock for now)
    actual_sharpe = 1.75
    actual_drawdown = -12.5
    actual_return = 18.5
    
    sharpe_pass = actual_sharpe >= min_sharpe
    drawdown_pass = actual_drawdown >= max_drawdown
    return_pass = actual_return >= min_return
    
    passed = sharpe_pass and drawdown_pass and return_pass
    gate_status = "passed" if passed else "failed"
    
    return CRVGateResult(
        strategy_id=request.strategy_id,
        gate_status=gate_status,
        passed=passed,
        min_sharpe_threshold=min_sharpe,
        max_drawdown_threshold=max_drawdown,
        min_return_threshold=min_return,
        actual_sharpe=actual_sharpe,
        actual_drawdown=actual_drawdown,
        actual_return=actual_return,
        sharpe_pass=sharpe_pass,
        drawdown_pass=drawdown_pass,
        return_pass=return_pass,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.post("/product-gate", response_model=ProductGateResult)
async def run_product_gate(request: GateCheckRequest):
    """Run full production gate (all checks combined)."""
    
    # Run dev and CRV gates
    dev_gate = await run_dev_gate(request)
    crv_gate = await run_crv_gate(request)
    
    # Check validation (mock)
    validation_passed = True  # Would check actual validation result
    
    # Determine production readiness
    production_ready = (
        dev_gate.passed and 
        crv_gate.passed and 
        validation_passed
    )
    
    recommendation = (
        "✅ Ready for production deployment" if production_ready
        else "❌ Not ready for production - see gate results"
    )
    
    return ProductGateResult(
        strategy_id=request.strategy_id,
        production_ready=production_ready,
        dev_gate=dev_gate,
        crv_gate=crv_gate,
        validation_passed=validation_passed,
        recommendation=recommendation,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/{strategy_id}/status", response_model=GateStatusResponse)
async def get_gate_status(strategy_id: str):
    """Get current gate status for a strategy."""
    
    # This would query actual results in production
    return GateStatusResponse(
        strategy_id=strategy_id,
        dev_gate_passed=True,
        crv_gate_passed=True,
        validation_passed=True,
        production_ready=True,
    )
