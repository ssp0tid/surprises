# Local Pipeline

A YAML-based local task pipeline/orchestrator with DAG scheduling, parallel execution, retry logic, and a web dashboard.

## Features

- YAML-based pipeline definitions with schema validation
- DAG scheduling with topological sort
- Parallel task execution
- Retry logic with exponential backoff
- Cron-style triggers
- Webhook support for external triggers
- Manual trigger API
- SQLite-backed execution history
- Web dashboard with run history

## Requirements

- Python 3.11+
- uv (optional, for dependency management)

## Installation

```bash
# Clone the repository
cd local-pipeline

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Or with uv
uv pip install -e ".[dev]"
```

## Configuration

Create a `config.yaml` file:

```yaml
server:
  host: "0.0.0.0"
  port: 8080

database:
  url: "sqlite+aiosqlite:///data/local_pipeline.db"

execution:
  max_parallel_tasks: 4
  default_timeout: 300

scheduler:
  timezone: "UTC"

webhooks:
  secret: ""
  enabled: true
```

## Usage

### Starting the Server

```bash
python -m local_pipeline.main
# Or with custom config
python -m local_pipeline.main --config config.yaml
```

The server will start on `http://localhost:8080`

### Creating a Pipeline

Via API:

```bash
curl -X POST http://localhost:8080/api/v1/pipelines \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-pipeline",
    "description": "My first pipeline",
    "yaml_content": "name: my-pipeline\nversion: 1.0\ntasks:\n  - id: task1\n    name: Hello\n    type: shell\n    command: echo Hello"
  }'
```

### Triggering a Pipeline

```bash
curl -X POST http://localhost:8080/api/v1/pipelines/{pipeline_id}/trigger
```

### Webhook Trigger

```bash
curl -X POST http://localhost:8080/api/v1/webhooks/{pipeline_id} \
  -H "Content-Type: application/json" \
  -d '{"event": "push", "source": "github", "payload": {}}'
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/pipelines | List pipelines |
| POST | /api/v1/pipelines | Create pipeline |
| GET | /api/v1/pipelines/{id} | Get pipeline |
| PUT | /api/v1/pipelines/{id} | Update pipeline |
| DELETE | /api/v1/pipelines/{id} | Delete pipeline |
| POST | /api/v1/pipelines/{id}/trigger | Trigger pipeline |
| POST | /api/v1/pipelines/{id}/cancel | Cancel pipeline |
| GET | /api/v1/runs | List runs |
| GET | /api/v1/runs/{id} | Get run details |
| GET | /api/v1/runs/{id}/tasks | Get tasks for run |
| GET | /api/v1/health | Health check |
| GET | /api/v1/metrics | System metrics |

## Web Dashboard

- `/` - Dashboard home
- `/pipelines` - Pipeline list
- `/pipelines/{id}` - Pipeline detail
- `/runs` - All runs
- `/runs/{id}` - Run detail

## Pipeline YAML Schema

```yaml
name: "pipeline-name"
description: "Pipeline description"
version: "1.0"

triggers:
  - type: cron
    cron: "0 * * *"
  - type: webhook
  - type: manual
  - type: interval
    seconds: 3600

retry:
  max_attempts: 3
  backoff_factor: 2.0
  initial_delay: 1

default_timeout: 300

tasks:
  - id: task_1
    name: "Task Name"
    type: shell  # shell, python, http
    command: "echo hello"
    dependencies: []
    timeout: 60
    retry:
      max_attempts: 2
```

## Development

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src/local_pipeline --cov-report=html

# Lint
ruff check src/
```

## License

MIT
