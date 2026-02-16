"""Capability maturity and release gating helpers."""

from __future__ import annotations

from typing import Any


CAPABILITY_THRESHOLDS = {
    "production": {
        "truth_parity": True,
        "determinism": True,
        "contract_parity": True,
        "lineage_completeness": True,
    },
    "validated": {
        "truth_parity": True,
        "determinism": True,
        "contract_parity": False,
        "lineage_completeness": True,
    },
    "experimental": {
        "truth_parity": False,
        "determinism": False,
        "contract_parity": False,
        "lineage_completeness": False,
    },
}


def determine_maturity(evidence: dict[str, Any]) -> str:
    if all(bool(evidence.get(k)) == v for k, v in CAPABILITY_THRESHOLDS["production"].items()):
        return "production"
    if (
        bool(evidence.get("truth_parity"))
        and bool(evidence.get("determinism"))
        and bool(evidence.get("lineage_completeness"))
    ):
        return "validated"
    return "experimental"


def evaluate_release_gate(evidence: dict[str, Any]) -> tuple[bool, list[str], str]:
    reasons: list[str] = []

    for key, required in CAPABILITY_THRESHOLDS["production"].items():
        actual = bool(evidence.get(key))
        if required and not actual:
            reasons.append(f"{key}_failed")

    maturity = determine_maturity(evidence)
    passed = len(reasons) == 0
    return passed, reasons, maturity
