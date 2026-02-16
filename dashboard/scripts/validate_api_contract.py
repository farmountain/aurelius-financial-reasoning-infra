#!/usr/bin/env python3
"""Validate dashboard API contract against backend OpenAPI schema."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.request import urlopen

OPENAPI_URL = os.getenv("OPENAPI_URL", "http://127.0.0.1:8000/openapi.json")

# Dashboard service contract we rely on today.
REQUIRED_ENDPOINTS = {
    ("post", "/api/v1/strategies/generate"),
    ("get", "/api/v1/strategies/"),
    ("get", "/api/v1/strategies/{strategy_id}"),
    ("post", "/api/v1/backtests/run"),
    ("get", "/api/v1/backtests/"),
    ("get", "/api/v1/backtests/{backtest_id}"),
    ("post", "/api/v1/validation/run"),
    ("get", "/api/v1/validation/"),
    ("get", "/api/v1/validation/{validation_id}"),
    ("post", "/api/v1/gates/dev-gate"),
    ("post", "/api/v1/gates/crv-gate"),
    ("post", "/api/v1/gates/product-gate"),
    ("get", "/api/v1/gates/{strategy_id}/status"),
}

AUTH_REQUIRED_ENDPOINTS = {
    ("post", "/api/v1/backtests/run"),
    ("get", "/api/v1/backtests/{backtest_id}/status"),
    ("get", "/api/v1/backtests/{backtest_id}"),
    ("get", "/api/v1/backtests/"),
    ("post", "/api/v1/validation/run"),
    ("get", "/api/v1/validation/{validation_id}/status"),
    ("get", "/api/v1/validation/{validation_id}"),
    ("get", "/api/v1/validation/"),
    ("post", "/api/v1/gates/dev-gate"),
    ("post", "/api/v1/gates/crv-gate"),
    ("post", "/api/v1/gates/product-gate"),
    ("get", "/api/v1/gates/{strategy_id}/status"),
}

REPO_ROOT = Path(__file__).resolve().parents[2]
API_README = REPO_ROOT / "api" / "README.md"


def load_openapi() -> dict:
    with urlopen(OPENAPI_URL, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def collect_operations(schema: dict) -> set[tuple[str, str]]:
    operations: set[tuple[str, str]] = set()
    for path, methods in schema.get("paths", {}).items():
        for method in methods.keys():
            operations.add((method.lower(), path))
    return operations


def has_auth_security(schema: dict, method: str, path: str) -> bool:
    method_config = schema.get("paths", {}).get(path, {}).get(method, {})
    security = method_config.get("security")
    return isinstance(security, list) and len(security) > 0


def route_has_current_user_dependency(method: str, path: str) -> bool:
    """Fallback auth check for custom auth dependencies not represented as OpenAPI security schemes."""
    try:
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
        from api.main import app  # Imported lazily to keep script lightweight when not needed.
    except Exception:
        return False

    normalized_method = method.upper()
    for route in getattr(app, "routes", []):
        if getattr(route, "path", None) != path:
            continue
        methods = set(getattr(route, "methods", set()))
        if normalized_method not in methods:
            continue

        dependant = getattr(route, "dependant", None)
        dependencies = getattr(dependant, "dependencies", []) if dependant is not None else []
        for dep in dependencies:
            call = getattr(dep, "call", None)
            if getattr(call, "__name__", None) == "get_current_user":
                return True
        return False

    return False


def validate_api_readme_examples() -> list[str]:
    errors: list[str] = []
    text = API_README.read_text(encoding="utf-8")

    if '"strategies": [' in text and '"id": ' not in text:
        errors.append("API README strategy generation response example must include strategy 'id' field")

    if "`seed` and `data_source`" not in text:
        errors.append("API README must describe deterministic run controls: seed and data_source")

    return errors


def main() -> int:
    schema = load_openapi()
    available = collect_operations(schema)

    missing = sorted(REQUIRED_ENDPOINTS - available)
    if missing:
        print("API contract drift detected. Missing endpoints:")
        for method, path in missing:
            print(f"  - {method.upper()} {path}")
        return 1

    auth_drift = []
    for method, path in sorted(AUTH_REQUIRED_ENDPOINTS):
        if (method, path) not in available:
            continue
        if not has_auth_security(schema, method, path) and not route_has_current_user_dependency(method, path):
            auth_drift.append((method, path))

    if auth_drift:
        print("API auth contract drift detected. Missing auth requirements:")
        for method, path in auth_drift:
            print(f"  - {method.upper()} {path}")
        return 1

    readme_errors = validate_api_readme_examples()
    if readme_errors:
        print("API documentation contract issues detected:")
        for err in readme_errors:
            print(f"  - {err}")
        return 1

    print("API contract parity check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
