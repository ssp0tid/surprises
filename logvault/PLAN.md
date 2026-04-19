# LogVault - Implementation Plan

**Self-hosted web-based log management and real-time log viewer with search, filtering, and analytics**

---

## 1. Project Overview

### 1.1 Purpose

LogVault is a self-hosted, lightweight log management system providing:
- Real-time log streaming via WebSocket/SSE
- Full-text and field-based search
- Filtering by level, service, time range
- Analytics dashboards with charts and aggregations
- Single-binary deployment (no external dependencies)

### 1.2 Target Users

- Developers debugging applications
- DevOps Engineers monitoring services
- Small-to-medium teams needing self-hosted log aggregation

### 1.3 Scope

| Feature | In Scope | Out of Scope |
|---------|----------|--------------|
| Real-time tail | ✅ | - |
| Search/Filter | ✅ | Distributed clustering |
| Analytics | ✅ | ML-based anomaly detection |
| Alerting | Basic thresholds | Complex rules |
| Single-node deployment | ✅ | Multi-node HA |

---

## 2. Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Clients                                  │
│  (Browser) ←── SSE/WebSocket ──→ (API Server) ←─────────────→  │
└─────────────────────────────────────────────────────────────────┘
                                              │
                            ┌─────────────────┴─────────────────┐
                            │                               │
                            ▼                               ▼
                    ┌──────────────┐               ┌──────────────┐
                    │ ClickHouse   │               │  UI Assets   │
                    │ (logs.db)   │               │  (static)    │
                    └──────────────┘               └──────────────┘
```

### 2.2 Core Components

| Component | Responsibility | Mode |
|-----------|---------------|------|
| HTTP Server | REST API, static files | Single process |
| WebSocket Server | Real-time log streaming | Same process |
| Log Ingestor | Parse, validate, write to DB | Same process |
| Query Engine | Search, filter, aggregate | Same process |

### 2.3 Data Flow

```
Application Logs
       │
       ▼
  ┌─────────┐    ┌──────────────┐    ┌─────────────┐
  │ Ingest  │───▶│ Parse & Index │───▶│ ClickHouse  │
  │ endpoint│    │ (timestamp,   │    │ (app_logs   │
  └─────────┘    │  level, msg)  │    │  table)     │
                 └──────────────┘                 │
                         │                        │
                         ▼                        ▼
                  WebSocket                Query API
                  broadcast                (filter/search)
