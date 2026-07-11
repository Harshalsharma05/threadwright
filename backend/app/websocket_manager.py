import logging

logger = logging.getLogger(__name__)

async def broadcast_status(workflow_run_id: str, node_id: str, status: str):
    """
    Placeholder broadcast function to be implemented in Phase 5.
    """
    logger.info(f"[WS BROADCAST] Run: {workflow_run_id} | Node: {node_id} | Status: {status}")