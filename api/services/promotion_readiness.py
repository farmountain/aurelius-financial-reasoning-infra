"""Promotion-readiness scorecard helpers.

Computes weighted readiness score and operator-facing decision outputs
from existing gate/runtime/evidence signals.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


DEFAULT_WEIGHTS: dict[str, float] = {
    "D": 0.25,
    "R": 0.20,
    "P": 0.25,
    "O": 0.15,
    "U": 0.15,
}
DEFAULT_THRESHOLDS: dict[str, int] = {
    "green": 85,
    "amber": 70,
}
SCORECARD_VERSION = "v1"


BLOCKER_ACTIONS: dict[str, str] = {
    "missing_run_identity": "Run a completed backtest with persisted run identity metadata.",
    "parity_check_failed": "Re-run deterministic replay and resolve parity violations before promotion.",
    "missing_replay_check": "Enable replay parity checks and re-run backtest evidence.",
    "missing_backtest_metrics": "Run a completed backtest so CRV/product checks have metrics.",
    "missing_lineage_fields": "Populate required lineage fields in run metadata before promotion.",
    "policy_block_reasons": "Resolve policy/governance block reasons before promotion.",
    "validation_not_completed": "Complete walk-forward validation and persist status before promotion.",
    "crv_unavailable": "Run CRV gate on completed metrics and resolve threshold failures.",
    "ops_degraded": "Fix dependency/startup health degradations and re-check service health.",
    "evidence_stale": "Refresh acceptance evidence in a known-good environment.",
    "contract_invalid_gate_path": "Fix gate endpoint contract/runtime errors and rerun acceptance evidence.",
    "ui_contract_mismatch": "Align API and dashboard readiness contract before using decision output.",
}


@dataclass
class ReadinessSignals:
    run_identity_present: bool
    parity_checked: bool
    parity_passed: bool
    validation_passed: bool
    crv_available: bool
    risk_metrics_complete: bool
    policy_block_reasons: list[str]
    lineage_complete: bool
    startup_status: str
    startup_reasons: list[str]
    evidence_stale: bool
    environment_caveat: str | None
    evidence_classification: str | None
    evidence_timestamp: str | None
    contract_mismatch: bool
    maturity_label_visible: bool


def _clamp_score(value: float, field: str, warnings: list[str]) -> float:
    if value < 0:
        warnings.append(f"{field}_below_zero_clamped")
        return 0.0
    if value > 100:
        warnings.append(f"{field}_above_hundred_clamped")
        return 100.0
    return float(value)


def _decision_band(score: float, thresholds: dict[str, int]) -> str:
    if score >= thresholds["green"]:
        return "Green"
    if score >= thresholds["amber"]:
        return "Amber"
    return "Red"


def _compute_component_scores(signals: ReadinessSignals, warnings: list[str]) -> dict[str, float]:
    d = 100.0
    if not signals.parity_checked:
        d -= 40.0
    if not signals.run_identity_present:
        d -= 30.0
    if not signals.parity_passed:
        d -= 30.0

    r = 100.0
    if not signals.validation_passed:
        r -= 50.0
    if not signals.crv_available:
        r -= 25.0
    if not signals.risk_metrics_complete:
        r -= 25.0

    p = 100.0
    if signals.policy_block_reasons:
        p -= 60.0
    if not signals.lineage_complete:
        p -= 40.0

    o = 100.0
    if signals.startup_status != "healthy":
        o -= 40.0
    if signals.evidence_stale:
        o -= 30.0
    if len(signals.startup_reasons) >= 2:
        o -= 30.0

    u = 100.0
    if signals.contract_mismatch:
        u -= 60.0
    if not signals.maturity_label_visible:
        u -= 40.0

    return {
        "D": _clamp_score(d, "D", warnings),
        "R": _clamp_score(r, "R", warnings),
        "P": _clamp_score(p, "P", warnings),
        "O": _clamp_score(o, "O", warnings),
        "U": _clamp_score(u, "U", warnings),
    }


def _collect_hard_blockers(signals: ReadinessSignals) -> list[str]:
    blockers: list[str] = []
    if not signals.run_identity_present:
        blockers.append("missing_run_identity")
    if not signals.parity_checked:
        blockers.append("missing_replay_check")
    if not signals.parity_passed:
        blockers.append("parity_check_failed")
    if not signals.lineage_complete:
        blockers.append("missing_lineage_fields")
    if signals.policy_block_reasons:
        blockers.append("policy_block_reasons")
    return blockers


def _top_blockers(hard_blockers: list[str], components: dict[str, float], signals: ReadinessSignals) -> list[str]:
    if hard_blockers:
        return hard_blockers[:3]

    blockers: list[str] = []
    if components["R"] < 80 and not signals.validation_passed:
        blockers.append("validation_not_completed")
    if components["R"] < 80 and not signals.crv_available:
        blockers.append("crv_unavailable")
    if components["O"] < 80 and signals.startup_status != "healthy":
        blockers.append("ops_degraded")
    if components["O"] < 80 and signals.evidence_stale:
        blockers.append("evidence_stale")
    if signals.environment_caveat == "contract_invalid_gate_path":
        blockers.append("contract_invalid_gate_path")
    if components["U"] < 80 and signals.contract_mismatch:
        blockers.append("ui_contract_mismatch")

    if not blockers:
        return ["monitor_inputs"]

    deduped: list[str] = []
    for item in blockers:
        if item not in deduped:
            deduped.append(item)
    return deduped[:3]


def _next_actions(blockers: list[str]) -> list[str]:
    actions: list[str] = []
    for blocker in blockers:
        action = BLOCKER_ACTIONS.get(blocker)
        if action and action not in actions:
            actions.append(action)
    if not actions:
        actions.append("No immediate blockers. Continue monitoring readiness metrics.")
    return actions[:3]


def _component_delta(current: dict[str, float], previous: dict[str, float] | None) -> dict[str, float]:
    if not previous:
        return {key: 0.0 for key in current}
    return {key: round(float(current.get(key, 0.0)) - float(previous.get(key, 0.0)), 3) for key in current}


def _changed_components(delta: dict[str, float]) -> list[str]:
    return [key for key, value in delta.items() if abs(value) >= 0.001]


def build_readiness_payload(
    *,
    strategy_id: str,
    signals: ReadinessSignals,
    previous_scorecard: dict[str, Any] | None = None,
    weights: dict[str, float] | None = None,
    thresholds: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Build canonical readiness payload with score/band/blockers/actions."""
    warnings: list[str] = []
    weights = dict(weights or DEFAULT_WEIGHTS)
    thresholds = dict(thresholds or DEFAULT_THRESHOLDS)

    components = _compute_component_scores(signals, warnings)
    score = sum(weights[key] * components[key] for key in ("D", "R", "P", "O", "U"))
    score = round(_clamp_score(score, "S", warnings), 3)

    hard_blockers = _collect_hard_blockers(signals)
    band = _decision_band(score, thresholds)
    blocked = len(hard_blockers) > 0
    final_band = "Red" if blocked else band

    top_blockers = _top_blockers(hard_blockers, components, signals)
    actions = _next_actions(top_blockers)

    previous_components = None
    previous_score = None
    if isinstance(previous_scorecard, dict):
        previous_components = previous_scorecard.get("components") if isinstance(previous_scorecard.get("components"), dict) else None
        previous_score = previous_scorecard.get("score")

    delta = _component_delta(components, previous_components)
    changed = _changed_components(delta)

    kpi_events = {
        "decision_latency_ms": None,
        "false_promotion_proxy": int(blocked and score >= thresholds["green"]),
        "reproducibility_pass": int(signals.parity_checked and signals.parity_passed and signals.run_identity_present),
        "onboarding_reliability": 1 if signals.startup_status == "healthy" else 0,
    }

    return {
        "strategy_id": strategy_id,
        "scorecard_version": SCORECARD_VERSION,
        "weights": weights,
        "thresholds": thresholds,
        "components": components,
        "score": score,
        "band": final_band,
        "blocked": blocked,
        "hard_blockers": hard_blockers,
        "top_blockers": top_blockers,
        "next_actions": actions,
        "warnings": warnings,
        "maturity_label": "validated" if final_band in {"Green", "Amber"} else "experimental",
        "transition": {
            "previous_score": previous_score,
            "score_delta": round(score - float(previous_score), 3) if isinstance(previous_score, (int, float)) else None,
            "component_delta": delta,
            "changed_components": changed,
        },
        "operational_context": {
            "startup_status": signals.startup_status,
            "startup_reasons": signals.startup_reasons,
            "evidence_stale": signals.evidence_stale,
            "environment_caveat": signals.environment_caveat,
            "evidence_classification": signals.evidence_classification,
            "evidence_timestamp": signals.evidence_timestamp,
            "contract_mismatch": signals.contract_mismatch,
            "maturity_label_visible": signals.maturity_label_visible,
        },
        "kpi_events": kpi_events,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }


