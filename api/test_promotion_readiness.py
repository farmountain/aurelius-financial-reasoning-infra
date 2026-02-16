"""Unit tests for promotion-readiness scorecard service."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = REPO_ROOT / "api"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from services.promotion_readiness import (
    ReadinessSignals,
    build_readiness_payload,
    parse_acceptance_evidence_metadata,
)


def _base_signals() -> ReadinessSignals:
    return ReadinessSignals(
        run_identity_present=True,
        parity_checked=True,
        parity_passed=True,
        validation_passed=True,
        crv_available=True,
        risk_metrics_complete=True,
        policy_block_reasons=[],
        lineage_complete=True,
        startup_status="healthy",
        startup_reasons=[],
        evidence_stale=False,
        environment_caveat=None,
        evidence_classification="contract-valid-success",
        evidence_timestamp="2026-02-16T00:00:00+00:00",
        contract_mismatch=False,
        maturity_label_visible=True,
    )


def test_contract_invalid_gate_path_is_operator_visible_blocker_and_action():
    signals = _base_signals()
    signals.environment_caveat = "contract_invalid_gate_path"

    payload = build_readiness_payload(strategy_id="s-1", signals=signals)

    assert "contract_invalid_gate_path" in payload["top_blockers"]
    assert any("contract/runtime" in action for action in payload["next_actions"])
    assert payload["operational_context"]["environment_caveat"] == "contract_invalid_gate_path"
    assert payload["operational_context"]["evidence_classification"] == "contract-valid-success"


def test_hard_blockers_force_red_band_even_with_high_component_scores():
    signals = _base_signals()
    signals.run_identity_present = False

    payload = build_readiness_payload(strategy_id="s-2", signals=signals)

    assert payload["blocked"] is True
    assert payload["band"] == "Red"
    assert "missing_run_identity" in payload["hard_blockers"]


def test_parse_acceptance_evidence_metadata_classifies_contract_invalid_failure(tmp_path: Path):
    evidence = tmp_path / "evidence.md"
    evidence.write_text(
        "\n".join(
            [
                "- Timestamp (UTC): `2026-02-16T00:00:00Z`",
                "- Environment: `local_ci`",
                "- Gates: `{\"dev_status\":500,\"crv_status\":0,\"product_status\":500}`",
            ]
        ),
        encoding="utf-8",
    )

    meta = parse_acceptance_evidence_metadata(evidence, max_age_hours=999999)

    assert meta["classification"] == "contract-invalid-failure"
    assert meta["environment_caveat"] == "contract_invalid_gate_path"
    assert meta["latest_timestamp"] is not None
