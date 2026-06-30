"""WebSocket router for real-time dashboard events streaming."""

import asyncio
import json
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/api/ws")

class ConnectionManager:
    """Manages active WebSocket connections and broadcasts events."""

    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Send a JSON payload to all connected clients."""
        payload = json.dumps(message)
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception:
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)

manager = ConnectionManager()

@router.websocket("")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection endpoint."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, listen for any client messages (not strictly needed)
            data = await websocket.receive_text()
            # Echo or ignore
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


# Custom Logger Handler for live log streaming to dashboard
class DashboardLogHandler(logging.Handler):
    """Logging handler redirecting log logs to connected WebSockets."""

    def __init__(self, connection_manager: ConnectionManager) -> None:
        super().__init__()
        self.manager = connection_manager
        # Avoid infinite recursion when websockets library logs itself
        self.setLevel(logging.INFO)

    def emit(self, record: logging.LogRecord) -> None:
        # Ignore websockets internal logging to prevent loop feedbacks
        if "websockets" in record.name or "uvicorn" in record.name:
            return

        try:
            log_message = self.format(record)
            payload = {
                "type": "log",
                "timestamp": record.created,
                "level": record.levelname,
                "message": log_message,
                "logger": record.name
            }
            # Run broadcast in the main bot loop asynchronously
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.manager.broadcast(payload))
        except Exception:
            pass
