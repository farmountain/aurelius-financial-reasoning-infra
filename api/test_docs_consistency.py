"""Trust-critical documentation consistency checks."""
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

TRUST_DOCS = {
    "CURRENT_STATUS.md": REPO_ROOT / "CURRENT_STATUS.md",
    "PROJECT_COMPLETE.md": REPO_ROOT / "PROJECT_COMPLETE.md",
    "FINAL_SUMMARY.md": REPO_ROOT / "FINAL_SUMMARY.md",
}


ACCEPTANCE_EVIDENCE_PATH = REPO_ROOT / "docs" / "ACCEPTANCE_EVIDENCE_CLOSE_PRODUCT_EXPERIENCE_GAPS.md"


def test_trust_docs_include_evidence_gated_maturity_language():
    for name, path in TRUST_DOCS.items():
        text = path.read_text(encoding="utf-8")
        head = "\n".join(text.splitlines()[:40])
        assert "evidence" in head.lower(), f"{name} must mention evidence-gated interpretation near the top"


def test_project_completion_docs_do_not_use_absolute_release_claims_in_headers():
    current_status_head = "\n".join(TRUST_DOCS["CURRENT_STATUS.md"].read_text(encoding="utf-8").splitlines()[:25])
    project_complete_head = "\n".join(TRUST_DOCS["PROJECT_COMPLETE.md"].read_text(encoding="utf-8").splitlines()[:25])

    assert "100% complete" not in current_status_head.lower()
    assert "production ready" not in current_status_head.lower() or "validated with environment caveats" in current_status_head.lower()
    assert "100% complete" not in project_complete_head.lower()


def test_trust_docs_reference_acceptance_evidence_artifact():
    assert ACCEPTANCE_EVIDENCE_PATH.exists(), "Acceptance evidence artifact must exist"

    current = TRUST_DOCS["CURRENT_STATUS.md"].read_text(encoding="utf-8")
    assert "ACCEPTANCE_EVIDENCE_CLOSE_PRODUCT_EXPERIENCE_GAPS.md" in current
