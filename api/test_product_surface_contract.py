"""Product-surface and websocket contract tests."""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = REPO_ROOT / "api"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from api.routers import reflexion as reflexion_router
from api.routers import orchestrator as orchestrator_router
from api.security.auth import TokenData
from database.session import get_db


app = FastAPI()
app.include_router(reflexion_router.router)
app.include_router(orchestrator_router.router)
app.dependency_overrides = {}


def _auth_override():
    return TokenData(user_id="u-1", email="u@example.com", name="User", is_admin=False)


class _DummyDB:
    def commit(self):
        return None

    def refresh(self, obj):
        return obj


def _db_override():
    yield _DummyDB()


# Import dependency function lazily to avoid circular imports in static checks.
from security.dependencies import get_current_user  # noqa: E402

app.dependency_overrides[get_current_user] = _auth_override
app.dependency_overrides[get_db] = _db_override


@dataclass
class FakeStrategy:
    id: str
    strategy_type: str = "ts_momentum"
    parameters: dict | None = None


@dataclass
class FakeReflexionIteration:
    id: str
    strategy_id: str
    iteration_num: int
    improvement_score: float
    feedback: str | None
    improvements: list[str]
    created_at: datetime


@dataclass
class FakeBacktest:
    id: str


@dataclass
class FakeValidation:
    id: str


@dataclass
class FakeGate:
    id: str


@dataclass
class FakeRun:
    id: str
    strategy_id: str | None
    status: str
    current_stage: str | None
    stages: dict
    inputs: dict
    outputs: dict
    error_message: str | None
    created_at: datetime
    updated_at: datetime | None
    completed_at: datetime | None



def test_reflexion_history_happy_path(monkeypatch):
    from api.routers import reflexion

    monkeypatch.setattr(reflexion.StrategyDB, "get", lambda db, strategy_id: FakeStrategy(id=strategy_id))
    monkeypatch.setattr(
        reflexion.ReflexionDB,
        "list_by_strategy",
        lambda db, strategy_id, limit=100: [
            FakeReflexionIteration(
                id="r1",
                strategy_id=strategy_id,
                iteration_num=1,
                improvement_score=0.42,
                feedback="test",
                improvements=["x"],
                created_at=datetime.utcnow(),
            )
        ],
    )

    client = TestClient(app)
    response = client.get("/api/v1/reflexion/s-1/history", headers={"Authorization": "Bearer dummy"})
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert payload[0]["strategy_id"] == "s-1"



def test_reflexion_history_strategy_not_found(monkeypatch):
    from api.routers import reflexion

    monkeypatch.setattr(reflexion.StrategyDB, "get", lambda db, strategy_id: None)

    client = TestClient(app)
    response = client.get("/api/v1/reflexion/missing/history", headers={"Authorization": "Bearer dummy"})
    assert response.status_code == 404



def test_orchestrator_create_run_happy_path(monkeypatch):
    from api.routers import orchestrator

    now = datetime.utcnow()

    monkeypatch.setattr(orchestrator.StrategyDB, "get", lambda db, strategy_id: FakeStrategy(id=strategy_id, parameters={"symbol": "SPY"}))
    monkeypatch.setattr(
        orchestrator.OrchestratorDB,
        "create",
        lambda db, strategy_id, inputs, stages: FakeRun(
            id="run-1",
            strategy_id=strategy_id,
            status="running",
            current_stage="generate_strategy",
            stages=stages,
            inputs=inputs,
            outputs={},
            error_message=None,
            created_at=now,
            updated_at=now,
            completed_at=None,
        ),
    )
    monkeypatch.setattr(orchestrator.OrchestratorDB, "update_stage", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        orchestrator.OrchestratorDB,
        "complete",
        lambda db, run_id, outputs: FakeRun(
            id=run_id,
            strategy_id="s-1",
            status="completed",
            current_stage="completed",
            stages={"product_gate": {"status": "completed"}},
            inputs={},
            outputs=outputs,
            error_message=None,
            created_at=now,
            updated_at=now,
            completed_at=now,
        ),
    )

    monkeypatch.setattr(orchestrator.BacktestDB, "create", lambda *args, **kwargs: FakeBacktest(id="bt-1"))
    monkeypatch.setattr(orchestrator.BacktestDB, "update_running", lambda *args, **kwargs: None)
    monkeypatch.setattr(orchestrator.BacktestDB, "update_completed", lambda *args, **kwargs: None)
    monkeypatch.setattr(orchestrator.BacktestDB, "get", lambda *args, **kwargs: type("Obj", (), {"trades": [], "equity_curve": []})())

    monkeypatch.setattr(orchestrator.ValidationDB, "create", lambda *args, **kwargs: FakeValidation(id="val-1"))
    monkeypatch.setattr(orchestrator.ValidationDB, "update_completed", lambda *args, **kwargs: None)

    monkeypatch.setattr(orchestrator.GateResultDB, "create", lambda *args, **kwargs: FakeGate(id="gate-1"))

    monkeypatch.setattr(
        orchestrator,
        "run_engine_backtest",
        lambda *args, **kwargs: type(
            "RunResult",
            (),
            {"metrics": {"sharpe_ratio": 1.0}, "trades": [], "equity_curve": []},
        )(),
    )

    async def _noop_emit(*args, **kwargs):
        return None

    monkeypatch.setattr(orchestrator, "_emit_stage", _noop_emit)

    async def _noop_broadcast(*args, **kwargs):
        return None

    monkeypatch.setattr(orchestrator.manager, "broadcast", _noop_broadcast)

    client = TestClient(app)
    response = client.post(
        "/api/v1/orchestrator/runs",
        headers={"Authorization": "Bearer dummy"},
        json={
            "strategy_id": "s-1",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": 100000,
            "instruments": ["SPY"],
            "seed": 42,
            "data_source": "default",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == "run-1"
    assert payload["status"] == "completed"



def test_websocket_contract_events_match_dashboard_contract_file():
    from api.websocket.contract import SUPPORTED_EVENTS

    root = Path(__file__).resolve().parents[1]
    js_file = root / "dashboard" / "src" / "services" / "websocketContract.js"
    text = js_file.read_text(encoding="utf-8")

    events = set(re.findall(r"'([a-z_]+)'", text))
    # Remove non-event constants accidentally matched
    events = {e for e in events if "_" in e or e in {"connected", "subscribed", "unsubscribed", "pong"}}

    assert SUPPORTED_EVENTS == events


def test_realtime_consumers_use_only_canonical_event_names():
    root = Path(__file__).resolve().parents[1]
    realtime_hook = (root / "dashboard" / "src" / "hooks" / "useRealtime.js").read_text(encoding="utf-8")

    assert "dashboard_update" not in realtime_hook
    assert "subscribe('backtest_started'" in realtime_hook
    assert "subscribe('backtest_completed'" in realtime_hook
    assert "subscribe('gate_verified'" in realtime_hook
    assert "subscribe('reflexion_iteration_created'" in realtime_hook


def test_orchestrator_and_reflexion_surfaces_consume_realtime_events():
    root = Path(__file__).resolve().parents[1]
    orchestrator_page = (root / "dashboard" / "src" / "pages" / "Orchestrator.jsx").read_text(encoding="utf-8")
    reflexion_page = (root / "dashboard" / "src" / "pages" / "Reflexion.jsx").read_text(encoding="utf-8")

    assert "subscribe('orchestrator_run_created'" in orchestrator_page
    assert "subscribe('orchestrator_stage_updated'" in orchestrator_page
    assert "useRealtimeReflexionEvents" in reflexion_page