```

---

## 3. Tech Stack

### 3.1 Technology Choices

| Layer | Technology | Rationale |
|-------|------------|----------|
| Language | Go | Single binary, performance, simplicity |
| Database | **ClickHouse** | 10-20x compression, 50-200 MB/s ingest, analytical queries |
| Frontend | **HTMX + Alpine.js** | No build step, progressive enhancement |
| Real-time | **Server-Sent Events** | Simpler than WebSocket, auto-reconnect, HTTP-compatible |
| Config | **ENV files** | No external config dependency |
| HTTP Router | chi | Lightweight, Go-native |

### 3.2 Why These Choices

**Backend: Go**
- Single binary deployment (no runtime required)
- Excellent performance for log ingestion
- Great ecosystem (chi, golang.org/x/crypto)
- ClickHouse has official Go client

**Database: ClickHouse**
- Columnar storage: 15-25x compression for logs
- Analytical queries: ~100ms on 1B rows vs seconds in PostgreSQL
- Append-only: perfect for log write patterns
- Self-hostable: single binary or Docker

**Frontend: HTMX + Alpine.js**
- No npm, no build: edit in browser
- Progressive enhancement works without JS
- Small footprint (~14KB total)
- Easy integration with Go templates

---

## 4. File Structure

```
logvault/
├── cmd/
│   └── logvault/
│       └── main.go              # Entry point
├── internal/
│   ├── config/
│   │   └── config.go           # Configuration
│   ├── server/
│   │   ├── server.go           # HTTP server setup
│   │   ├── routes.go           # Route definitions
│   │   └── middleware.go      # Auth, CORS, logging
│   ├── handler/
│   │   ├── ingest.go           # POST /api/v1/logs
│   │   ├── query.go            # GET /api/v1/logs
│   │   ├── stream.go          # SSE endpoint
│   │   ├── analytics.go       # GET /api/v1/analytics
│   │   └── auth.go            # Login/logout
│   ├── db/
│   │   ├── client.go          # ClickHouse client
│   │   ├── migrations.go      # Schema setup
│   │   └── queries.go         # Query builders
│   ├── logparser/
│   │   ├── parser.go          # Log parsing
│   │   └── levels.go          # Log level constants
│   ├── analytics/
│   │   ├── engine.go         # Aggregation engine
│   │   └── aggregations.go   # Query templates
│   └── model/
│       └── types.go          # Data types
├── web/
│   ├── index.html            # Main app
│   ├── css/
│   │   └── app.css           # Styles
│   └── js/
│       └── app.js            # Client-side JS (minimal)
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── migrations/
│   └── 001_create_logs.sql
├── go.mod
├── go.sum
└── PLAN.md
```

---

## 5. Database Schema

### 5.1 Log Table (ClickHouse)

```sql
CREATE TABLE app_logs (
    timestamp DateTime64(3),
    level Enum8('DEBUG'=1, 'INFO'=2, 'WARN'=3, 'ERROR'=4, 'FATAL'=5),
    service String,
    host String,
    message String,
    metadata String,           -- JSON for additional fields
    _raw String              -- Original log line for full-text search
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (service, timestamp, level)
TTL timestamp + INTERVAL 90 DAY
SETTINGS index_granularity = 8192;
```

### 5.2 Index Design

| Field | Type | Purpose |
|-------|------|---------|
| `timestamp` | DateTime64(3) | Time filtering, sorting |
| `level` | Enum8 | Fast level filtering |
| `service` | String | Service filtering |
| `host` | String | Host filtering |
| `message` | String | Full-text search |
| `_raw` | String | Raw storage |
| `metadata` | JSON | Additional fields |

### 5.3 Partitioning Strategy

- **Partition**: Monthly (`toYYYYMM(timestamp)`)
- **Order by**: `(service, timestamp, level)`
- **TTL**: 90 days (configurable)
- **Index granularity**: 8192 (balance between index size and query speed)

---

## 6. API Design

### 6.1 REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/logs` | Ingest a log entry |
| POST | `/api/v1/logs/batch` | Ingest multiple log entries |
| GET | `/api/v1/logs` | Query logs with filters |
| GET | `/api/v1/logs/:id` | Get single log by ID |
| GET | `/api/v1/stream` | SSE for real-time logs |
| GET | `/api/v1/analytics/summary` | Overview metrics |
| GET | `/api/v1/analytics/volume` | Log volume over time |
| GET | `/api/v1/analytics/levels` | Log level distribution |
| POST | `/api/v1/auth/login` | Login |
| POST | `/api/v1/auth/logout` | Logout |
| GET | `/api/v1/health` | Health check |

### 6.2 Query Parameters

**GET /api/v1/logs**

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `q` | string | Full-text search | `q=timeout` |
| `level` | string | Log level filter | `level=ERROR` |
| `service` | string | Service filter | `service=api` |
| `host` | string | Host filter | `host=server1` |
| `from` | datetime | Start time | `from=2026-04-19T00:00:00Z` |
| `to` | datetime | End time | `to=2026-04-19T12:00:00Z` |
| `limit` | int | Max results (default 100) | `limit=50` |
| `cursor` | string | Cursor for pagination | `cursor=abc123` |
| `sort` | string | Sort field | `sort=timestamp` |
| `order` | string | Sort order | `order=desc` |

### 6.3 Request/Response Examples

**Ingest Single Log**
```bash
POST /api/v1/logs
Content-Type: application/json

{
  "timestamp": "2026-04-19T10:30:00Z",
  "level": "INFO",
  "service": "api",
  "host": "server1",
  "message": "Request processed",
  "metadata": {
    "method": "GET",
    "path": "/api/health",
    "status": 200
  }
}
```

**Response**
```json
{
  "id": "20260419_1_1",
  "success": true
}
```

**Query Logs**
```bash
GET /api/v1/logs?level=ERROR&service=api&from=2026-04-19T00:00:00Z&limit=20
```

**Response**
```json
{
  "logs": [
    {
      "id": "20260419_1_1",
      "timestamp": "2026-04-19T10:30:00Z",
      "level": "ERROR",
      "service": "api",
      "host": "server1",
      "message": "Connection timeout",
      "metadata": {"error": "ETIMEDOUT"}
    }
  ],
  "cursor": "next_cursor_value",
  "total": 150
}
```

---

## 7. Real-Time Streaming (SSE)

### 7.1 SSE Endpoint

```
GET /api/v1/stream?level=ERROR&service=api
```

**Response (text/event-stream)**
```
id: 1700000001
data: {"timestamp":"2026-04-19T10:30:01Z","level":"ERROR","message":"..."}

id: 1700000002
data: {"timestamp":"2026-04-19T10:30:02Z","level":"ERROR","message":"..."}
```

### 7.2 Client Implementation

```javascript
const es = new EventSource('/api/v1/stream?level=ERROR');

es.onmessage = (e) => {
  const log = JSON.parse(e.data);
  appendLogLine(log);
};

es.onerror = () => {
  // EventSource auto-reconnects with Last-Event-ID
};
```

### 7.3 Connection Resumption

Client sends `Last-Event-ID` header on reconnect. Server resumes from that point:

```go
func (s *Server) handleStream(w http.ResponseWriter, r *http.Request) {
    lastID := r.Header.Get("Last-Event-ID")
    
    // If lastID provided, query from that point
    // Otherwise start from now()
}
```

### 7.4 Broadcasting

```go
type Broadcaster struct {
    clients map[chan string]Filter
    mu      sync.RWMutex
}

func (b *Broadcaster) Send(log LogEntry) {
    b.mu.RLock()
    defer b.mu.RUnlock()
    
    for ch, filter := range b.clients {
        if filter.Matches(log) {
            select {
            case ch <- logJSON:
            default:
            }
        }
    }
}
```

---

## 8. Authentication

### 8.1 Simple Auth (Single User)

```go
type Config struct {
    AuthEnabled  bool   // Default: false
    Username     string // Admin username
    PasswordHash string // bcrypt hash
}
```

### 8.2 Session Management

```
Session token: JWT with expiry (24h default)
Storage: In-memory (single instance) or Redis (optional)
Refresh: Automatic on activity
```

### 8.3 Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/login` | POST | Login with credentials |
| `/api/v1/auth/logout` | POST | Invalidate session |
| `/api/v1/auth/me` | GET | Get current user |

### 8.4 Middleware

```go
func AuthMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        if !config.AuthEnabled {
            next.ServeHTTP(w, r)
            return
        }
        
        token := r.Header.Get("Authorization")
        if token == "" {
            token = r.Cookie("session").Value
        }
        
        if !ValidateToken(token) {
            http.Error(w, "Unauthorized", 401)
            return
        }
        
        next.ServeHTTP(w, r)
    })
}
```

---

## 9. Analytics

### 9.1 Summary Endpoint

**GET /api/v1/analytics/summary**

```json
{
  "total_logs": 1250000,
  "logs_last_24h": 45000,
  "error_count": 234,
  "error_rate": 0.52,
  "services": ["api", "worker", "scheduler"],
  "time_range": {
    "oldest": "2026-04-18T10:30:00Z",
    "newest": "2026-04-19T10:30:00Z"
  }
}
```

### 9.2 Volume Over Time

**GET /api/v1/analytics/volume?interval=1h&from=2026-04-18T00:00:00Z**

```json
{
  "interval": "1h",
  "data": [
    {"timestamp": "2026-04-18T01:00:00Z", "count": 1200},
    {"timestamp": "2026-04-18T02:00:00Z", "count": 980},
    {"timestamp": "2026-04-18T03:00:00Z", "count": 450}
  ]
}
```

### 9.3 Level Distribution

**GET /api/v1/analytics/levels**

```json
{
  "by_count": [
    {"level": "INFO", "count": 45000},
    {"level": "ERROR", "count": 234},
    {"level": "WARN", "count": 89},
    {"level": "DEBUG", "count": 12}
  ],
  "by_percentage": [
    {"level": "INFO", "percentage": 99.26},
    {"level": "ERROR", "percentage": 0.52},
    {"level": "WARN", "percentage": 0.20},
    {"level": "DEBUG", "percentage": 0.03}
  ]
}
```

### 9.4 Service Breakdown

**GET /api/v1/analytics/services?from=2026-04-18T00:00:00Z**

```json
{
  "data": [
    {"service": "api", "total": 45000, "errors": 200},
    {"service": "worker", "total": 12000, "errors": 34},
    {"service": "scheduler", "total": 5000, "errors": 0}
  ]
}
```

---

## 10. Error Handling

### 10.1 HTTP Status Codes

| Status | Usage |
|--------|-------|
| 200 | Success |
| 201 | Created |
| 400 | Bad request (invalid JSON, missing fields) |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not found |
| 413 | Payload too large |
| 422 | Unprocessable (validation error) |
| 429 | Rate limited |
| 500 | Internal server error |
| 503 | Service unavailable |

### 10.2 Error Response Format

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Missing required field: timestamp",
    "details": {
      "field": "timestamp",
      "reason": "must be RFC3339 format"
    }
  }
}
```

### 10.3 Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| INVALID_REQUEST | 400 | Malformed request |
| MISSING_FIELD | 400 | Required field missing |
| INVALID_TIMESTAMP | 400 | Invalid timestamp format |
| NOT_FOUND | 404 | Resource not found |
| UNAUTHORIZED | 401 | Missing/invalid auth |
| FORBIDDEN | 403 | Insufficient permissions |
| RATE_LIMITED | 429 | Too many requests |
| INTERNAL_ERROR | 500 | Server error |

### 10.4 Logging Errors

```go
func (s *Server) logError(r *http.Request, err error) {
    logEntry := LogEntry{
        timestamp: time.Now(),
        level:    "ERROR",
        service: "logvault",
        message: err.Error(),
        metadata: map[string]interface{}{
            "path":   r.URL.Path,
            "method": r.Method,
            "remote": r.RemoteAddr,
        },
    }
    s.db.Insert(logEntry)
}
```

---

## 11. Edge Cases

### 11.1 Large Payloads

| Edge Case | Handling |
|----------|----------|
| Log message > 1MB | Truncate to 1MB, flag as truncated |
| Batch > 1000 logs | Process in chunks of 100 |
| Metadata > 64KB | Store raw, index limited fields |

### 11.2 Time Edge Cases

| Edge Case | Handling |
|----------|----------|
| No timestamp provided | Use server time |
| Future timestamp | Allow (up to +1 hour) |
| Very old timestamp | Allow if within retention |
| Invalid format | Return 400 |

### 11.3 Rate Limiting

| Scope | Limit | Window |
|-------|-------|-------|
| IP | 1000 req/min | Per IP |
| Authenticated | 10000 req/min | Per user |
| Ingest | 5000 logs/sec | Per service |

### 11.4 Query Edge Cases

| Edge Case | Handling |
|----------|----------|
| No results | Return empty array, 200 |
| Query too slow | Timeout after 30s |
| Invalid level | Return empty |
| Malformed cursor | Reset pagination |

### 11.5 Connection Edge Cases

| Edge Case | Handling |
|----------|----------|
| SSE timeout | Auto-reconnect with Last-Event-ID |
| Client disconnect | Clean up channel |
| Server restart | Client reconnects |
| Network drop | Browser auto-retry |

### 11.6 Data Edge Cases

| Edge Case | Handling |
|----------|----------|
| Unknown level | Default to INFO |
| Empty message | Allow (log may be empty) |
| Special characters | Escape properly |
| Binary in message | Sanitize to UTF-8 |

---

## 12. Configuration

### 12.1 Environment Variables

```bash
# Server
LOGVAULT_HOST=0.0.0.0
LOGVAULT_PORT=8080
LOGVAULT_BASE_URL=http://localhost:8080

