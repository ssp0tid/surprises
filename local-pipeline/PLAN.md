# Implementation Plan: local-pipeline

## Project Overview

**local-pipeline** is a YAML-based local task pipeline/orchestrator that enables users to define, schedule, and execute multi-step workflows via declarative YAML configuration files. It provides DAG-based task scheduling, cron-style triggers, SQLite-backed execution history, parallel execution, and a web dashboard for monitoring and manual intervention.

**Target Users/Use Cases:**
- DevOps engineers automating local workflows
- Data engineers running ETL pipelines
- Developers needing task orchestration for scripts/CI/CD
- System administrators automating maintenance tasks
- Anyone needing cron-style but more powerful task orchestration

## Core Features

All features listed in the requirements will be implemented:
- YAML-based pipeline definitions with full schema validation
- DAG scheduling with explicit task dependencies
- Cron-style triggers (via croniter)
- SQLite execution history with full audit trail
- Parallel task execution (threading-based workers)
- Retry logic with configurable attempts/exponential backoff
- Web dashboard for viewing runs/history
- Manual trigger API (REST endpoints)
- Webhook endpoint for external triggers

## Dependencies

**Python packages with version constraints:**
- `fastapi>=0.100.0` - Web framework
- `uvicorn[standard]>=0.23.0` - ASGI server
- `sqlalchemy>=2.0.0` - ORM
- `apscheduler>=3.10.0` - Cron scheduling
- `pyyaml>=6.0` - YAML parsing
- `pydantic>=2.0.0` - Schema validation
- `pydantic-settings>=2.0.0` - Configuration
- `aiosqlite>=0.19.0` - Async SQLite driver
- `apscheduler` - Job scheduling
- `python-croniter>=1.4.0` - Cron parsing

**Dev dependencies:**
- `pytest>=7.0.0`
- `pytest-asyncio>=0.21.0`
- `pytest-cov>=4.0.0`
- `ruff>=0.1.0`

## Architecture & File Structure

```
local-pipeline/
├── src/local_pipeline/
│   ├── __init__.py
│   ├── config.py           # Configuration management
│   ├── models.py           # Pydantic schemas & DB models
│   ├── database.py         # SQLAlchemy setup
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── scheduler.py   # DAG topological sort
│   │   ├── executor.py     # Task execution engine
│   │   ├── workers.py     # Thread pool workers
│   │   └── retry.py       # Retry logic
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py      # All REST endpoints
│   │   ├── webhooks.py    # Webhook handlers
│   │   └── schemas.py      # Request/response models
│   ├── web/
│   │   ├── __init__.py
│   │   ├── router.py      # Dashboard routes
│   │   └── templates.py   # HTML templates
│   ├── parser/
│   │   ├── __init__.py
│   │   ├── loader.py      # YAML file loading
│   │   ├── validator.py   # Schema validation
│   │   └── models.py      # Pipeline/task models
│   ├── triggers/
│   │   ├── __init__.py
│   │   ├── cron.py        # Cron trigger handler
│   │   ├── manual.py      # Manual trigger handler
│   │   └── webhook.py    # Webhook trigger handler
│   └── utils/
│       ├── __init__.py
│       └── logging.py    # Logging setup
├── pipelines/             # Pipeline YAML files
│   └── example.yaml
├── data/                  # SQLite database
│   └── local_pipeline.db
├── static/               # Dashboard static files
│   ├── css/
│   │   └── styles.css
│   └── js/
│       └── dashboard.js
├── tests/
│   ├── __init__.py
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── pyproject.toml
├── uv.lock
├── README.md
├── CONFIG.md
├── AGENTS.md
└── PLAN.md
```

## YAML Pipeline Schema

```yaml
# pipelines/example.yaml
name: "example-pipeline"
description: "Example pipeline demonstrating all features"
version: "1.0"

# Trigger configuration
triggers:
  - type: cron
    cron: "0 * * *"           # Every hour
  - type: webhook            # Enable webhook trigger
  - type: manual            # Enable manual trigger
  - type: interval
    seconds: 3600           # Every hour (alternative)

# Global retry configuration
retry:
  max_attempts: 3
  backoff_factor: 2.0       # Exponential backoff
  initial_delay: 1          # Initial delay in seconds

# Default timeout for all tasks
default_timeout: 300       # 5 minutes

# Tasks definitions
tasks:
  # Shell command task
  - id: task_1
    name: "Fetch Data"
    type: shell
    command: "curl -s https://api.example.com/data"
    env:
      API_KEY: "${ENV_API_KEY}"
    timeout: 60
    retry:
      max_attempts: 2
    output_file: /tmp/data.json
  
  # Python script task
  - id: task_2
    name: "Process Data"
    type: python
    script: ./scripts/process.py
    args:
      - --input
      - /tmp/data.json
      - --output
      - /tmp/processed.json
    dependencies: [task_1]
    timeout: 120
  
  # HTTP request task
  - id: task_3
    name: "Upload Results"
    type: http
    method: POST
    url: https://api.example.com/upload
    headers:
      Authorization: "Bearer ${API_TOKEN}"
    body:
      file: /tmp/processed.json
    dependencies: [task_2]
  
  # Parallel tasks (both depend on task_1)
  - id: task_4a
    name: "Task 4a"
    type: shell
    command: "echo 'Running 4a'"
    dependencies: [task_1]
  
  - id: task_4b
    name: "Task 4b"
    type: shell
    command: "echo 'Running 4b'"
    dependencies: [task_1]

# DAG example showing parallel execution:
# task_1 -> [task_4a, task_4b] -> task_3
```

