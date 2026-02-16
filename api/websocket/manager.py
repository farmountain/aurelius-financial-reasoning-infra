"""WebSocket connection manager for handling multiple client connections."""

import json
import logging
from typing import Dict, List, Set
from fastapi import WebSocket

from websocket.contract import SUPPORTED_EVENTS, build_ws_message

logger = logging.getLogger(__name__)
DEFAULT_EVENT = "connected"


class ConnectionManager:
    """
    Manages WebSocket connections and message broadcasting.
    
    Supports:
    - Multiple concurrent connections
    - User-specific subscriptions
    - Event-based message routing
    - Automatic cleanup on disconnect
    """

    def __init__(self):
        # Store active connections: {user_id: [websockets]}
        self.active_connections: Dict[str, List[WebSocket]] = {}

        # Track subscriptions: {user_id: set(event_types)}
        self.subscriptions: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            user_id: The authenticated user's ID
        """
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
            self.subscriptions[user_id] = set()

        self.active_connections[user_id].append(websocket)

        # Default subscriptions for all users
        self.subscriptions[user_id].update([
            "strategy_created",
            "backtest_started",
            "backtest_completed",
            "backtest_failed",
            "validation_completed",
            "gate_verified",
            "reflexion_iteration_created",
            "orchestrator_run_created",
            "orchestrator_stage_updated",
        ])

        logger.info(f"WebSocket connected for user {user_id}. Total connections: {self._get_connection_count()}")

    def disconnect(self, websocket: WebSocket, user_id: str):
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection to remove
            user_id: The user's ID
        """
        if user_id in self.active_connections:
            try:
                self.active_connections[user_id].remove(websocket)
            except ValueError:
                pass

            # Clean up empty lists
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                if user_id in self.subscriptions:
                    del self.subscriptions[user_id]

        logger.info(f"WebSocket disconnected for user {user_id}. Total connections: {self._get_connection_count()}")

    async def send_personal_message(self, message: dict, user_id: str):
        """
        Send a message to a specific user's connections.
        
        Args:
            message: The message to send (will be JSON-encoded)
            user_id: The target user's ID
        """
        if user_id not in self.active_connections:
            return

        event = message.get("event") or message.get("type") or DEFAULT_EVENT
        if event not in SUPPORTED_EVENTS:
            logger.warning("Non-canonical websocket event '%s' mapped to '%s'", event, DEFAULT_EVENT)
            event = DEFAULT_EVENT
        payload = message.get("payload")
        if payload is None:
            payload = message.get("data", {})
        envelope = build_ws_message(event, payload)
        message_text = json.dumps(envelope)
        dead_connections = []

        for connection in self.active_connections[user_id]:
            try:
                await connection.send_text(message_text)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                dead_connections.append(connection)

        # Clean up dead connections
        for dead in dead_connections:
            self.disconnect(dead, user_id)

    async def broadcast(self, message: dict, event_type: str = None):
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: The message to send (will be JSON-encoded)
            event_type: Optional event type to filter by subscriptions
        """
        event = event_type or message.get("event") or message.get("type") or DEFAULT_EVENT
        if event not in SUPPORTED_EVENTS:
            logger.warning("Non-canonical websocket event '%s' mapped to '%s'", event, DEFAULT_EVENT)
            event = DEFAULT_EVENT
        payload = message.get("payload")
        if payload is None:
            payload = message.get("data", {})
        message_text = json.dumps(build_ws_message(event, payload))
        dead_connections = []

        for user_id, connections in list(self.active_connections.items()):
            # Check if user is subscribed to this event type
            if event_type and event_type not in self.subscriptions.get(user_id, set()):
                continue

            for connection in connections:
                try:
                    await connection.send_text(message_text)
                except Exception as e:
                    logger.error(f"Error broadcasting to user {user_id}: {e}")
                    dead_connections.append((connection, user_id))

        # Clean up dead connections
        for dead, user_id in dead_connections:
            self.disconnect(dead, user_id)

    async def subscribe(self, user_id: str, event_types: List[str]):
        """
        Subscribe a user to specific event types.
        
        Args:
            user_id: The user's ID
            event_types: List of event types to subscribe to
        """
        if user_id not in self.subscriptions:
            self.subscriptions[user_id] = set()

        self.subscriptions[user_id].update(event_types)
        logger.info(f"User {user_id} subscribed to: {event_types}")

    async def unsubscribe(self, user_id: str, event_types: List[str]):
        """
        Unsubscribe a user from specific event types.
        
        Args:
            user_id: The user's ID
            event_types: List of event types to unsubscribe from
        """
        if user_id in self.subscriptions:
            self.subscriptions[user_id].difference_update(event_types)
            logger.info(f"User {user_id} unsubscribed from: {event_types}")

    def _get_connection_count(self) -> int:
        """Get the total number of active connections."""
        return sum(len(conns) for conns in self.active_connections.values())

    def get_stats(self) -> dict:
        """
        Get statistics about active connections.
        
        Returns:
            Dictionary with connection statistics
        """
        return {
            "total_connections": self._get_connection_count(),
            "unique_users": len(self.active_connections),
            "connections_by_user": {
                user_id: len(conns)
                for user_id, conns in self.active_connections.items()
            }
        }


# Global connection manager instance
manager = ConnectionManager()
