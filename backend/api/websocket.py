"""WebSocket support for real-time pipeline updates."""

import structlog
import asyncio
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.services.storage import storage_service


logger = structlog.get_logger()

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for pipeline updates."""

    def __init__(self):
        """Initialize connection manager."""
        # Map pipeline_id -> set of websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.logger = logger

    async def connect(self, websocket: WebSocket, pipeline_id: str):
        """
        Connect a client to pipeline updates.

        Args:
            websocket: WebSocket connection
            pipeline_id: Pipeline to subscribe to
        """
        await websocket.accept()

        if pipeline_id not in self.active_connections:
            self.active_connections[pipeline_id] = set()

        self.active_connections[pipeline_id].add(websocket)

        self.logger.info(
            "websocket_connected",
            pipeline_id=pipeline_id,
            connections=len(self.active_connections[pipeline_id])
        )

    def disconnect(self, websocket: WebSocket, pipeline_id: str):
        """
        Disconnect a client.

        Args:
            websocket: WebSocket connection
            pipeline_id: Pipeline ID
        """
        if pipeline_id in self.active_connections:
            self.active_connections[pipeline_id].discard(websocket)

            if not self.active_connections[pipeline_id]:
                del self.active_connections[pipeline_id]

        self.logger.info(
            "websocket_disconnected",
            pipeline_id=pipeline_id
        )

    async def broadcast(self, pipeline_id: str, message: dict):
        """
        Broadcast update to all clients subscribed to a pipeline.

        Args:
            pipeline_id: Pipeline ID
            message: Message to broadcast
        """
        if pipeline_id not in self.active_connections:
            return

        # Send to all connected clients
        disconnected = []

        for websocket in self.active_connections[pipeline_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                self.logger.warning(
                    "websocket_send_error",
                    pipeline_id=pipeline_id,
                    error=str(e)
                )
                disconnected.append(websocket)

        # Clean up disconnected clients
        for ws in disconnected:
            self.disconnect(ws, pipeline_id)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/pipeline/{pipeline_id}")
async def pipeline_websocket(websocket: WebSocket, pipeline_id: str):
    """
    WebSocket endpoint for real-time pipeline updates.

    Args:
        websocket: WebSocket connection
        pipeline_id: Pipeline to subscribe to
    """
    await manager.connect(websocket, pipeline_id)

    try:
        # Send initial state
        state = await storage_service.load_pipeline_state(pipeline_id)

        if state:
            await websocket.send_json({
                "type": "initial_state",
                "data": {
                    "pipeline_id": state.pipeline_id,
                    "status": state.status.value,
                    "retry_count": state.retry_count,
                    "error": state.error
                }
            })

        # Poll for updates
        # In production, this should be event-driven via pub/sub
        last_updated = state.updated_at if state else None

        while True:
            await asyncio.sleep(2)  # Poll every 2 seconds

            current_state = await storage_service.load_pipeline_state(pipeline_id)

            if not current_state:
                continue

            # Check if state changed
            if last_updated is None or current_state.updated_at > last_updated:
                last_updated = current_state.updated_at

                # Broadcast update
                await websocket.send_json({
                    "type": "state_update",
                    "data": {
                        "pipeline_id": current_state.pipeline_id,
                        "status": current_state.status.value,
                        "retry_count": current_state.retry_count,
                        "error": current_state.error,
                        "updated_at": current_state.updated_at.isoformat()
                    }
                })

                # Send completion notification
                if current_state.status.value in ["completed", "partial", "failed"]:
                    await websocket.send_json({
                        "type": "pipeline_complete",
                        "data": {
                            "pipeline_id": current_state.pipeline_id,
                            "status": current_state.status.value,
                            "has_report": current_state.verifier_output is not None
                        }
                    })
                    break

    except WebSocketDisconnect:
        manager.disconnect(websocket, pipeline_id)
    except Exception as e:
        logger.error("websocket_error", pipeline_id=pipeline_id, error=str(e))
        manager.disconnect(websocket, pipeline_id)
