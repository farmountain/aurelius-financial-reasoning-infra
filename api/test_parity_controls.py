"""Parity and replay control tests for runtime truth path."""

from services.parity_config import PARITY_TOLERANCES, metric_within_tolerance


def test_parity_tolerance_config_exists():
    assert "total_return" in PARITY_TOLERANCES
    assert "sharpe_ratio" in PARITY_TOLERANCES
    assert "max_drawdown" in PARITY_TOLERANCES


def test_metric_within_tolerance_positive_case():
    tol = PARITY_TOLERANCES["sharpe_ratio"]
    assert metric_within_tolerance("sharpe_ratio", 1.0, 1.0 + tol * 0.5)


def test_metric_within_tolerance_negative_case():
    tol = PARITY_TOLERANCES["sharpe_ratio"]
    assert not metric_within_tolerance("sharpe_ratio", 1.0, 1.0 + tol * 2.0)
