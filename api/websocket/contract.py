"""Canonical websocket envelope and event taxonomy."""
from __future__ import annotations

from datetime import datetime
from typing import Any

WS_ENVELOPE_VERSION = "1.0"

SUPPORTED_EVENTS = {
    "connected",
    "subscribed",
    "unsubscribed",
    "pong",
    "strategy_created",
    "backtest_started",
    "backtest_completed",
    "backtest_failed",
    "validation_completed",
    "gate_verified",
    "reflexion_iteration_created",
    "orchestrator_run_created",
    "orchestrator_stage_updated",
}


def build_ws_message(event: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a canonical websocket message envelope."""
    return {
        "event": event,
        "timestamp": datetime.utcnow().isoformat(),
        "version": WS_ENVELOPE_VERSION,
        "payload": payload or {},
    }
