import asyncio
import uuid
import logging
import json
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from ..db import async_session
from ..scheduler import run_workflow
from workflows.company_research import COMPANY_RESEARCH_GRAPH, NODE_REGISTRY

logger = logging.getLogger(__name__)
router = APIRouter()

class CreateRunPayload(BaseModel):
    company_name: str
    job_description: Optional[str] = None  # New optional field
    inject_failure: Optional[bool] = False # Keeping your fault injection flag

@router.post("/runs")
async def start_workflow_run(payload: CreateRunPayload):
    """
    Creates a new workflow run record, schedules its execution in the 
    background, and immediately returns the run ID.
    """
    workflow_run_id = str(uuid.uuid4())
    company_name = payload.company_name.strip()
    
    # Safely handle the optional job description
    job_description = payload.job_description.strip() if payload.job_description else None

    if not company_name:
        raise HTTPException(status_code=400, detail="Company name cannot be blank.")

    logger.info(f"Initializing new workflow run request for: '{company_name}'")

    # Build the input payload dict for DB serialization and scheduler execution
    run_input = {
        "company_name": company_name,
        "job_description": job_description,
        "inject_failure": payload.inject_failure
    }

    async with async_session() as session:
        async with session.begin():
            # Ensure the base workflow definition exists in the database
            workflow_id = "00000000-0000-0000-0000-000000000000"
            await session.execute(
                text("""
                    INSERT INTO workflows (id, name, graph_definition)
                    VALUES (:id, :name, :graph_def)
                    ON CONFLICT (id) DO NOTHING;
                """),
                {
                    "id": workflow_id,
                    "name": COMPANY_RESEARCH_GRAPH.name,
                    "graph_def": COMPANY_RESEARCH_GRAPH.model_dump_json()
                }
            )

            # Insert the run tracking record using json.dumps for safe input_payload serialization
            await session.execute(
                text("""
                    INSERT INTO workflow_runs (id, workflow_id, input_payload, status)
                    VALUES (:run_id, :wf_id, :payload, 'pending');
                """),
                {
                    "run_id": workflow_run_id,
                    "wf_id": workflow_id,
                    "payload": json.dumps(run_input)
                }
            )

    # Trigger execution in the background; prevents the HTTP request from blocking
    asyncio.create_task(
        run_workflow(
            workflow_run_id=workflow_run_id,
            graph=COMPANY_RESEARCH_GRAPH,
            node_registry=NODE_REGISTRY,
            run_input=run_input  # Passing the updated dict containing the JD
        )
    )
    
    return {
        "workflow_run_id": workflow_run_id,
        "status": "pending"
    }


# Append this to the bottom of backend/app/routes/runs.py

@router.get("/runs/{workflow_run_id}")
async def get_run_status(workflow_run_id: str):
    """
    Retrieves the execution status and results for a specific workflow run 
    and all of its child node runs.
    """
    async with async_session() as session:
        # 1. Fetch the overall workflow run metadata
        run_query = await session.execute(
            text("""
                SELECT status, input_payload, created_at, updated_at
                FROM workflow_runs
                WHERE id = :id;
            """),
            {"id": workflow_run_id}
        )
        run_row = run_query.fetchone()
        
        if not run_row:
            raise HTTPException(status_code=404, detail="Workflow run not found.")

        # 2. Fetch all individual node execution records associated with this run
        nodes_query = await session.execute(
            text("""
                SELECT node_id, status, attempt, result, error, started_at, finished_at
                FROM node_runs
                WHERE workflow_run_id = :id;
            """),
            {"id": workflow_run_id}
        )
        node_rows = nodes_query.fetchall()

    # Format the node runs into a dictionary keyed by node_id
    nodes_state = {}
    for row in node_rows:
        nodes_state[row.node_id] = {
            "status": row.status,
            "attempt": row.attempt,
            "result": row.result,  # This contains our 'sources' or 'llm_provider' data
            "error": row.error,
            "started_at": row.started_at,
            "finished_at": row.finished_at
        }

    return {
        "workflow_run_id": workflow_run_id,
        "status": run_row.status,
        "input_payload": run_row.input_payload,
        "created_at": run_row.created_at,
        "updated_at": run_row.updated_at,
        "nodes": nodes_state
    }


# @router.get("/runs/{run_id}")
# async def get_run_status(run_id: str):
#     """
#     Fetches the current status of a workflow run and all its executed nodes.
#     Used by the frontend to hydrate state on refresh and fetch final results.
#     """
#     async with async_session() as session:
#         # 1. Verify the run exists and get its top-level status
#         run_result = await session.execute(
#             text("SELECT status FROM workflow_runs WHERE id = :run_id"),
#             {"run_id": run_id}
#         )
#         run_row = run_result.fetchone()
        
#         if not run_row:
#             raise HTTPException(status_code=404, detail="Workflow run not found")

#         # 2. Fetch all node states associated with this run
#         nodes_result = await session.execute(
#             text("SELECT node_id, status, result FROM node_runs WHERE workflow_run_id = :run_id"),
#             {"run_id": run_id}
#         )
        
#         # 3. Format into the dictionary shape the frontend expects
#         nodes_data = {}
#         for row in nodes_result.fetchall():
#             nodes_data[row.node_id] = {
#                 "status": row.status,
#                 "result": row.result  
#             }

#     return {
#         "workflow_run_id": run_id,
#         "status": run_row.status,
#         "nodes": nodes_data
#     }