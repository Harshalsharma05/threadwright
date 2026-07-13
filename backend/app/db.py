from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from .config import settings

# Create the async engine
engine = create_async_engine(
    settings.database_url, 
    echo=False,
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0  # Disables prepared statement caching for transaction poolers
    }
)

# async_sessionmaker is the modern SQLAlchemy 2.0 utility designed specifically 
# for AsyncSession creation and type-safety.
async_session = async_sessionmaker(bind=engine, expire_on_commit=False)

async def mark_node_running(workflow_run_id: str, node_id: str, attempt: int):
    """
    Inserts or updates a node run record to 'running' status.
    Uses ON CONFLICT to ensure idempotency.
    """
    async with async_session() as session:
        async with session.begin():  # Explicit transaction boundary
            await session.execute(
                text("""
                    INSERT INTO node_runs (workflow_run_id, node_id, status, attempt, started_at)
                    VALUES (:wr, :nid, 'running', :attempt, NOW())
                    ON CONFLICT (workflow_run_id, node_id)
                    DO UPDATE SET status = 'running', attempt = :attempt, started_at = NOW(), finished_at = NULL, error = NULL;
                """),
                {"wr": workflow_run_id, "nid": node_id, "attempt": attempt},
            )

async def mark_node_done(workflow_run_id: str, node_id: str, result: dict):
    """
    Updates the node run status to 'done' and saves the JSON result in a single transaction.
    """
    import json
    async with async_session() as session:
        async with session.begin():  # Explicit transaction boundary
            await session.execute(
                text("""
                    UPDATE node_runs
                    SET status = 'done', result = :result, finished_at = NOW(), error = NULL
                    WHERE workflow_run_id = :wr AND node_id = :nid;
                """),
                {"wr": workflow_run_id, "nid": node_id, "result": json.dumps(result)},
            )

async def mark_node_failed(workflow_run_id: str, node_id: str, error: str):
    """
    Updates the node run status to 'failed' and records the traceback or error message.
    """
    async with async_session() as session:
        async with session.begin():  # Explicit transaction boundary
            await session.execute(
                text("""
                    UPDATE node_runs
                    SET status = 'failed', error = :error, finished_at = NOW()
                    WHERE workflow_run_id = :wr AND node_id = :nid;
                """),
                {"wr": workflow_run_id, "nid": node_id, "error": error},
            )

async def get_node_runs(workflow_run_id: str) -> dict[str, dict]:
    """
    Retrieves all executed or running nodes for a given workflow run.
    This is used by the scheduler to reconstruct the execution state upon crash/resume.
    """
    async with async_session() as session:
        result = await session.execute(
            text("""
                SELECT node_id, status, attempt, result, error, started_at, finished_at
                FROM node_runs
                WHERE workflow_run_id = :wr;
            """),
            {"wr": workflow_run_id},
        )
        
        node_runs_map = {}
        for row in result.fetchall():
            node_runs_map[row[0]] = {
                "status": row[1],
                "attempt": row[2],
                "result": row[3],
                "error": row[4],
                "started_at": row[5],
                "finished_at": row[6]
            }
        return node_runs_map