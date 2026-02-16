"""Gate verification router."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.dirname(__file__))

from schemas.gate import (
    GateCheckRequest,
    DevGateCheck,
    DevGateResult,
    CRVGateResult,
    ProductGateResult,
    GateStatusResponse,
)
from database.session import get_db
from database.crud import GateResultDB, BacktestDB, ValidationDB, StrategyDB
from database.models import Backtest, Validation
from services.governance import check_lineage_completeness, build_governance_report
from services.release_gates import evaluate_release_gate
import os
from config import settings
from security.dependencies import get_current_user
from security.auth import TokenData

router = APIRouter(prefix="/api/v1/gates", tags=["gates"])


def _resolve_backtest(request: GateCheckRequest, db: Session) -> Backtest | None:
    if request.backtest_id:
        return BacktestDB.get(db, request.backtest_id)
    return db.query(Backtest).filter(
        Backtest.strategy_id == request.strategy_id,
        Backtest.status == "completed"
    ).order_by(Backtest.completed_at.desc()).first()


def _resolve_validation(request: GateCheckRequest, db: Session) -> Validation | None:
    if request.validation_id:
        return ValidationDB.get(db, request.validation_id)
    return db.query(Validation).filter(
        Validation.strategy_id == request.strategy_id,
        Validation.status == "completed"
    ).order_by(Validation.completed_at.desc()).first()


def _parity_block_reasons(backtest: Backtest | None) -> list[str]:
    if not backtest or not isinstance(backtest.metrics, dict):
        return ["missing_backtest_metrics"]

    metrics = backtest.metrics
    reasons: list[str] = []

    if not metrics.get("run_identity"):
        reasons.append("missing_run_identity")

    parity = metrics.get("parity_check") if isinstance(metrics.get("parity_check"), dict) else {}
    if not parity.get("checked", False):
        reasons.append("missing_replay_check")
    if not parity.get("passed", False):
        reasons.append("parity_check_failed")

    return reasons


@router.post("/dev-gate", response_model=DevGateResult)
async def run_dev_gate(
    request: GateCheckRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run development gate checks on strategy."""

    strategy = StrategyDB.get(db, request.strategy_id)
    backtest = _resolve_backtest(request, db)
    metrics = backtest.metrics if backtest and isinstance(backtest.metrics, dict) else {}
    run_identity = metrics.get("run_identity") if isinstance(metrics, dict) else None
    replay_pass = bool(metrics.get("replay_pass", False)) if isinstance(metrics, dict) else False

    checks = [
        DevGateCheck(
            check_name="Strategy Exists",
            passed=strategy is not None,
            description="Strategy artifact must exist",
            message=f"strategy_id={request.strategy_id}",
        ),
        DevGateCheck(
            check_name="Completed Backtest",
            passed=backtest is not None,
            description="Completed backtest artifact is required",
            message=f"backtest_id={backtest.id if backtest else 'none'}",
        ),
        DevGateCheck(
            check_name="Run Identity Present",
            passed=bool(run_identity),
            description="Canonical run identity must be persisted",
            message=str(run_identity) if run_identity else "missing run_identity",
        ),
        DevGateCheck(
            check_name="Replay Determinism",
            passed=replay_pass,
            description="Strategy produces consistent results",
            message="Replay parity passed" if replay_pass else "Replay parity failed or missing",
        ),
    ]

    passed = all(check.passed for check in checks)
    gate_status = "passed" if passed else "failed"

    result = DevGateResult(
        strategy_id=request.strategy_id,
        gate_status=gate_status,
        passed=passed,
        checks=checks,
        timestamp=datetime.utcnow().isoformat(),
    )

    # Store in database
    GateResultDB.create(db, request.strategy_id, "dev", passed,
                       {"checks": [c.dict() for c in checks], "gate_status": gate_status})

    return result


