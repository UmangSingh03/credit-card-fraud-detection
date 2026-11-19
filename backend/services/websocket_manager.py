"""
WebSocket connection manager for real-time live events.
Broadcasts transaction events, alerts, simulation metrics, and training progress.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any
from fastapi import WebSocket, WebSocketDisconnect

from backend.core.logging_config import get_logger

logger = get_logger(__name__)


class WebSocketManager:
    """Manages active WebSocket connections and broadcasting."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, event_type: str, data: dict[str, Any]) -> None:
        """
        Broadcast a structured JSON message to all active clients.
        Drops disconnected clients gracefully.
        """
        message = json.dumps({"type": event_type, "data": data}, default=str)
        to_remove = []

        async with self._lock:
            connections = list(self.active_connections)

        for connection in connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket client: {e}")
                to_remove.append(connection)

        if to_remove:
            async with self._lock:
                for dead_conn in to_remove:
                    if dead_conn in self.active_connections:
                        self.active_connections.remove(dead_conn)


ws_manager = WebSocketManager()
