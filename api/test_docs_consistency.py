"""Trust-critical documentation consistency checks."""
from __future__ import annotations

import json
from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[1]

TRUST_DOCS = {
    "CURRENT_STATUS.md": REPO_ROOT / "CURRENT_STATUS.md",
    "PROJECT_COMPLETE.md": REPO_ROOT / "PROJECT_COMPLETE.md",
    "FINAL_SUMMARY.md": REPO_ROOT / "FINAL_SUMMARY.md",
}


ACCEPTANCE_EVIDENCE_PATH = REPO_ROOT / "docs" / "ACCEPTANCE_EVIDENCE_CLOSE_PRODUCT_EXPERIENCE_GAPS.md"
API_README_PATH = REPO_ROOT / "api" / "README.md"


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


def test_api_readme_strategy_generate_response_example_is_valid_json_payload():
    text = API_README_PATH.read_text(encoding="utf-8")
    match = re.search(
        r"\*\*Response:\*\*\s*```json\s*(\{.*?\})\s*```",
        text,
        flags=re.DOTALL,
    )
    assert match, "Expected a JSON response example under the strategy generation response section"

    payload = json.loads(match.group(1))
    assert isinstance(payload.get("strategies"), list)
    assert payload["strategies"], "Strategies array in README example must not be empty"
    assert payload["strategies"][0].get("id"), "Strategy example must include an id"


def test_trust_docs_avoid_unqualified_release_ready_language():
    current_status_text = TRUST_DOCS["CURRENT_STATUS.md"].read_text(encoding="utf-8").lower()
    project_complete_text = TRUST_DOCS["PROJECT_COMPLETE.md"].read_text(encoding="utf-8").lower()

    assert "ready for integration testing and deployment" not in current_status_text
    assert "production grade" not in project_complete_text


def test_acceptance_evidence_includes_environment_caveat_and_gate_endpoint_outcomes():
    text = ACCEPTANCE_EVIDENCE_PATH.read_text(encoding="utf-8")

    assert "- environment:" in text.lower(), "Acceptance evidence must record execution environment metadata"
    gate_lines = [line for line in text.splitlines() if line.startswith("- Gates: `")]
    assert gate_lines, "Acceptance evidence must include gate endpoint outcome lines"

    latest_gate_json = gate_lines[-1].split("`", 2)[1]
    payload = json.loads(latest_gate_json)
    assert "dev_status" in payload
    assert "crv_status" in payload
    assert "product_status" in payload
    assert payload["dev_status"] == 200, "Dev gate endpoint must remain reachable"


def test_readmes_document_readiness_scorecard_formula_and_bands():
    root_readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    api_readme = (REPO_ROOT / "api" / "README.md").read_text(encoding="utf-8")
    dash_readme = (REPO_ROOT / "dashboard" / "README.md").read_text(encoding="utf-8")

    assert "Promotion Readiness Scorecard" in root_readme
    assert "S = 0.25D + 0.20R + 0.25P + 0.15O + 0.15U" in root_readme

    assert "scorecard_version" in api_readme
    assert '"green": 85' in api_readme
    assert '"amber": 70' in api_readme

    assert "Green (>= 85)" in dash_readme
    assert "Amber (70-84.999)" in dash_readme
    assert "Red (< 70)" in dash_readme
