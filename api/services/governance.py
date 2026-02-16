"""Governance and lineage validation helpers."""

from __future__ import annotations

from typing import Any


REQUIRED_LINEAGE_FIELDS = (
    "run_identity",
    "data_provenance",
    "transformation_lineage",
    "policy_outcomes",
    "artifact_links",
)


def check_lineage_completeness(metrics: dict[str, Any] | None) -> tuple[bool, list[str]]:
    if not isinstance(metrics, dict):
        return False, list(REQUIRED_LINEAGE_FIELDS)

    missing = [field for field in REQUIRED_LINEAGE_FIELDS if not metrics.get(field)]
    return len(missing) == 0, missing


def build_governance_report(
    strategy_id: str,
    checks: dict[str, Any],
) -> dict[str, Any]:
    passed = all(bool(v) for v in checks.values())
    return {
        "strategy_id": strategy_id,
        "passed": passed,
        "checks": checks,
    }
