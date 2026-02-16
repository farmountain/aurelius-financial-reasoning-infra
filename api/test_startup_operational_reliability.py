"""Startup and operational reliability regression tests."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace

from sqlalchemy.sql.elements import TextClause

from api import main
from database import optimization


class _FakeConnection:
    def __init__(self):
        self.statements = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execution_options(self, **kwargs):
        return self

    def execute(self, statement):
        self.statements.append(statement)

    def commit(self):
        return None


class _FakeEngine:
    def __init__(self):
        self.conn = _FakeConnection()

    def connect(self):
        return self.conn


def test_health_endpoint_reports_structured_degraded_status(monkeypatch):
    main.app.state.startup_status = {
        "status": "degraded",
        "components": {
            "database": {"status": "failed", "reason": "db down"},
            "indexes": {"status": "degraded", "reason": "partial"},
            "cache": {"status": "healthy", "reason": None},
        },
    }

    monkeypatch.setattr(main, "_check_database_liveness", lambda: (False, "db down"))

    payload = asyncio.run(main.health())

    assert payload["status"] == "degraded"
    assert payload["database"] == "disconnected"
    assert payload["dependencies"]["database"]["reason"] == "db down"
    assert payload["startup"]["status"] == "degraded"


def test_database_liveness_uses_executable_sqlalchemy_query(monkeypatch):
    fake_engine = _FakeEngine()

    monkeypatch.setattr("database.session.engine", fake_engine)

    ok, reason = main._check_database_liveness()

    assert ok is True
    assert reason is None
    assert len(fake_engine.conn.statements) == 1
    assert isinstance(fake_engine.conn.statements[0], TextClause)


def test_startup_sets_degraded_state_when_dependencies_fail(monkeypatch):
    class _FakeMetadata:
        @staticmethod
        def create_all(bind):
            raise RuntimeError("database unavailable")

    monkeypatch.setattr(main.Base, "metadata", _FakeMetadata())
    monkeypatch.setattr(main, "engine", object())

    fake_opt_module = SimpleNamespace(create_performance_indexes=lambda: False)
    fake_cache_module = SimpleNamespace(cache=SimpleNamespace(get_stats=lambda: {"enabled": False}))

    import sys
    monkeypatch.setitem(sys.modules, "database.optimization", fake_opt_module)
    monkeypatch.setitem(sys.modules, "cache", fake_cache_module)

    asyncio.run(main.startup_event())

    assert main.app.state.startup_status["status"] == "degraded"
    assert main.app.state.startup_status["components"]["database"]["status"] == "failed"


def test_index_creation_skips_missing_schema_objects(monkeypatch):
    fake_engine = _FakeEngine()

    class _FakeInspector:
        def get_table_names(self):
            return ["strategies", "backtests"]

        def get_columns(self, table_name):
            columns = {
                "strategies": [{"name": "name"}],
                "backtests": [{"name": "strategy_id"}, {"name": "created_at"}, {"name": "status"}],
            }
            return columns.get(table_name, [])

    monkeypatch.setattr(optimization, "engine", fake_engine)
    monkeypatch.setattr(optimization, "inspect", lambda _engine: _FakeInspector())

    success = optimization.create_performance_indexes()

    assert success is False
    assert any("idx_backtests_strategy_id" in str(stmt) for stmt in fake_engine.conn.statements)