# Database
LOGVAULT_DB_HOST=localhost
LOGVAULT_DB_PORT=9000
LOGVAULT_DB_USER=default
LOGVAULT_DB_PASSWORD=
LOGVAULT_DB_NAME=logs

# Auth
LOGVAULT_AUTH_ENABLED=false
LOGVAULT_USERNAME=admin
LOGVAULT_PASSWORD=

# Retention
LOGVAULT_RETENTION_DAYS=90

# Limits
LOGVAULT_MAX_MESSAGE_SIZE=1048576
LOGVAULT_MAX_BATCH_SIZE=1000
LOGVAULT_RATE_LIMIT=5000
```

### 12.2 Docker

```yaml
version: '3.8'
services:
  logvault:
    image: logvault:latest
    ports:
      - "8080:8080"
    environment:
      - LOGVAULT_DB_HOST=clickhouse
      - LOGVAULT_DB_PORT=9000
      - LOGVAULT_AUTH_ENABLED=true
      - LOGVAULT_USERNAME=admin
      - LOGVAULT_PASSWORD=${LOGVAULT_PASSWORD}
    volumes:
      - ./data:/data

  clickhouse:
    image: clickhouse/clickhouse-server
    ports:
      - "9000:9000"
    volumes:
      - ./clickhouse/data:/var/lib/clickhouse