def parse_acceptance_evidence_metadata(
    evidence_path: Path,
    *,
    max_age_hours: int = 24,
) -> dict[str, Any]:
    """Extract freshness and environment caveat metadata from acceptance evidence."""
    if not evidence_path.exists():
        return {
            "evidence_stale": True,
            "environment_caveat": "missing_evidence_artifact",
            "latest_timestamp": None,
            "classification": None,
        }

    text = evidence_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    latest_ts: datetime | None = None
    latest_gates: dict[str, Any] | None = None
    latest_environment: str | None = None

    for line in lines:
        if line.startswith("- Timestamp (UTC): `"):
            value = line.split("`", 2)[1]
            try:
                ts = datetime.fromisoformat(value.replace("Z", "+00:00"))
                latest_ts = ts
            except Exception:
                pass
        elif line.startswith("- Environment: `"):
            latest_environment = line.split("`", 2)[1]
        elif line.startswith("- Gates: `"):
            payload = line.split("`", 2)[1]
            try:
                latest_gates = json.loads(payload)
            except Exception:
                latest_gates = None

    now = datetime.now(timezone.utc)
    if latest_ts is None:
        stale = True
    else:
        if latest_ts.tzinfo is None:
            latest_ts = latest_ts.replace(tzinfo=timezone.utc)
        stale = (now - latest_ts).total_seconds() > (max_age_hours * 3600)

    classification = None
    if isinstance(latest_gates, dict):
        dev = int(latest_gates.get("dev_status", 0) or 0)
        crv = int(latest_gates.get("crv_status", 0) or 0)
        product = int(latest_gates.get("product_status", 0) or 0)
        if dev == 200 and crv == 200 and product == 200:
            classification = "contract-valid-success"
        elif dev == 200 and crv in {404, 422} and product in {404, 422}:
            classification = "contract-valid-failure"
        elif any(code >= 500 for code in (dev, crv, product)) or dev == 0:
            classification = "contract-invalid-failure"
        else:
            classification = "mixed"

    caveat = None
    if stale:
        caveat = "evidence_stale"
    elif classification == "contract-invalid-failure":
        caveat = "contract_invalid_gate_path"

    return {
        "evidence_stale": stale,
        "environment_caveat": caveat,
        "latest_timestamp": latest_ts.isoformat() if latest_ts else None,
        "classification": classification,
        "latest_environment": latest_environment,
    }