@router.post("/crv-gate", response_model=CRVGateResult)
async def run_crv_gate(
    request: GateCheckRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run CRV (Cumulative Risk/Reward) gate checks."""

    backtest = _resolve_backtest(request, db)
    if not backtest or not isinstance(backtest.metrics, dict):
        raise HTTPException(status_code=404, detail="No completed backtest metrics found for CRV gate")

    # Set thresholds
    min_sharpe = 0.8
    max_drawdown = -25.0
    min_return = 5.0

    # Get actual metrics from backtest artifacts
    actual_sharpe = float(backtest.metrics.get("sharpe_ratio", 0.0))
    actual_drawdown = float(backtest.metrics.get("max_drawdown", 0.0))
    actual_return = float(backtest.metrics.get("total_return", 0.0))

    sharpe_pass = actual_sharpe >= min_sharpe
    drawdown_pass = actual_drawdown >= max_drawdown
    return_pass = actual_return >= min_return

    passed = sharpe_pass and drawdown_pass and return_pass
    gate_status = "passed" if passed else "failed"

    result = CRVGateResult(
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

    # Store in database
    GateResultDB.create(db, request.strategy_id, "crv", passed,
                       result.dict())

    return result


@router.post("/product-gate", response_model=ProductGateResult)
async def run_product_gate(
    request: GateCheckRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run full production gate (all checks combined)."""

    if not getattr(settings, "enable_truth_gates", True):
        raise HTTPException(status_code=503, detail="Truth gates execution is disabled by rollout flag")

    # Run dev and CRV gates
    dev_gate = await run_dev_gate(request=request, current_user=current_user, db=db)
    crv_gate = await run_crv_gate(request=request, current_user=current_user, db=db)
    backtest = _resolve_backtest(request, db)

    validation = _resolve_validation(request, db)
    validation_passed = bool(validation and validation.passed)
    parity_block_reasons = _parity_block_reasons(backtest)
    parity_passed = len(parity_block_reasons) == 0
    lineage_passed, missing_lineage_fields = check_lineage_completeness(
        backtest.metrics if backtest else None
    )

    # Determine production readiness
    production_ready = (
        dev_gate.passed and
        crv_gate.passed and
        validation_passed and
        parity_passed and
        lineage_passed
    )

    governance_report = build_governance_report(
        strategy_id=request.strategy_id,
        checks={
            "dev_gate": dev_gate.passed,
            "crv_gate": crv_gate.passed,
            "validation": validation_passed,
            "parity": parity_passed,
            "lineage": lineage_passed,
        },
    )

    contract_parity = os.getenv("API_CONTRACT_PARITY", "true").lower() == "true"
    release_evidence = {
        "truth_parity": parity_passed,
        "determinism": dev_gate.passed,
        "contract_parity": contract_parity,
        "lineage_completeness": lineage_passed,
    }
    release_gate_passed, release_block_reasons, maturity_label = evaluate_release_gate(release_evidence)

    recommendation = (
        "✅ Ready for production deployment" if production_ready
        else "❌ Not ready for production - see gate results"
    )

    result = ProductGateResult(
        strategy_id=request.strategy_id,
        production_ready=production_ready,
        dev_gate=dev_gate,
        crv_gate=crv_gate,
        validation_passed=validation_passed,
        recommendation=recommendation,
        timestamp=datetime.utcnow().isoformat(),
    )

    # Store in database
    GateResultDB.create(db, request.strategy_id, "product", production_ready,
                       {
                           "recommendation": recommendation,
                           "parity_passed": parity_passed,
                           "parity_block_reasons": parity_block_reasons,
                           "lineage_passed": lineage_passed,
                           "missing_lineage_fields": missing_lineage_fields,
                           "run_identity": (backtest.metrics or {}).get("run_identity") if backtest and isinstance(backtest.metrics, dict) else None,
                           "governance_report": governance_report,
                           "release_gate": {
                               "passed": release_gate_passed,
                               "block_reasons": release_block_reasons,
                               "maturity_label": maturity_label,
                               "evidence": release_evidence,
                           },
                           **result.dict(),
                       })

    return result


@router.get("/{strategy_id}/status", response_model=GateStatusResponse)
async def get_gate_status(
    strategy_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current gate status for a strategy."""

    # Get latest gate results from database
    dev_gate = GateResultDB.get_latest(db, strategy_id, "dev")
    crv_gate = GateResultDB.get_latest(db, strategy_id, "crv")
    product_gate = GateResultDB.get_product_gate(db, strategy_id)

    dev_passed = dev_gate.passed if dev_gate else False
    crv_passed = crv_gate.passed if crv_gate else False
    prod_ready = product_gate.production_ready if product_gate else False
    latest_validation = db.query(Validation).filter(
        Validation.strategy_id == strategy_id,
        Validation.status == "completed"
    ).order_by(Validation.completed_at.desc()).first()
    validation_passed = bool(latest_validation and latest_validation.passed)
    product_results = product_gate.results if product_gate and isinstance(product_gate.results, dict) else {}
    promotion_block_reasons = []
    if isinstance(product_results.get("parity_block_reasons"), list):
        promotion_block_reasons.extend(product_results.get("parity_block_reasons", []))
    if isinstance(product_results.get("missing_lineage_fields"), list):
        promotion_block_reasons.extend([f"missing_{f}" for f in product_results.get("missing_lineage_fields", [])])
    release_gate = product_results.get("release_gate") if isinstance(product_results.get("release_gate"), dict) else {}
    if isinstance(release_gate.get("block_reasons"), list):
        promotion_block_reasons.extend(release_gate.get("block_reasons", []))

    latest_backtest = db.query(Backtest).filter(
        Backtest.strategy_id == strategy_id,
        Backtest.status == "completed"
    ).order_by(Backtest.completed_at.desc()).first()
    execution_mode = None
    if latest_backtest and isinstance(latest_backtest.metrics, dict):
        execution_mode = latest_backtest.metrics.get("execution_mode")

    return GateStatusResponse(
        strategy_id=strategy_id,
        dev_gate_passed=dev_passed,
        crv_gate_passed=crv_passed,
        validation_passed=validation_passed,
        production_ready=prod_ready,
        execution_mode=execution_mode,
        promotion_block_reasons=promotion_block_reasons,
    )
