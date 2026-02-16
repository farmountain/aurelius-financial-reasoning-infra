"""Parity validation configuration for API/CLI consistency checks."""

PARITY_TOLERANCES = {
    "total_return": 0.01,   # percentage points
    "sharpe_ratio": 0.01,
    "max_drawdown": 0.01,   # percentage points
}


def metric_within_tolerance(metric: str, lhs: float, rhs: float) -> bool:
    tolerance = float(PARITY_TOLERANCES.get(metric, 0.0))
    return abs(float(lhs) - float(rhs)) <= tolerance
