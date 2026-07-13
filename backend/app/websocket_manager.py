# backend/app/websocket_manager.py
import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Maps workflow_run_id (str) -> list of active WebSocket connections
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, workflow_run_id: str, websocket: WebSocket):
        """Accepts a new connection and registers it under the specific run ID."""
        await websocket.accept()
        self.active_connections.setdefault(workflow_run_id, []).append(websocket)
        logger.info(f"New client connected to live-updates for run: {workflow_run_id}")

    def disconnect(self, workflow_run_id: str, websocket: WebSocket):
        """Unregisters a client connection."""
        if workflow_run_id in self.active_connections:
            if websocket in self.active_connections[workflow_run_id]:
                self.active_connections[workflow_run_id].remove(websocket)
                logger.info(f"Client disconnected from run: {workflow_run_id}")
            
            # Clean up empty dictionary keys to conserve memory
            if not self.active_connections[workflow_run_id]:
                del self.active_connections[workflow_run_id]

    async def broadcast(self, workflow_run_id: str, message: dict):
        """
        Sends a JSON payload to all active clients listening to a specific run ID.
        Identifies and purges dead or broken sockets encountered during broadcast.
        """
        if workflow_run_id not in self.active_connections:
            return

        dead_connections = []
        for connection in self.active_connections[workflow_run_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send update to client. Queueing connection for removal. Error: {e}")
                dead_connections.append(connection)

        # Purge any stale connections discovered during this broadcast iteration
        for dead_conn in dead_connections:
            self.disconnect(workflow_run_id, dead_conn)


# Create a single, shared global instance of the connection manager
manager = ConnectionManager()


async def broadcast_status(workflow_run_id: str, node_id: str, status: str):
    """
    Standard interface used by the scheduler (and tools) to dispatch live updates
    to connected UI instances.
    """
    message = {
        "type": "node_status_update",
        "node_id": node_id,
        "status": status
    }
    await manager.broadcast(workflow_run_id, message)