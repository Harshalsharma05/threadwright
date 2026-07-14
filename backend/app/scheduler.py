import asyncio
import logging
import random
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
    Natively manages the retry loop to broadcast intermediate failure and backoff states to the UI.
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
        node_input["workflow_run_id"] = workflow_run_id
        node_input["inject_failure"] = run_input.get("inject_failure", False)
    except Exception as e:
        error_msg = f"Failed to build input for node '{node.id}': {e}"
        logger.error(error_msg)
        await mark_node_failed(workflow_run_id, node.id, error_msg)
        await broadcast_status(workflow_run_id, node.id, "failed")
        return

    attempt = 0
    max_retries = node.max_retries
    base_delay = 1.0

    while True:
        # 1. Start execution attempt: mark 'running' (turns Yellow on UI)
        logger.info(f"Executing node {node.id} (Attempt {attempt + 1}/{max_retries + 1})")
        await mark_node_running(workflow_run_id, node.id, attempt=attempt)
        await broadcast_status(workflow_run_id, node.id, "running")

        try:
            # Run the actual node handler
            result = await handler(node_input)
            
            # 2. Success: mark 'done' and notify UI (turns Green on UI)
            await mark_node_done(workflow_run_id, node.id, result)
            await broadcast_status(workflow_run_id, node.id, "done")
            results[node.id] = result
            break  # Exit retry loop on success

        except Exception as e:
            attempt += 1
            if attempt > max_retries:
                # 3. Permanent Failure: final write and notify UI (turns Red permanently)
                logger.error(f"Node {node.id} failed permanently after {attempt} attempts. Error: {e}")
                await mark_node_failed(workflow_run_id, node.id, str(e))
                await broadcast_status(workflow_run_id, node.id, "failed")
                break

            # 4. Intermediate Failure: mark 'failed' and notify UI (turns Red during sleep)
            error_msg = f"Attempt {attempt}/{max_retries + 1} failed: {e}"
            logger.warning(f"Node {node.id} intermediate failure: {error_msg}")
            
            await mark_node_failed(workflow_run_id, node.id, error_msg)
            await broadcast_status(workflow_run_id, node.id, "failed")

            # Calculate backoff delay with jitter
            delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.3)
            logger.warning(f"Node {node.id} sleeping for {delay:.2f}s before next attempt...")
            await asyncio.sleep(delay)

def _build_input(node, run_input, results):
    """
    Constructs the input payload for a specific node by pulling data 
    from the initial run_input or from the outputs of upstream nodes.
    """
    node_input = {}
    
    for target_key, mapping_rules in node.input_mapping.items():
        # Check if this input comes from the initial payload (e.g., POST body)
        if "from_input" in mapping_rules:
            source_key = mapping_rules["from_input"]
            node_input[target_key] = run_input.get(source_key)
            
        # Check if this input comes from a previously executed node
        elif "from_node" in mapping_rules:
            source_node_id = mapping_rules["from_node"]
            node_input[target_key] = results.get(source_node_id)
            
    return node_input

# def _build_input(node: NodeDefinition, run_input: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
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