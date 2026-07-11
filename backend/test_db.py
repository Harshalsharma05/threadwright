# backend/test_db.py
import asyncio
import sys
from sqlalchemy import text
from app.db import async_session

async def test_db_connection():
    print("Testing connection and table presence...")
    try:
        async with async_session() as session:
            # Test simple connectivity
            result = await session.execute(text("SELECT 1;"))
            print(f"Database connection: OK (Result: {result.scalar()})")

            # Check if our critical tables exist
            tables = ["workflows", "workflow_runs", "node_runs", "node_run_events"]
            for table in tables:
                query = text(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :table);"
                )
                res = await session.execute(query, {"table": table})
                exists = res.scalar()
                print(f"Table '{table}' status: {'FOUND' if exists else 'MISSING'}")
                if not exists:
                    raise ValueError(f"Table {table} is missing from the database.")
            
            print("Database schema verification passed.")
    except Exception as e:
        print(f"Database verification failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_db_connection())