# Threadwright — Implementation Plan

**Project name: Threadwright**
(A "wright" is a builder/craftsperson — a wheelwright, a shipwright. A "thread" here is a strand of execution — a branch in the workflow graph. Threadwright = someone who builds and weaves execution threads together. Short, unused as a platform name, and the metaphor holds up under interview questioning: branches are threads, the synthesis node is where they're woven together, and the engine is the loom.)

Alternate names if you want options for the repo: **Kilnframe**, **Warpline**, **Shuttlecraft**.

---

## What this document is

A phase-by-phase build plan for Threadwright — a self-built async DAG orchestration engine with a live-updating React UI, demoed via a "company research brief" workflow (news + GitHub + Reddit + job-posting branches → synthesis).

Rules this document follows:

- Frontend sections describe **files and responsibilities only** — no code. Whoever builds it (you, or an AI pair-programmer) should be able to construct the exact file from the description.
- Backend sections include **code/templates for the parts most likely to be implemented wrong** — the scheduler loop, the transaction boundary, the retry wrapper, the WebSocket push. Everything else is described.
- Every phase ends with a **"Definition of Done"** checklist so you know when to move on.

---

## Phase 0 — Project Scaffolding & Environment Setup

### Step 0.1 — Repo & folder structure

```
threadwright/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models.py
│   │   ├── db.py
│   │   ├── scheduler.py
│   │   ├── retry.py
│   │   ├── websocket_manager.py
│   │   ├── workflows/
│   │   │   └── company_research.py
│   │   ├── tools/
│   │   │   ├── tavily_client.py
│   │   │   ├── github_client.py
│   │   │   ├── reddit_client.py
│   │   │   └── llm_client.py
│   │   └── routes/
│   │       ├── runs.py
│   │       └── ws.py
│   ├── tests/
│   ├── .env.example
│   ├── requirements.txt
│   └── README.md
├── frontend/
│   ├── src/
│   ├── .env.example
│   ├── package.json
│   └── README.md
├── supabase/
│   └── schema.sql
├── docs/
│   ├── FAILURES.md
│   └── ARCHITECTURE.md
├── .gitignore
└── README.md
```

### Step 0.2 — Backend setup commands

```bash
mkdir -p threadwright/backend/app/{workflows,tools,routes}
cd threadwright/backend

python3 -m venv venv
source venv/bin/activate

pip install fastapi uvicorn[standard] asyncpg sqlalchemy[asyncio] \
            httpx python-dotenv pydantic praw websockets
```

Why each dependency:

- `fastapi` — the web framework; async-native, gives WebSocket support out of the box.
- `uvicorn[standard]` — ASGI server to actually run FastAPI.
- `asyncpg` + `sqlalchemy[asyncio]` — async Postgres driver + ORM, needed so DB writes don't block the event loop (critical since your whole concurrency story depends on nothing blocking).
- `httpx` — async HTTP client, used for Tavily/GitHub/LLM calls concurrently.
- `python-dotenv` — load `.env` config locally.
- `pydantic` — data validation for node/edge/graph schemas (ships with FastAPI, listed explicitly for clarity).
- `praw` — Reddit API wrapper, handles OAuth token exchange for you.
- `websockets` — underlying protocol library FastAPI uses for WS; explicit install avoids version issues.

Freeze once stable:

```bash
pip freeze > requirements.txt
```

### Step 0.3 — Frontend setup commands

```bash
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss-cli@latest init -p
npm install axios
```

Why each dependency:

- `vite` + `react` template — fast dev server, no need for CRA's slower tooling.
- `tailwindcss` — utility CSS for the DAG visualization and status colors without hand-writing a stylesheet.
- `axios` — simpler API for the one or two REST calls you'll need (starting a run); WebSocket itself uses the native browser `WebSocket` API, no library needed.

Update `tailwind.config.js` `content` array to include `./index.html` and `./src/**/*.{js,jsx}`, and add the three Tailwind directives (`@tailwind base/components/utilities`) to `src/index.css`.

### Step 0.4 — Supabase project setup

1. Create a free project at supabase.com.
2. Grab the **Project URL**, **anon key**, and **Postgres connection string** (Settings → Database).
3. Store these only in `.env` files (never commit them) — see `.env.example` templates below.

### Step 0.5 — Environment files

`backend/.env.example`:

```
DATABASE_URL=postgresql+asyncpg://postgres:<password>@<host>:5432/postgres
TAVILY_API_KEY=
GITHUB_TOKEN=
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=threadwright-research/0.1 by <your_reddit_username>
GROQ_API_KEY=
ANTHROPIC_API_KEY=
```

`frontend/.env.example`:

```
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

### Definition of Done — Phase 0

- [ ] Folder structure created exactly as above.
- [x] `backend` venv active, all packages installed, `requirements.txt` generated.
- [ ] `frontend` scaffolded with Vite+React, Tailwind configured and confirmed working (a test `bg-red-500` div renders red).
- [ ] Supabase project created, connection string obtained.
- [x] Both `.env` files created locally from the `.example` templates and added to `.gitignore`.

---

## Phase 1 — Database Schema (Supabase / Postgres)

### Step 1.1 — Design rationale

You need four tables:

- `workflows` — a saved graph definition (nodes + edges as JSON), reusable across runs.
- `workflow_runs` — one row per execution of a workflow (e.g., one "Razorpay" search).
- `node_runs` — one row per node, per run — this is the table your crash-resume demo depends on. Status and result are written **in the same transaction**.
- `node_run_events` (optional, for a richer trace) — append-only log of status transitions with timestamps, used to draw the "duration" timers in the UI.

### Step 1.2 — Schema script

Save as `supabase/schema.sql` and run via the Supabase SQL editor:

```sql
create table workflows (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    graph_definition jsonb not null,  -- {nodes: [...], edges: [...]}
    created_at timestamptz default now()
);

create table workflow_runs (
    id uuid primary key default gen_random_uuid(),
    workflow_id uuid references workflows(id),
    input_payload jsonb not null,     -- e.g. {"company_name": "Razorpay"}
    status text not null default 'pending', -- pending | running | done | failed
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

create table node_runs (
    id uuid primary key default gen_random_uuid(),
    workflow_run_id uuid references workflow_runs(id) on delete cascade,
    node_id text not null,            -- matches node id in graph_definition
    status text not null default 'pending', -- pending | running | done | failed
    attempt integer not null default 0,
    result jsonb,
    error text,
    started_at timestamptz,
    finished_at timestamptz,
    unique (workflow_run_id, node_id)
);

create table node_run_events (
    id bigserial primary key,
    node_run_id uuid references node_runs(id) on delete cascade,
    event_type text not null,   -- status_changed | retry | error
    detail jsonb,
    created_at timestamptz default now()
);

create index idx_node_runs_workflow_run on node_runs(workflow_run_id);
create index idx_events_node_run on node_run_events(node_run_id);
```

Why `unique (workflow_run_id, node_id)`: this constraint is what makes your persistence layer idempotent — if the scheduler ever tries to re-insert a node that already has a row (e.g., after a crash-restart), you `UPDATE` instead of `INSERT`, and the DB itself prevents duplicate rows if there's a logic bug.

### Definition of Done — Phase 1

- [ ] All four tables created in Supabase, visible in the Table Editor.
- [ ] Can manually insert a test row into `workflows` and query it back via the Supabase SQL editor.

---

## Phase 2 — Backend Core: Graph Models & Config

### Step 2.1 — `app/config.py`

Purpose: load `.env` values into a single typed settings object, used everywhere instead of scattered `os.getenv()` calls.

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    tavily_api_key: str
    github_token: str
    reddit_client_id: str
    reddit_client_secret: str
    reddit_user_agent: str
    groq_api_key: str
    anthropic_api_key: str

    class Config:
        env_file = ".env"

settings = Settings()
```

Note: `pydantic-settings` is a separate package from core `pydantic` v2 — add it: `pip install pydantic-settings`.

### Step 2.2 — `app/models.py`

Purpose: define the shape of a node, edge, and graph. This is the schema every other module imports.

```python
from pydantic import BaseModel
from typing import Literal, Optional
from enum import Enum

class NodeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"

class NodeType(str, Enum):
    TOOL = "tool"       # e.g. tavily search, github search, reddit search
    LLM = "llm"         # e.g. synthesis, job-posting parse
    FUNCTION = "function"  # plain python logic, no external call

class NodeDefinition(BaseModel):
    id: str                  # unique within a graph, e.g. "search_news"
    type: NodeType
    handler: str              # dotted path or registry key, e.g. "tools.tavily_client.search_news"
    depends_on: list[str] = []
    max_retries: int = 2
    input_mapping: dict = {}  # how to build this node's input from prior node outputs + run input

class GraphDefinition(BaseModel):
    name: str
    nodes: list[NodeDefinition]
```

Why `depends_on` lives on the node (not a separate edge list) even though the DB stores `graph_definition` as one JSON blob: it keeps the in-memory scheduling logic simple — computing "what's ready" is just "all ids in my `depends_on` have status DONE," no separate edge traversal needed.

### Definition of Done — Phase 2

- [ ] `config.py` loads `.env` correctly (`print(settings.tavily_api_key)` shows the real value, not empty).
- [ ] A hand-written `GraphDefinition` for the company-research workflow (5 nodes: search_news, github_signal, reddit_signal, parse_job, synthesize) validates without errors when constructed in a Python shell.

---

## Phase 3 — The Scheduler (core logic — this is the heart of the project)

### Step 3.1 — `app/db.py` — persistence layer

Purpose: every function that touches `node_runs` lives here, and every write is inside an explicit transaction. This is the file your crash-resume proof depends on — get the ordering right.

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def mark_node_running(workflow_run_id: str, node_id: str, attempt: int):
    async with async_session() as session:
        async with session.begin():  # transaction boundary
            await session.execute(
                """
                insert into node_runs (workflow_run_id, node_id, status, attempt, started_at)
                values (:wr, :nid, 'running', :attempt, now())
                on conflict (workflow_run_id, node_id)
                do update set status = 'running', attempt = :attempt, started_at = now()
                """,
                {"wr": workflow_run_id, "nid": node_id, "attempt": attempt},
            )

async def mark_node_done(workflow_run_id: str, node_id: str, result: dict):
    async with async_session() as session:
        async with session.begin():
            # status flip and result write happen in ONE transaction —
            # this is the line that makes crash-resume correct. If these were
            # two separate commits, a crash between them would leave a node
            # marked "done" with no result, or "running" with a result already
            # sitting there — both are corrupted states the scheduler can't
            # recover from cleanly.
            await session.execute(
                """
                update node_runs
                set status = 'done', result = :result, finished_at = now()
                where workflow_run_id = :wr and node_id = :nid
                """,
                {"wr": workflow_run_id, "nid": node_id, "result": result},
            )

async def mark_node_failed(workflow_run_id: str, node_id: str, error: str):
    ... # same pattern as mark_node_done, status='failed', error=error

async def get_node_runs(workflow_run_id: str) -> dict[str, dict]:
    # returns {node_id: {"status": ..., "result": ..., "attempt": ...}, ...}
    # used on scheduler startup/resume to know what's already done
    ...
```

Build `mark_node_failed` and `get_node_runs` following the exact same transaction pattern as `mark_node_done` — don't let an AI tool "simplify" these into two separate `execute()` calls outside a `session.begin()` block, since that reintroduces the exact bug the comment above describes.

### Step 3.2 — `app/retry.py` — retry/backoff wrapper

Purpose: a generic decorator applied to any node handler, not special-cased per node. This is what you point to in interviews to prove the retry logic is a primitive, not a hack.

```python
import asyncio
import random

async def run_with_retry(fn, *args, max_retries: int = 2, base_delay: float = 1.0, **kwargs):
    attempt = 0
    while True:
        try:
            return await fn(*args, **kwargs)
        except Exception as e:
            attempt += 1
            if attempt > max_retries:
                raise
            delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.3)
            await asyncio.sleep(delay)
```

Why exponential backoff with jitter (the `random.uniform` term): without jitter, if multiple nodes fail at once, they'd all retry at exactly the same moment and could hammer the same downstream API simultaneously — a detail worth mentioning if an interviewer asks "why not just fixed delay?"

### Step 3.3 — `app/scheduler.py` — the DAG execution loop

This is the single most important file in the project. Core algorithm:

```python
import asyncio
from .db import mark_node_running, mark_node_done, mark_node_failed, get_node_runs
from .retry import run_with_retry
from .websocket_manager import broadcast_status

async def run_workflow(workflow_run_id: str, graph, node_registry, run_input: dict):
    existing = await get_node_runs(workflow_run_id)  # resume support
    completed = {nid for nid, r in existing.items() if r["status"] == "done"}
    results = {nid: existing[nid]["result"] for nid in completed}

    remaining = {n.id: n for n in graph.nodes if n.id not in completed}

    while remaining:
        ready = [
            n for n in remaining.values()
            if all(dep in completed for dep in n.depends_on)
        ]
        if not ready:
            break  # nothing runnable -> either done or a stuck/failed dependency

        # THIS is the line that proves real parallelism: every ready node
        # is launched concurrently, not looped over with sequential awaits.
        await asyncio.gather(*[
            _execute_node(workflow_run_id, n, node_registry, run_input, results)
            for n in ready
        ])

        for n in ready:
            if n.id in results:
                completed.add(n.id)
                del remaining[n.id]
            else:
                del remaining[n.id]  # failed after retries; dependents won't become ready

async def _execute_node(workflow_run_id, node, node_registry, run_input, results):
    handler = node_registry[node.handler]
    node_input = _build_input(node, run_input, results)

    await mark_node_running(workflow_run_id, node.id, attempt=0)
    await broadcast_status(workflow_run_id, node.id, "running")

    try:
        result = await run_with_retry(handler, node_input, max_retries=node.max_retries)
        await mark_node_done(workflow_run_id, node.id, result)
        await broadcast_status(workflow_run_id, node.id, "done")
        results[node.id] = result
    except Exception as e:
        await mark_node_failed(workflow_run_id, node.id, str(e))
        await broadcast_status(workflow_run_id, node.id, "failed")

def _build_input(node, run_input, results):
    # combine run_input (e.g. company_name) with outputs of node.depends_on
    # using node.input_mapping — describe your own small convention here,
    # e.g. {"claim_from": "parse_job"} means "take output of parse_job node"
    ...
```

Why resume works with this structure: on startup, `get_node_runs` tells you which nodes are already `done` from a previous (crashed) attempt, so they're excluded from `remaining` entirely and never re-executed — only genuinely incomplete nodes run.

### Definition of Done — Phase 3

- [ ] Can run a fake graph of 3-4 dummy nodes (functions that just `asyncio.sleep` and return a string) end-to-end, see all rows correctly populated in `node_runs`.
- [ ] Kill the process mid-run (`Ctrl+C`) and restart with the same `workflow_run_id` — confirm only the in-flight node re-executes.
- [ ] Force one dummy node to always raise an exception — confirm it retries `max_retries` times with growing delay, then correctly marks `failed` and does not run dependents.

---

## Phase 4 — Real Node Implementations (tools/)

Each file in `app/tools/` exports one or more async functions matching the `handler` signature `async def fn(node_input: dict) -> dict`.

- **`tavily_client.py`** — wraps a POST to Tavily's search endpoint via `httpx.AsyncClient`, takes `{"query": ...}`, returns top results (title/url/snippet).
- **`github_client.py`** — wraps GitHub REST search (`/search/repositories` or `/orgs/{org}/repos`) via `httpx`, using `GITHUB_TOKEN` as a Bearer header for the higher rate limit.
- **`reddit_client.py`** — uses `praw` (sync library) — since `praw` isn't natively async, wrap calls with `asyncio.to_thread(...)` so they don't block the event loop. This is an important detail: describe it in `FAILURES.md` too, since it's a genuine gotcha ("praw is sync-only; used `asyncio.to_thread` to keep it from blocking the scheduler").
- **`llm_client.py`** — one function per LLM task (`parse_job_posting`, `synthesize_brief`), each an async call to Groq or Claude's API via `httpx`, given a prompt template and returning parsed/structured text (ask the model to return JSON and parse it, per your existing structured-output pattern from the RAG assistant project).

### Definition of Done — Phase 4

- [ ] Each tool function callable standalone (outside the scheduler) with a hardcoded input, returns real data.
- [ ] All four registered in a `node_registry` dict mapping string keys (matching `NodeDefinition.handler`) to these functions.

---

## Phase 5 — WebSocket Layer

### Step 5.1 — `app/websocket_manager.py`

Purpose: a simple in-memory registry of connected clients per `workflow_run_id`, and a `broadcast_status` function the scheduler calls on every status change.

```python
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active: dict[str, list[WebSocket]] = {}

    async def connect(self, workflow_run_id: str, ws: WebSocket):
        await ws.accept()
        self.active.setdefault(workflow_run_id, []).append(ws)

    def disconnect(self, workflow_run_id: str, ws: WebSocket):
        self.active.get(workflow_run_id, []).remove(ws)

    async def broadcast(self, workflow_run_id: str, message: dict):
        for ws in self.active.get(workflow_run_id, []):
            await ws.send_json(message)

manager = ConnectionManager()

async def broadcast_status(workflow_run_id: str, node_id: str, status: str):
    await manager.broadcast(workflow_run_id, {"node_id": node_id, "status": status})
```

### Step 5.2 — `app/routes/ws.py` and `app/routes/runs.py`

- `routes/runs.py`: one `POST /runs` endpoint — accepts `{"company_name": "..."}`, creates a `workflow_run` row, kicks off `run_workflow(...)` as a background task (`asyncio.create_task` or FastAPI's `BackgroundTasks`), returns the `workflow_run_id` immediately so the frontend can open a WebSocket for it.
- `routes/ws.py`: one `WS /ws/{workflow_run_id}` endpoint that calls `manager.connect(...)`, then just waits (`await ws.receive_text()` in a loop, ignoring input) until disconnect — all real traffic flows server→client via `broadcast`.

### Definition of Done — Phase 5

- [ ] Using a WebSocket testing tool (e.g. browser dev console, or `websocat`), connect to `/ws/{id}`, trigger a run via `POST /runs`, confirm status messages arrive live in the correct order.

---

## Phase 6 — Frontend (description only — no code here)

### File-by-file description

`frontend/src/main.jsx` — standard Vite entry point, mounts `<App />`.

`frontend/src/App.jsx` — top-level component. Holds: the company-name/job-URL text input, a "Run" button, and renders `<GraphView />` once a run has started. On "Run" click: calls `POST /runs` via `axios`, gets back a `workflow_run_id`, stores it in state, and passes it down to `<GraphView />`.

`frontend/src/hooks/useWorkflowSocket.js` — a custom React hook. Takes a `workflow_run_id`, opens a `WebSocket` to `${VITE_WS_BASE_URL}/ws/{id}` on mount, listens for incoming JSON messages (`{node_id, status}`), and maintains a state object `{ [node_id]: status }` that it returns. Closes the socket on unmount. This hook is the single source of truth the rest of the UI reads from — no component should manage WebSocket connections itself.

`frontend/src/components/GraphView.jsx` — renders the DAG. Takes the graph definition (can be a hardcoded JS object matching the backend's 5-node company-research graph, or fetched from the backend — hardcoding is fine for a demo since the graph shape doesn't change) and the live status map from `useWorkflowSocket`. Lays out nodes in columns by dependency depth (news/github/reddit/parse_job in column 1, synthesize in column 2) using plain CSS flex/grid — no graph-drawing library needed for 5 nodes. Renders each node as a `<NodeBox />`.

`frontend/src/components/NodeBox.jsx` — a single box: node label, a colored status dot (gray/yellow/green/red mapped from the status prop via Tailwind classes), and — if you choose to track it — an elapsed-time counter (can compute from a `started_at` timestamp broadcast alongside status, added as an enhancement once the base flow works).

`frontend/src/components/ResultPanel.jsx` — once the `synthesize` node's status is `done`, fetch (or receive via the same WebSocket, as an additional message type) its result and render the final research brief as readable text below the graph.

`frontend/src/components/DemoControls.jsx` — (optional but recommended, since it's what makes the crash-resume and retry demos self-serve for an interviewer) a small panel with: a "kill server" instruction/button (can just be a text note "run `kill %1` in terminal" if you don't want to expose an actual kill endpoint for safety reasons), and a toggle sent to the backend as a query param/body field like `inject_failure: true` on the `search_news` node, so you can trigger the retry demo on demand instead of hoping it happens naturally.

`frontend/src/index.css` — Tailwind directives only.

`frontend/tailwind.config.js` — standard config, `content` paths as set up in Phase 0.

### Definition of Done — Phase 6

- [ ] Typing a company name and clicking "Run" shows the graph, nodes light up live, final brief renders once synthesis completes.
- [ ] Refreshing the page mid-run and reconnecting the WebSocket still shows correct current state (bonus: fetch current `node_runs` status via a `GET /runs/{id}` REST endpoint on mount, so state isn't lost on refresh even without replaying WS history).

---

## Phase 7 — Demo Hardening

### Step 7.1 — Fault injection for the retry demo

Add an optional `inject_failure_prob: float` field to the run-creation payload; when set, wrap the `search_news` handler so it randomly raises before actually calling Tavily, based on that probability. This makes the retry demo reliably triggerable on request rather than hoping a real API call fails during a live demo.

### Step 7.2 — `docs/FAILURES.md`

Write this as you go, not at the end. Format: one entry per real bug — what broke, why, the fix. Example entries to aim for:

- The `praw` sync-in-async gotcha (Phase 4).
- Any transaction-ordering bug you hit before landing on the pattern in Phase 3.
- Any WebSocket race condition (client connects after the run already started and misses early events) — fix: have `GET /runs/{id}` return current state on connect, so the frontend always reconciles instead of relying purely on live messages.

### Step 7.3 — `docs/ARCHITECTURE.md`

One diagram (can be a simple exported image or ASCII) of the flow: React → REST (start run) → Scheduler → asyncio.gather → tool clients → Postgres (transactional writes) → WebSocket → React. This is what you show first before diving into code, in an interview.

### Definition of Done — Phase 7

- [ ] Retry demo triggerable on demand via the fault-injection flag.
- [ ] `FAILURES.md` has at least 3 real entries.
- [ ] `ARCHITECTURE.md` has the one-diagram overview.

---

## Phase 8 — Optional Deployment (skip if short on time — not required for a live/recorded demo)

- Backend: Render or Railway free tier, pointing at the same Supabase Postgres instance.
- Frontend: Vercel or Netlify free tier, `VITE_API_BASE_URL`/`VITE_WS_BASE_URL` pointed at the deployed backend.
- Note: free-tier backends often spin down when idle — mention this if you deploy, so an interviewer isn't confused by a slow first request.

---

## Final Checklist Before Calling It Resume-Ready

- [ ] End-to-end run works with a real, arbitrary company name typed live.
- [ ] Crash-resume demo works reliably, at an arbitrary kill point.
- [ ] Retry-with-backoff demo works reliably, on demand.
- [ ] `FAILURES.md` and `ARCHITECTURE.md` are present and specific.
- [ ] README explains the project in the first three sentences without needing you to narrate it.
- [ ] Repo is public, named `threadwright` (or your chosen alternate).
