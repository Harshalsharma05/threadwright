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