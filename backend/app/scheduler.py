import asyncio
import logging
from typing import Any, Dict
from .models import GraphDefinition, NodeDefinition
from .db import mark_node_running, mark_node_done, mark_node_failed, get_node_runs
from .retry import run_with_retry
from .websocket_manager import broadcast_status

logger = logging.getLogger(__name__)

async def run_workflow(
    workflow_run_id: str, 
    graph: GraphDefinition, 
    node_registry: Dict[str, Any], 
    run_input: Dict[str, Any]
):
    """
    Executes a directed acyclic graph (DAG) workflow run.
    Reconstructs progress for crash recovery and runs available nodes concurrently.
    """
    logger.info(f"Starting workflow run {workflow_run_id}")
    
    # 1. Reconstruct current progress for crash-resume support
    existing = await get_node_runs(workflow_run_id)
    completed = {nid for nid, r in existing.items() if r["status"] == "done"}
    results = {nid: existing[nid]["result"] for nid in completed}

    # Identify which nodes still need execution
    remaining = {n.id: n for n in graph.nodes if n.id not in completed}

    # 2. Main Scheduling Loop
    while remaining:
        # Identify nodes whose dependencies are all completed
        ready = [
            n for n in remaining.values()
            if all(dep in completed for dep in n.depends_on)
        ]
        
        if not ready:
            if remaining:
                # If we have nodes left but none are ready, we may have hit a cycle 
                # or an upstream dependency failed.
                failed_upstream = any(
                    existing.get(dep, {}).get("status") == "failed"
                    for n in remaining.values()
                    for dep in n.depends_on
                )
                if failed_upstream:
                    logger.warning("Execution stopped: Upstream node execution failed.")
                else:
                    logger.error("Deadlock detected: Possible circular dependency in graph definition.")
            break

        # 3. Parallel Execution Boundary
        # Run all currently eligible nodes concurrently
        logger.info(f"Concurrently executing ready nodes: {[n.id for n in ready]}")
        await asyncio.gather(*[
            _execute_node(workflow_run_id, n, node_registry, run_input, results)
            for n in ready
        ])

        # 4. Post-execution status check
        for n in ready:
            if n.id in results:
                completed.add(n.id)
                del remaining[n.id]
            else:
                # If the node did not populate its output in results, it failed.
                # Remove it so we do not attempt to run it again, but block its descendants.
                del remaining[n.id]

    logger.info(f"Workflow run {workflow_run_id} execution loop completed.")


async def _execute_node(
    workflow_run_id: str, 
    node: NodeDefinition, 
    node_registry: Dict[str, Any], 
    run_input: Dict[str, Any], 
    results: Dict[str, Any]
):
    """
    Handles state transition, dynamic input composition, execution, and output logging for a node.
    """
    handler = node_registry.get(node.handler)
    if not handler:
        error_msg = f"Handler '{node.handler}' not found in registry."
        logger.error(error_msg)
        await mark_node_failed(workflow_run_id, node.id, error_msg)
        await broadcast_status(workflow_run_id, node.id, "failed")
        return

    # Build node input using mapped values from initial input and prior results
    try:
        node_input = _build_input(node, run_input, results)
    except Exception as e:
        error_msg = f"Failed to build input for node '{node.id}': {e}"
        logger.error(error_msg)
        await mark_node_failed(workflow_run_id, node.id, error_msg)
        await broadcast_status(workflow_run_id, node.id, "failed")
        return

    # Mark as running in Database and notify WebSocket
    await mark_node_running(workflow_run_id, node.id, attempt=0)
    await broadcast_status(workflow_run_id, node.id, "running")

    # Execute wrapped inside the retry handler
    try:
        result = await run_with_retry(handler, node_input, max_retries=node.max_retries)
        await mark_node_done(workflow_run_id, node.id, result)
        await broadcast_status(workflow_run_id, node.id, "done")
        results[node.id] = result
    except Exception as e:
        await mark_node_failed(workflow_run_id, node.id, str(e))
        await broadcast_status(workflow_run_id, node.id, "failed")


def _build_input(node: NodeDefinition, run_input: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assembles input dictionary for a node according to its input_mapping definitions.
    Example: 
      input_mapping = {"query": "company_name"} 
      looks up 'company_name' in run_input or upstream node results.
    """
    node_input = {}
    for target_key, source_key in node.input_mapping.items():
        # 1. Check if the mapping source points directly to an upstream node's output structure
        if source_key in results:
            node_input[target_key] = results[source_key]
        # 2. Check if the mapping source is present in the initial workflow input payload
        elif source_key in run_input:
            node_input[target_key] = run_input[source_key]
        # 3. Default fallback: apply direct string values if no exact dynamic source matches
        else:
            node_input[target_key] = source_key
            
    return node_input