**Full schema in JSON Schema format** will be defined in `src/local_pipeline/parser/validator.py`

## Database Schema

```sql
-- Pipelines table
CREATE TABLE pipelines (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    version TEXT NOT NULL,
    yaml_path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

CREATE INDEX idx_pipelines_name ON pipelines(name);
CREATE INDEX idx_pipelines_active ON pipelines(is_active);

-- Runs table
CREATE TABLE runs (
    id TEXT PRIMARY KEY,
    pipeline_id TEXT NOT NULL REFERENCES pipelines(id),
    run_number INTEGER NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending', 'running', 'success', 'failed', 'cancelled')),
    triggered_by TEXT NOT NULL,
    trigger_source TEXT,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_runs_pipeline ON runs(pipeline_id);
CREATE INDEX idx_runs_status ON runs(status);
CREATE INDEX idx_runs_created ON runs(created_at);

-- Tasks table
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(id),
    pipeline_task_id TEXT NOT NULL,
    name TEXT NOT NULL,
    task_type TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending', 'running', 'success', 'failed', 'skipped', 'retrying')),
    output TEXT,
    error TEXT,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    duration_ms INTEGER,
    attempt INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tasks_run ON tasks(run_id);
CREATE INDEX idx_tasks_status ON tasks(status);

-- Task dependencies table
CREATE TABLE task_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL REFERENCES tasks(id),
    depends_on_task_id TEXT NOT NULL REFERENCES tasks(id),
    depends_on_task_ref TEXT NOT NULL,
    
    UNIQUE(task_id, depends_on_task_ref)
);

CREATE INDEX idx_deps_task ON task_dependencies(task_id);
CREATE INDEX idx_deps_on ON task_dependencies(depends_on_task_id);

-- Execution logs table
CREATE TABLE execution_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT REFERENCES tasks(id),
    run_id TEXT REFERENCES runs(id),
    level TEXT NOT NULL CHECK(level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR')),
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_logs_task ON execution_logs(task_id);
CREATE INDEX idx_logs_run ON execution_logs(run_id);
```

## API Design

**RESTful endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/pipelines | List all pipelines |
| POST | /api/v1/pipelines | Register a new pipeline |
| GET | /api/v1/pipelines/{id} | Get pipeline details |
| PUT | /api/v1/pipelines/{id} | Update pipeline |
| DELETE | /api/v1/pipelines/{id} | Delete pipeline |
| POST | /api/v1/pipelines/{id}/trigger | Trigger pipeline manually |
| POST | /api/v1/pipelines/{id}/cancel | Cancel running pipeline |
| GET | /api/v1/runs | List runs (with filters) |
| GET | /api/v1/runs/{id} | Get run details |
| GET | /api/v1/runs/{id}/tasks | Get tasks for a run |
| GET | /api/v1/tasks/{id} | Get task execution details |
| POST | /api/v1/tasks/{id}/retry | Retry failed task |
| GET | /api/v1/health | Health check |
| GET | /api/v1/metrics | System metrics |

**Webhook endpoint:**
- POST `/api/v1/webhooks/{pipeline_id}` - Trigger via webhook
- Body: `{"event": "push", "payload": {...}, "signature": "sha256=..."}`

**Request/response formats:**
```json
// POST /api/v1/pipelines
{
  "name": "my-pipeline",
  "description": "Pipeline description",
  "yaml_content": "..."  // or yaml_path
}

// GET /api/v1/runs?status=running&pipeline_id=xxx
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20
}

// Webhook payload
{
  "event": "push",
  "source": "github",
  "payload": {
    "ref": "refs/heads/main",
    "before": "abc123",
    "after": "def456"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Execution Engine

**DAG topological sort:**
```python
def topological_sort(tasks: list[Task]) -> list[Task]:
    # Kahn's algorithm for topological sorting
    # Detects circular dependencies
    # Returns ordered list respecting dependencies
```

**Parallel execution strategy:**
- Build dependency graph from YAML
- Identify "ready" tasks (all deps satisfied, not running)
- Execute ready tasks in thread pool
- On task completion, update graph and queue new ready tasks
- Maximum parallelism controlled by config (default: 4)

**Task worker model:**
- ThreadPoolExecutor for I/O-bound tasks (shell, http)
- Configurable worker pool size
- Per-task timeout enforcement
- Graceful shutdown on cancellation

## Error Handling

**Task failure handling:**
- Mark task as failed, log error
- Check retry configuration
- If retry available, schedule retry with backoff
- If no retry, mark dependent tasks as skipped
- Update run status accordingly

**Retry logic implementation:**
```python
class RetryPolicy:
    max_attempts: int = 3
    backoff_factor: float = 2.0
    initial_delay: float = 1.0
    
    def get_delay(self, attempt: int) -> float:
        return self.initial_delay * (self.backoff_factor ** (attempt - 1))
