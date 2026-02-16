"""Integration checks for auth policy consistency across backtest/validation/gate workflows."""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = REPO_ROOT / "api"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from api.main import app
from security.auth import TokenData
from security.dependencies import get_current_user
from database.session import get_db


class _DummyQuery:
    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return None


class _DummyDB:
    def query(self, *args, **kwargs):
        return _DummyQuery()


def _dummy_db_override():
    yield _DummyDB()


def _dummy_user_override():
    return TokenData(user_id="u-1", email="u@example.com", name="User", is_admin=False)


def test_auth_is_required_for_workflow_family_endpoints():
    client = TestClient(app)

    requests = [
        ("post", "/api/v1/backtests/run", {"strategy_id": "s-1", "start_date": "2023-01-01", "end_date": "2023-12-31", "initial_capital": 100000, "instruments": ["SPY"]}),
        ("get", "/api/v1/backtests/bt-1/status", None),
        ("post", "/api/v1/validation/run", {"strategy_id": "s-1", "start_date": "2023-01-01", "end_date": "2023-12-31", "window_size_days": 90, "train_size_days": 180, "initial_capital": 100000}),
        ("get", "/api/v1/validation/val-1/status", None),
        ("post", "/api/v1/gates/dev-gate", {"strategy_id": "s-1"}),
        ("post", "/api/v1/gates/crv-gate", {"strategy_id": "s-1"}),
        ("post", "/api/v1/gates/product-gate", {"strategy_id": "s-1"}),
        ("get", "/api/v1/gates/s-1/status", None),
    ]

    for method, path, payload in requests:
        response = getattr(client, method)(path, json=payload) if payload is not None else getattr(client, method)(path)
        assert response.status_code in {401, 403}, f"Expected auth failure for {method.upper()} {path}, got {response.status_code}"


def test_authenticated_requests_do_not_fail_auth_for_status_endpoints(monkeypatch):
    from api.routers import backtests, validation, gates

    app.dependency_overrides[get_current_user] = _dummy_user_override
    app.dependency_overrides[get_db] = _dummy_db_override

    monkeypatch.setattr(backtests.BacktestDB, "get", lambda db, backtest_id: None)
    monkeypatch.setattr(validation.ValidationDB, "get", lambda db, validation_id: None)
    monkeypatch.setattr(gates.GateResultDB, "get_latest", lambda db, strategy_id, gate_type: None)
    monkeypatch.setattr(gates.GateResultDB, "get_product_gate", lambda db, strategy_id: None)

    client = TestClient(app)

    bt_resp = client.get("/api/v1/backtests/bt-1/status", headers={"Authorization": "Bearer dummy"})
    val_resp = client.get("/api/v1/validation/val-1/status", headers={"Authorization": "Bearer dummy"})
    gate_resp = client.get("/api/v1/gates/s-1/status", headers={"Authorization": "Bearer dummy"})

    assert bt_resp.status_code == 404
    assert val_resp.status_code == 404
    assert gate_resp.status_code == 200

    app.dependency_overrides = {}
