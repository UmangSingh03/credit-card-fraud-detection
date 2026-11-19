"""
WebSocket endpoint for real-time live event streaming.
"""
from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.core.logging_config import get_logger
from backend.services.websocket_manager import ws_manager

logger = get_logger(__name__)
router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Accept real-time WebSocket connection and keep open for server pushes."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Receive client ping or heartbeat messages
            data = await websocket.receive_text()
            # Respond with pong if requested
            if data == "ping":
                await websocket.send_text('{"type": "pong"}')
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket connection error: {e}")
        await ws_manager.disconnect(websocket)
