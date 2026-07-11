# backend/test_scheduler_flow.py
import asyncio
import sys
import uuid
from sqlalchemy import text
from app.db import async_session, get_node_runs
from app.models import GraphDefinition, NodeDefinition, NodeType
from app.scheduler import run_workflow

# Define Mock Handlers
async def dummy_fetch_data(node_input: dict) -> dict:
    company = node_input.get("company_name", "Unknown")
    print(f"[Handler] Fetching data for {company}...")
    await asyncio.sleep(1.0)  # Simulate network latency
    return {"status": "success", "data": f"Raw data for {company}"}

async def dummy_process_data(node_input: dict) -> dict:
    raw_info = node_input.get("raw_data", {})
    print(f"[Handler] Processing data: {raw_info}...")
    await asyncio.sleep(0.5)
    return {"processed": True, "details": raw_info.get("data", "")}

# Handler that always fails to test retries
fail_attempts = 0
async def dummy_flaky_handler(node_input: dict) -> dict:
    global fail_attempts
    fail_attempts += 1
    print(f"[Handler] Flaky handler execution (Attempt {fail_attempts})...")
    raise ValueError("Simulated network timeout.")

# Node handler registry mapping
MOCK_REGISTRY = {
    "fetch_data": dummy_fetch_data,
    "process_data": dummy_process_data,
    "flaky_handler": dummy_flaky_handler
}

# Define a 3-node graph using our validation model
graph = GraphDefinition(
    name="test_scheduler_graph",
    nodes=[
        NodeDefinition(
            id="node_1",
            type=NodeType.TOOL,
            handler="fetch_data",
            depends_on=[],
            max_retries=1,
            input_mapping={"company_name": "company"}
        ),
        NodeDefinition(
            id="node_2",
            type=NodeType.FUNCTION,
            handler="process_data",
            depends_on=["node_1"],
            max_retries=1,
            input_mapping={"raw_data": "node_1"}
        ),
        NodeDefinition(
            id="node_flaky",
            type=NodeType.TOOL,
            handler="flaky_handler",
            depends_on=[],
            max_retries=2,
            input_mapping={}
        )
    ]
)
async def setup_test_run(workflow_run_id: str):
    """Inserts a dummy workflow and run record to satisfy foreign keys."""
    async with async_session() as session:
        async with session.begin():
            # Clean up old records for this run if they exist
            await session.execute(
                text("DELETE FROM workflow_runs WHERE id = :id"), {"id": workflow_run_id}
            )
            
            # Insert a temporary workflow definitions record
            workflow_id = str(uuid.uuid4())
            await session.execute(
                text("""
                    INSERT INTO workflows (id, name, graph_definition)
                    VALUES (:id, 'Test Workflow', '{}'::jsonb)
                    ON CONFLICT DO NOTHING;
                """),
                {"id": workflow_id}
            )
            
            # Insert a temporary workflow runs record
            await session.execute(
                text("""
                    INSERT INTO workflow_runs (id, workflow_id, input_payload, status)
                    VALUES (:id, :w_id, '{"company": "Threadwright Inc."}'::jsonb, 'running')
                """),
                {"id": workflow_run_id, "w_id": workflow_id}
            )

async def print_database_results(workflow_run_id: str):
    """Helper to inspect the state of the database rows after execution."""
    print("\n--- Current Database State ---")
    node_states = await get_node_runs(workflow_run_id)
    for node_id, state in node_states.items():
        print(f"Node: {node_id:<12} | Status: {state['status']:<8} | Attempt: {state['attempt']} | Error: {state['error']}")
    print("------------------------------\n")

async def main():
    # Keep the execution ID stable so we can test resume/crash functionality
    test_run_id = "00000000-0000-0000-0000-000000000001"
    
    print("Initializing test database records...")
    await setup_test_run(test_run_id)
    
    print("\n--- TEST 1: Running Scheduler Loop ---")
    try:
        await run_workflow(
            workflow_run_id=test_run_id,
            graph=graph,
            node_registry=MOCK_REGISTRY,
            run_input={"company": "Threadwright Inc."}
        )
    except Exception as e:
        print(f"Scheduler execution encountered an unhandled exception: {e}", file=sys.stderr)
        
    await print_database_results(test_run_id)

if __name__ == "__main__":
    asyncio.run(main())