```

**Timeout handling:**
- Per-task timeout from YAML (default: 300s)
- Thread-based timeout enforcement
- Cancel task thread on timeout
- Treat as failure, apply retry policy

**Deadlock prevention:**
- Validate pipeline YAML on load
- Detect circular dependencies via topological sort
- Reject invalid pipelines with clear error

## Edge Cases

| Edge Case | Handling |
|-----------|----------|
| Circular dependency | Validate on load, reject with error message |
| Task timeout | Cancel thread, mark failed, apply retry |
| Database locking | Use WAL mode, transaction retry |
| Webhook authentication | Optional HMAC signature verification |
| Pipeline validation | YAML schema validation + DAG validation |
| Concurrent run handling | Queue runs, allow config for parallelism |
| Partial failure recovery | Allow selective task retry |

## Web Dashboard

**UI pages/routes:**

| Route | Description |
|-------|-------------|
| / | Dashboard home - list pipelines |
| /pipelines | Pipeline list with status |
| /pipelines/{id} | Pipeline detail with runs |
| /runs | All runs with filters |
| /runs/{id} | Run detail with task graph |
| /settings | Configuration settings |

**Data visualization:**
- Run status badges (pending/running/success/failed/cancelled)
- Duration timing (bar charts for tasks)
- Success/failure rates (pie charts)
- Timeline view for recent runs

**Actions available:**
- Trigger pipeline (manual button)
- Cancel running pipeline
- Retry failed tasks
- View logs/output
- Download artifacts

## Implementation Phases

**Phase 1 - MVP (Priority: Critical)**
- Project scaffolding
- YAML parser with schema validation
- Database setup with SQLAlchemy
- Basic execution engine (sequential)
- Shell task execution
- CLI tool
- Basic API endpoints
- Health check

**Phase 2 - Core Features (Priority: High)**
- DAG topological sort
- Parallel execution
- Retry logic
- Cron triggers
- Webhook endpoint
- Manual trigger API

**Phase 3 - Dashboard (Priority: Medium)**
- Web dashboard UI
- Run history view
- Task detail view
- Trigger/cancel actions
- Basic statistics

**Phase 4 - Polish (Priority: Low)**
- Advanced retry policies
- Task output capture
- Execution logs
- Metrics API
- Configuration UI

## Configuration

**Config file (config.yaml):**
```yaml
server:
  host: "0.0.0.0"
  port: 8080
  
database:
  url: "sqlite+aiosqlite:///data/local_pipeline.db"
  
execution:
  max_parallel_tasks: 4
  default_timeout: 300
  shutdown_timeout: 30
  
scheduler:
  timezone: "UTC"
  max_history_days: 30
  
webhooks:
  secret: "${WEBHOOK_SECRET}"
  enabled: true
  
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

**Environment variables:**
- `LOCAL_PIPELINE_CONFIG` - Path to config file
- `LOCAL_PIPELINE_DB_PATH` - Database path
- `LOCAL_PIPELINE_PORT` - Server port
- `WEBHOOK_SECRET` - Webhook HMAC secret

**CLI flags:**
```
local-pipeline serve --config config.yaml
local-pipeline run --pipeline my-pipeline
local-pipeline validate --file pipeline.yaml
local-pipeline web --port 8080
```

## Atomic Commit Strategy

Commits organized by feature with TDD approach:

```
1. project-scaffold           # pyproject.toml, directories, basic imports
2. config-models             # Pydantic models, config loading
3. database-setup            # SQLAlchemy models, migrations
4. yaml-parser               # YAML loading, schema validation
5. execution-engine-core    # Sequential task execution
6. dag-scheduler            # Topological sort, dependency graph
7. parallel-execution        # Thread pool execution
8. retry-logic              # Retry policies, backoff
9. cron-triggers            # APScheduler integration
10. api-routes              # REST endpoints
11. webhook-handler         # Webhook processing
12. web-dashboard           # HTML dashboard
13. cli-tool                # CLI commands
14. integration-tests       # Full integration tests
15. polish                  # Final refinements
```

Each commit should:
- Pass all tests (unit + integration)
- Pass lint/type check
- Be atomic and reversible
- Include clear commit message

## TDD-Oriented Planning

**Test strategy:**
1. **Unit tests**: Parser, validator, scheduler, retry logic
2. **Integration tests**: Full pipeline execution
3. **API tests**: All endpoints with FastAPI TestClient
4. **E2E tests**: Full workflow via dashboard

**Test fixtures:**
- Sample pipeline YAML files
- Mock task outputs
- Database fixtures

**QA verification:**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/local_pipeline --cov-report=html

# Lint
ruff check src/

# Type check
mypy src/
```