```

---

## 13. Implementation Phases

### Phase 1: Core (Day 1-2)
- [x] Project setup (Go module, deps)
- [x] ClickHouse schema
- [x] HTTP server with chi
- [x] Log ingest endpoint
- [x] Basic query endpoint

### Phase 2: Search & Filter (Day 3-4)
- [x] Full-text search
- [x] Level filtering
- [x] Service/host filtering
- [x] Time range filtering
- [x] Pagination (cursor-based)

### Phase 3: Real-time (Day 5)
- [x] SSE endpoint
- [x] Broadcasting
- [x] Client-side connection
- [x] Reconnection handling

### Phase 4: UI & Analytics (Day 6-7)
- [x] Dashboard UI
- [x] Summary metrics
- [x] Volume chart
- [x] Level distribution

### Phase 5: Auth & Polish (Day 8)
- [x] Basic auth
- [x] Error handling
- [x] Docker setup
- [x] Testing

---

## 14. Out of Scope (Future)

- Multi-node clustering
- Distributed ingestion
- Complex alerting rules
- ML-based anomaly detection
- Log correlation/tracing
- LDAP/SSO integration
- Custom plugins
- Metrics storage

---

## 15. Dependencies

```go
github.com/ClickHouse/clickhouse-go/v2       // ClickHouse client
github.com/go-chi/chi/v5               // HTTP router
github.com/golang-jwt/jwt/v5            // JWT auth
golang.org/x/crypto/bcrypt                // Password hashing
gopkg.in/yaml.v3                        // Config (optional)
```

```html
<!-- Frontend (CDN) -->
<script src="https://unpkg.com/htmx.org@1.9.10"></script>
<script src="https://unpkg.com/alpinejs@3.13.5"></script>
```

---

## 16. Summary

LogVault provides a self-hosted, lightweight log management solution with:

| Feature | Implementation |
|---------|--------------|
| Real-time | SSE with cursor resumption |
| Search | Full-text + field filters |
| Storage | ClickHouse (columnar) |
| UI | HTMX + minimal JS |
| Auth | Optional JWT |
| Deployment | Single binary + Docker |

The architecture prioritizes simplicity and performance: single Go process, embedded UI, ClickHouse for storage. No external dependencies beyond ClickHouse itself.

Start with Phase 1 (core ingest/query) then iterate based on usage patterns.