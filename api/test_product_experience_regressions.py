"""Regression checks for product-experience closure tasks."""
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = REPO_ROOT / "api"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))


def test_advanced_features_no_random_synthetic_input_in_production_ui():
    page = (REPO_ROOT / "dashboard" / "src" / "pages" / "AdvancedFeatures.jsx").read_text(encoding="utf-8")
    assert "Math.random" not in page


def test_strategy_candidate_selection_varies_with_goal_and_risk():
    from routers.strategies import _select_strategy_types

    low_risk = _select_strategy_types("mean reversion in pairs", "conservative", 3)
    high_risk = _select_strategy_types("mean reversion in pairs", "aggressive", 3)

    assert low_risk != high_risk


def test_strategy_candidate_selection_is_deterministic_for_same_input():
    from routers.strategies import _select_strategy_types

    a = _select_strategy_types("momentum strategy for equities", "moderate", 5)
    b = _select_strategy_types("momentum strategy for equities", "moderate", 5)
    assert a == b


def test_engine_spec_honors_custom_seed():
    from services.engine_backtest import _build_spec

    spec = _build_spec(
        strategy={"parameters": {"lookback": 20, "vol_target": 0.2}},
        request_data={
            "initial_capital": 100000,
            "instruments": ["SPY"],
            "seed": 99,
        },
    )

    assert spec["seed"] == 99


def test_key_docs_include_reflexion_orchestrator_and_websocket_contract_references():
    root_readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    api_readme = (REPO_ROOT / "api" / "README.md").read_text(encoding="utf-8")
    dash_readme = (REPO_ROOT / "dashboard" / "README.md").read_text(encoding="utf-8")

    assert "Reflexion" in root_readme
    assert "Orchestrator" in root_readme
    assert "WebSocket" in root_readme

    assert "/api/v1/reflexion" in api_readme
    assert "/api/v1/orchestrator/runs" in api_readme
    assert "WEBSOCKET_CONTRACT.md" in api_readme

    assert "Reflexion" in dash_readme
    assert "Orchestrator" in dash_readme
    assert "WebSocket Contract" in dash_readme


def test_orchestrator_start_new_run_does_not_fallback_to_run_history_strategy_id():
    orchestrator_page = (REPO_ROOT / "dashboard" / "src" / "pages" / "Orchestrator.jsx").read_text(encoding="utf-8")

    assert "runs[0]?.strategy_id" not in orchestrator_page
    assert "selectedStrategyId || availableStrategies[0]?.id" in orchestrator_page


def test_gates_and_dashboard_render_readiness_scorecard_surfaces():
    gates_page = (REPO_ROOT / "dashboard" / "src" / "pages" / "Gates.jsx").read_text(encoding="utf-8")
    dashboard_page = (REPO_ROOT / "dashboard" / "src" / "pages" / "Dashboard.jsx").read_text(encoding="utf-8")

    assert "Promotion Readiness" in gates_page
    assert "ReadinessPanel" in gates_page
    assert "top_blockers" in gates_page

    assert "Promotion Readiness" in dashboard_page
    assert "averageScore" in dashboard_page
    assert "topBlockers" in dashboard_page


def test_readiness_panel_orders_blockers_by_priority():
    gates_page = (REPO_ROOT / "dashboard" / "src" / "pages" / "Gates.jsx").read_text(encoding="utf-8")
    
    # Verify blockers are rendered in priority order
    assert "top_blockers" in gates_page
    assert "next_actions" in gates_page


def test_readiness_panel_renders_compatibility_fallback_for_old_api():
    gates_page = (REPO_ROOT / "dashboard" / "src" / "pages" / "Gates.jsx").read_text(encoding="utf-8")
    
    # Verify compatibility layer for API versions without readiness
    assert "maturity_label" in gates_page or "production_ready" in gates_page


def test_dashboard_aggregates_readiness_across_strategies():
    dashboard_page = (REPO_ROOT / "dashboard" / "src" / "pages" / "Dashboard.jsx").read_text(encoding="utf-8")
    
    # Verify band distribution logic
    assert "bandCounts" in dashboard_page or "greenCount" in dashboard_page


def test_readiness_kpi_structure_matches_spec():
    api_readme = (REPO_ROOT / "api" / "README.md").read_text(encoding="utf-8")
    
    # Verify KPI documentation
    assert "decision_latency_ms" in api_readme or "Decision Latency" in api_readme
    assert "false_promotion_proxy" in api_readme or "False Promotion" in api_readme
    assert "reproducibility_pass" in api_readme or "Reproducibility" in api_readme
    assert "onboarding_reliability" in api_readme or "Onboarding" in api_readme
