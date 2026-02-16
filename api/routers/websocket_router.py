"""WebSocket endpoint for real-time updates."""

import logging
import sys
from pathlib import Path
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from fastapi.responses import JSONResponse

# Add parent directory to path to avoid namespace conflicts
sys.path.insert(0, str(Path(__file__).parent.parent))

from websocket.manager import manager
from websocket.contract import build_ws_message, SUPPORTED_EVENTS
from security.auth import verify_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("")
@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(None)):
    """
    WebSocket endpoint for real-time updates.
    
    Requires JWT token authentication via query parameter.
    
    Args:
        websocket: The WebSocket connection
        token: JWT access token for authentication
    
    Message Format:
        {
            "event": "event_type",
            "timestamp": "ISO-8601",
            "version": "1.0",
            "payload": {...}
        }
    
    Event Types:
        - strategy_created: New strategy generated
        - backtest_started: Backtest execution started
        - backtest_completed: Backtest finished
        - backtest_failed: Backtest failed
        - reflexion_iteration_created: Reflexion iteration persisted
        - orchestrator_run_created: Orchestrator run created
        - orchestrator_stage_updated: Orchestrator stage transition
    
    Client Commands:
        - subscribe: Subscribe to event types
          {"action": "subscribe", "events": ["strategy_created", "backtest_progress"]}
        - unsubscribe: Unsubscribe from event types
          {"action": "unsubscribe", "events": ["dashboard_update"]}
        - ping: Keep-alive ping
          {"action": "ping"}
    """
    user_id = None

    try:
        # Verify JWT token
        token_data = verify_token(token)
        if not token_data:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        user_id = token_data.user_id

        # Accept connection
        await manager.connect(websocket, user_id)

        # Send connection confirmation
        await websocket.send_json(build_ws_message("connected", {
            "message": "WebSocket connected successfully",
            "user_id": user_id,
            "supported_events": sorted(SUPPORTED_EVENTS),
        }))

        # Listen for client messages
        while True:
            data = await websocket.receive_json()

            # Handle client commands
            action = data.get("action")

            if action == "subscribe":
                event_types = data.get("events", [])
                await manager.subscribe(user_id, event_types)
                await websocket.send_json(build_ws_message("subscribed", {"events": event_types}))

            elif action == "unsubscribe":
                event_types = data.get("events", [])
                await manager.unsubscribe(user_id, event_types)
                await websocket.send_json(build_ws_message("unsubscribed", {"events": event_types}))

            elif action == "ping":
                await websocket.send_json(build_ws_message("pong", {"timestamp": data.get("timestamp")}))

            else:
                logger.warning(f"Unknown action from user {user_id}: {action}")

    except WebSocketDisconnect:
        if user_id:
            manager.disconnect(websocket, user_id)
        logger.info(f"WebSocket disconnected normally for user {user_id}")

    except Exception as e:
        if user_id:
            manager.disconnect(websocket, user_id)
        logger.error(f"WebSocket error for user {user_id}: {e}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except Exception:
            pass


@router.get("/stats")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics.
    
    Returns:
        Connection statistics including total connections and unique users
    """
    return JSONResponse(content=manager.get_stats())
