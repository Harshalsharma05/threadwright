# A WebSocket route that hooks into our ConnectionManager to stream node status changes.
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..websocket_manager import manager

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws/{workflow_run_id}")
async def websocket_endpoint(websocket: WebSocket, workflow_run_id: str):
    """
    Listens for updates regarding a specific workflow run.
    Keeps the connection open until the client disconnects.
    """
    await manager.connect(workflow_run_id, websocket)
    try:
        # Keep connection open. We ignore incoming messages because communication 
        # is strictly outbound (Server -> Client) for this workflow pattern.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(workflow_run_id, websocket)
    except Exception as e:
        logger.error(f"Unexpected WebSocket disconnection: {e}")
        manager.disconnect(workflow_run_id, websocket)