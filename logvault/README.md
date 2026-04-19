# LogVault

Self-hosted web-based log management and real-time log viewer with search, filtering, and analytics.

## Features

- Real-time log streaming via SSE
- Full-text and field-based search
- Filtering by level, service, host, time range
- Analytics dashboards with charts
- Single-binary deployment
- Optional authentication

## Quick Start (Docker)

```bash
cp .env.example .env

docker-compose up -d
```

Visit http://localhost:8080

## Quick Start (Binary)

Requirements: Go 1.21+, ClickHouse 24.x

```bash
# Start ClickHouse
docker run -d --name clickhouse \
  -p 9000:9000 -p 8123:8123 \
  clickhouse/clickhouse-server:24.3

# Build and run LogVault
go build -o logvault ./cmd/logvault
LOGVAULT_DB_HOST=localhost LOGVAULT_DB_PORT=9000 ./logvault
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| LOGVAULT_HOST | 0.0.0.0 | Server bind address |
| LOGVAULT_PORT | 8080 | Server port |
| LOGVAULT_BASE_URL | http://localhost:8080 | Public URL |
| LOGVAULT_DB_HOST | localhost | ClickHouse host |
| LOGVAULT_DB_PORT | 9000 | ClickHouse port |
| LOGVAULT_DB_USER | default | ClickHouse user |
| LOGVAULT_DB_PASSWORD | | ClickHouse password |
| LOGVAULT_DB_NAME | logs | Database name |
| LOGVAULT_AUTH_ENABLED | false | Enable authentication |
| LOGVAULT_USERNAME | admin | Auth username |
| LOGVAULT_PASSWORD | | Auth password |
| LOGVAULT_RETENTION_DAYS | 90 | Data retention |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/logs | Ingest log |
| POST | /api/v1/logs/batch | Ingest batch |
| GET | /api/v1/logs | Query logs |
| GET | /api/v1/stream | SSE stream |
| GET | /api/v1/analytics/summary | Summary |
| GET | /api/v1/analytics/volume | Volume |
| GET | /api/v1/analytics/levels | Levels |
| GET | /api/v1/health | Health check |

## Query Parameters

- `q` - Full-text search
- `level` - Log level (DEBUG, INFO, WARN, ERROR, FATAL)
- `service` - Service name
- `host` - Host name
- `from`, `to` - Time range (RFC3339)
- `limit` - Max results (default 100)
- `cursor` - Pagination cursor

## Ingestion Example

```bash
curl -X POST http://localhost:8080/api/v1/logs \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2026-04-19T10:30:00Z",
    "level": "INFO",
    "service": "api",
    "host": "server1",
    "message": "Request processed"
  }'
```

## Query Example

```bash
curl "http://localhost:8080/api/v1/logs?level=ERROR&limit=20"
```

## Tech Stack

- Backend: Go 1.21+
- Database: ClickHouse
- Frontend: HTMX + Alpine.js
- Router: chi