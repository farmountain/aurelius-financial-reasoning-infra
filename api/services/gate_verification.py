"""
Gate Verification Primitive Service

Provides gate verification logic for strategy promotion gates (dev, CRV, product).
Extracted from api/routers/gates.py for use as a composable primitive.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import Backtest, Validation
from services.promotion_readiness import build_readiness_payload, ReadinessSignals


class GateCheck(BaseModel):
    """Individual gate check result."""
    check_name: str
    passed: bool
    description: str
    message: Optional[str] = None
    severity: str = Field(default="error", description="error, warning, or info")


class GateVerifyRequest(BaseModel):
    """Request for gate verification."""
    strategy_id: str
    gate_type: str = Field(..., description="dev, crv, or product")
    backtest_metrics: Optional[Dict[str, Any]] = Field(default=None, description="Backtest metrics for verification")
    validation_metrics: Optional[Dict[str, Any]] = Field(default=None, description="Validation metrics")
    thresholds: Optional[Dict[str, float]] = Field(default=None, description="Custom thresholds (sharpe, drawdown, return)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "strategy_id": "strat-123",
                "gate_type": "dev",
                "backtest_metrics": {
                    "run_identity": "run-abc",
                    "sharpe_ratio": 1.8,
                    "max_drawdown": 0.12,
                    "total_return": 0.15,
                    "replay_pass": True
                },
                "thresholds": {
                    "min_sharpe": 1.0,
                    "max_drawdown": 0.20,
                    "min_return": 0.10
                }
            }
        }


class GateVerifyResponse(BaseModel):
    """Gate verification result."""
    strategy_id: str
    gate_type: str
    passed: bool
    gate_status: str = Field(..., description="passed, failed, or blocked")
    checks: List[GateCheck]
    score: Optional[float] = Field(default=None, description="Overall gate score (0-100)")
    readiness_payload: Optional[Dict[str, Any]] = Field(default=None, description="Promotion readiness data")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
    
    class Config:
        json_schema_extra = {
            "example": {
                "strategy_id": "strat-123",
                "gate_type": "dev",
                "passed": True,
                "gate_status": "passed",
                "checks": [
                    {
                        "check_name": "Strategy Exists",
                        "passed": True,
                        "description": "Strategy artifact must exist",
                        "message": "strategy_id=strat-123",
                        "severity": "error"
                    }
                ],
                "score": 100.0,
                "recommendations": []
            }
        }


class GateVerificationService:
    """Service for gate verification logic."""
    
    # Default thresholds
    DEFAULT_THRESHOLDS = {
        "min_sharpe": 1.0,
        "max_drawdown": 0.20,
        "min_return": 0.10
    }
    
    @staticmethod
    def verify_dev_gate(
        strategy_id: str,
        backtest_metrics: Optional[Dict[str, Any]] = None,
        strategy_exists: bool = True
    ) -> GateVerifyResponse:
        """
        Verify development gate checks.
        
        Checks:
        - Strategy artifact exists
        - Completed backtest available
        - Run identity present
        - Replay determinism passed
        """
        checks = []
        
        # Check 1: Strategy exists
        checks.append(GateCheck(
            check_name="Strategy Exists",
            passed=strategy_exists,
            description="Strategy artifact must exist",
            message=f"strategy_id={strategy_id}",
            severity="error"
        ))
        
        # Check 2: Backtest completed
        has_backtest = backtest_metrics is not None
        checks.append(GateCheck(
            check_name="Completed Backtest",
            passed=has_backtest,
            description="Completed backtest artifact is required",
            message="backtest available" if has_backtest else "missing backtest",
            severity="error"
        ))
        
        # Check 3: Run identity present
        run_identity = None
        if backtest_metrics:
            run_identity = backtest_metrics.get("run_identity")
        
        checks.append(GateCheck(
            check_name="Run Identity Present",
            passed=bool(run_identity),
            description="Canonical run identity must be persisted",
            message=str(run_identity) if run_identity else "missing run_identity",
            severity="error"
        ))
        
        # Check 4: Replay determinism
        replay_pass = False
        if backtest_metrics:
            replay_pass = bool(backtest_metrics.get("replay_pass", False))
        
        checks.append(GateCheck(
            check_name="Replay Determinism",
            passed=replay_pass,
            description="Strategy produces consistent results",
            message="Replay parity passed" if replay_pass else "Replay parity failed or missing",
            severity="error"
        ))
        
        # Calculate overall status
        passed = all(check.passed for check in checks)
        gate_status = "passed" if passed else "failed"
        
        # Calculate score
        score = (sum(1 for c in checks if c.passed) / len(checks)) * 100 if checks else 0
        
        # Generate recommendations
        recommendations = []
        if not passed:
            for check in checks:
                if not check.passed:
                    recommendations.append(f"Fix: {check.check_name} - {check.description}")
        
        return GateVerifyResponse(
            strategy_id=strategy_id,
            gate_type="dev",
            passed=passed,
            gate_status=gate_status,
            checks=checks,
            score=round(score, 1),
            recommendations=recommendations
        )
    
    @staticmethod
    def verify_crv_gate(
        strategy_id: str,
        backtest_metrics: Optional[Dict[str, Any]] = None,
        thresholds: Optional[Dict[str, float]] = None
    ) -> GateVerifyResponse:
        """
        Verify CRV (Cumulative Risk/Reward) gate checks.
        
        Checks:
        - Sharpe ratio meets minimum threshold
        - Max drawdown below maximum threshold
        - Total return meets minimum threshold
        """
        # Use default thresholds if not provided
        thresh = {**GateVerificationService.DEFAULT_THRESHOLDS, **(thresholds or {})}
        
        checks = []
        
        if not backtest_metrics:
            # No backtest metrics available
            checks.append(GateCheck(
                check_name="Backtest Metrics Available",
                passed=False,
                description="Risk metrics required for CRV gate",
                message="missing backtest metrics",
                severity="error"
            ))
            
            return GateVerifyResponse(
                strategy_id=strategy_id,
                gate_type="crv",
                passed=False,
                gate_status="blocked",
                checks=checks,
                score=0.0,
                recommendations=["Complete backtest to obtain risk metrics"]
            )
        
        # Extract metrics
        sharpe_ratio = backtest_metrics.get("sharpe_ratio", 0.0)
        max_drawdown = backtest_metrics.get("max_drawdown", 1.0)
        total_return = backtest_metrics.get("total_return", 0.0)
        
        # Check 1: Sharpe ratio
        sharpe_pass = sharpe_ratio >= thresh["min_sharpe"]
        checks.append(GateCheck(
            check_name="Sharpe Ratio",
            passed=sharpe_pass,
            description=f"Sharpe ratio must be >= {thresh['min_sharpe']}",
            message=f"actual: {sharpe_ratio:.2f}",
            severity="error"
        ))
        
        # Check 2: Max drawdown
        drawdown_pass = max_drawdown <= thresh["max_drawdown"]
        checks.append(GateCheck(
            check_name="Max Drawdown",
            passed=drawdown_pass,
            description=f"Max drawdown must be <= {thresh['max_drawdown']}",
            message=f"actual: {max_drawdown:.2f}",
            severity="error"
        ))
        
        # Check 3: Total return
        return_pass = total_return >= thresh["min_return"]
        checks.append(GateCheck(
            check_name="Total Return",
            passed=return_pass,
            description=f"Total return must be >= {thresh['min_return']}",
            message=f"actual: {total_return:.2f}",
            severity="error"
        ))
        
        # Calculate overall status
        passed = all(check.passed for check in checks)
        gate_status = "passed" if passed else "failed"
        
        # Calculate score
        score = (sum(1 for c in checks if c.passed) / len(checks)) * 100 if checks else 0
        
        # Generate recommendations
        recommendations = []
        if not sharpe_pass:
            recommendations.append(f"Improve Sharpe ratio from {sharpe_ratio:.2f} to {thresh['min_sharpe']}")
        if not drawdown_pass:
            recommendations.append(f"Reduce max drawdown from {max_drawdown:.2f} to {thresh['max_drawdown']}")
        if not return_pass:
            recommendations.append(f"Increase total return from {total_return:.2f} to {thresh['min_return']}")
        
        return GateVerifyResponse(
            strategy_id=strategy_id,
            gate_type="crv",
            passed=passed,
            gate_status=gate_status,
            checks=checks,
            score=round(score, 1),
            recommendations=recommendations
        )
    
    @staticmethod
    def verify_product_gate(
        strategy_id: str,
        backtest_metrics: Optional[Dict[str, Any]] = None,
        validation_metrics: Optional[Dict[str, Any]] = None,
        thresholds: Optional[Dict[str, float]] = None,
        strategy_exists: bool = True
    ) -> GateVerifyResponse:
        """
        Verify product gate (all gates combined).
        
        Combines:
        - Dev gate checks
        - CRV gate checks
        - Validation checks
        """
        all_checks = []
        
        # Run dev gate
        dev_result = GateVerificationService.verify_dev_gate(
            strategy_id=strategy_id,
            backtest_metrics=backtest_metrics,
            strategy_exists=strategy_exists
        )
        all_checks.extend(dev_result.checks)
        
        # Run CRV gate
        crv_result = GateVerificationService.verify_crv_gate(
            strategy_id=strategy_id,
            backtest_metrics=backtest_metrics,
            thresholds=thresholds
        )
        all_checks.extend(crv_result.checks)
        
        # Check validation
        validation_passed = False
        if validation_metrics:
            validation_passed = validation_metrics.get("status") == "completed"
        
        all_checks.append(GateCheck(
            check_name="Walk-Forward Validation",
            passed=validation_passed,
            description="Strategy must pass walk-forward validation",
            message="validation passed" if validation_passed else "validation missing or failed",
            severity="error"
        ))
        
        # Calculate overall status
        passed = all(check.passed for check in all_checks)
        gate_status = "passed" if passed else "failed"
        
        # Calculate score
        score = (sum(1 for c in all_checks if c.passed) / len(all_checks)) * 100 if all_checks else 0
        
        # Generate recommendations
        recommendations = []
        if not dev_result.passed:
            recommendations.append("Complete dev gate requirements first")
        if not crv_result.passed:
            recommendations.extend(crv_result.recommendations)
        if not validation_passed:
            recommendations.append("Complete walk-forward validation")
        
        return GateVerifyResponse(
            strategy_id=strategy_id,
            gate_type="product",
            passed=passed,
            gate_status=gate_status,
            checks=all_checks,
            score=round(score, 1),
            recommendations=recommendations
        )
    
    @staticmethod
    def verify_gate(request: GateVerifyRequest) -> GateVerifyResponse:
        """
        Main entry point for gate verification.
        
        Routes to appropriate gate type handler.
        """
        if request.gate_type == "dev":
            return GateVerificationService.verify_dev_gate(
                strategy_id=request.strategy_id,
                backtest_metrics=request.backtest_metrics,
                strategy_exists=True  # Assume exists if request made
            )
        elif request.gate_type == "crv":
            return GateVerificationService.verify_crv_gate(
                strategy_id=request.strategy_id,
                backtest_metrics=request.backtest_metrics,
                thresholds=request.thresholds
            )
        elif request.gate_type == "product":
            return GateVerificationService.verify_product_gate(
                strategy_id=request.strategy_id,
                backtest_metrics=request.backtest_metrics,
                validation_metrics=request.validation_metrics,
                thresholds=request.thresholds,
                strategy_exists=True
            )
        else:
            raise ValueError(f"Unknown gate type: {request.gate_type}")
