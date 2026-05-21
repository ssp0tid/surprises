# Trafix - Implementation Plan

## Project Overview

**Trafix** is a local HTTP API gateway and traffic inspector/proxy that sits between client applications and target APIs. It provides middleware-based request transformation, persistent request/response history in SQLite, a web dashboard for real-time traffic inspection, and built-in analytics.

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌────────────┐
│ Client  │────▶│ Trafix  │────▶│ Target  │────▶│ External   │
│ App     │     │ Gateway │     │ API     │     │ Service    │
└─────────┘     └─────────┘     └─────────┘     └────────────┘
                       │                                   
                       ▼                                   
                ┌────────────┐                             
                │ SQLite DB  │                             
                │ (History)  │                             
                └────────────┘                             
                       │                                   
                       ▼                                   
                ┌────────────┐                             
                │ Dashboard  │                             
                │ (Web UI)   │                             
                └────────────┘
```

---

## 1. File Structure

```
trafix/
├── src/
│   ├── main.go                 # Application entry point
│   ├── config/
│   │   └── config.go           # Configuration loading
│   ├── gateway/
│   │   ├── proxy.go           # Core HTTP proxy logic
│   │   ├── transport.go       # Custom transport for proxy
│   │   └── router.go           # Route handling
│   ├── middleware/
│   │   ├── middleware.go     # Middleware interface/chain
│   │   ├── ratelimit.go       # Rate limiting
│   │   ├── auth.go            # Authentication
│   │   ├── logging.go         # Request/response logging
│   │   └── cors.go            # CORS handling
│   ├── storage/
│   │   ├── db.go              # SQLite connection
│   │   ├── migrations.go      # Database migrations
│   │   └── request_repo.go    # Request/response CRUD
│   ├── analytics/
│   │   ├── analytics.go       # Analytics computation
│   │   └── metrics.go          # Metric models
│   ├── dashboard/
│   │   ├── server.go          # Dashboard HTTP server
│   │   ├── handlers.go       # Dashboard API handlers
│   │   ├── html/
│   │   │   └── index.html    # Dashboard UI (single page)
│   │   ├── static/
│   │   │   ├── style.css     # Dashboard styles
│   │   │   └── script.js     # Dashboard scripts
│   │   └── templates/
│   │       └── response.go   # Template rendering
│   └── utils/
│       ├── logger.go         # Structured logger
│       └── errors.go          # Error types
├── config.yaml               # Configuration file
├── migrations/
│   └── 001_initial.sql      # Database schema
├── go.mod                   # Go module
├── go.sum                   # Dependencies
├── Makefile                 # Build scripts
└── README.md               # Documentation
```

---

## 2. Dependencies

### Core

- **Go 1.21+** - Runtime
- **github.com/go-chi/chi/v5** - HTTP routing (lightweight, middleware-focused)
- **github.com/mattn/go-sqlite3** - SQLite driver
- **github.com/jmoiron/sqlx** - SQLite utilities

### Middleware & Authentication

- **github.com/go-chi/cors** - CORS middleware
- **golang.org/x/time/rate** - Rate limiting

### Configuration

- **github.com/spf13/viper** - Configuration loading (YAML/env vars)

### Dashboard

- **github.com/tdewolff/minify/v2** - HTML/JS/CSS minification
- **github.com/go-sqlite/sqlite3** - (bundled)

### Utilities

- **github.com/rs/zerolog** - Structured logging
- **github.com/google/uuid** - UUID generation

### Testing

- **github.com//stretchr/testify** - Test assertions
- **github.com/presonal/goftpd** - Testing proxy (if needed)

---

## 3. Configuration Design

### config.yaml Structure

```yaml
server:
  host: "127.0.0.1"
  port: 8080

dashboard:
  host: "127.0.0.1"
  port: 8081
  username: "admin"
  password: "changeme"  # Will be hashed at runtime

proxy:
  host: "127.0.0.1"
  port: 8082
  target_base_url: "http://localhost:3000"  # Default target
  timeout: 30s

storage:
  database: "./trafix.db"
  max_connections: 10

middleware:
  rate_limit:
    enabled: true
    requests_per_second: 100
    burst: 20
  auth:
    enabled: false
    api_keys:
      - "sk-test-12345"
      - "sk-prod-67890"
  logging:
    enabled: true
    log_requests: true
    log_responses: true
    max_body_size: 10240  # 10KB max logged body
  cors:
    enabled: false
    allowed_origins:
      - "http://localhost:3000"
    allowed_methods:
      - "GET"
      - "POST"
      - "PUT"
      - "DELETE"
    allowed_headers:
      - "Content-Type"
      - "Authorization"

analytics:
  window_size: 3600  # 1 hour in seconds
  retention_days: 30
```

### Environment Variable Overrides

```bash
TRAFIX_SERVER_HOST
TRAFIX_SERVER_PORT
TRAFIX_DASHBOARD_PORT
TRAFIX_DASHBOARD_PASSWORD  # Set password via env
TRAFIX_PROXY_TARGET_BASE_URL
```

---

## 4. Core Proxy Architecture

### HTTP Proxy Flow

```
Client Request
     │
     ▼
┌────────────────┐
│ Proxy Server   │  1. Receive request
└───────────────┘
     │
     ▼
┌────────────────┐
│ Middleware Chain│  2. Apply middleware (auth, rate limit, logging)
│ [logging]      │
│ [cors]         │  - Modify request
│ [auth]         │  - Reject early
│ [ratelimit]    │
└───────────────┘
     │
     ▼
┌────────────────┐
│ Target Request │  3. Transform and forward
│ Processing     │  - Set headers
│                │  - Resolve target URL
└───────────────┘
     │
     ▼
┌────────────────┐
│ Reverse Proxy  │  4. Forward to target
│ Transport      │
└───────────────┘
     │
     ▼
┌────────────────┐
│ Target Response │  5. Receive response
└───────────────┘
     │
     ▼
┌────────────────┐
│ Response       │  6. Apply response middleware
│ Middleware     │  - Log response
└───────────────┘
     │
     ▼
┌────────────────┐
│ SQLite Storage │  7. Persist request/response
└───────────────┘
     │
     ▼
Client Response
```

### Proxy Server Implementation

```go
// src/gateway/proxy.go

type Proxy struct {
    config      *Config
    middleware  MiddlewareChain
    transport   *http.Transport
    db          *storage.DB
}

func NewProxy(cfg *Config, db *storage.DB) *Proxy {
    p := &Proxy{
        config:    cfg,
        middleware: NewMiddlewareChain(cfg),
        transport: &http.Transport{
            TLSClientConfig: &tls.Config{InsecureSkipVerify: false},
        },
        db: db,
    }
    return p
}

func (p *Proxy) ServeHTTP(w http.ResponseWriter, r *http.Request) {
    ctx := NewContext(w, r)
    
    // Apply request middleware chain
    if err := p.middleware.ProcessRequest(ctx); err != nil {
        p.handleError(w, err)
        return
    }
    
    // Resolve target URL
    targetURL := p.resolveTarget(ctx)
    
    // Create proxied request
    proxyReq := p.createProxyRequest(ctx, targetURL)
    
    // Forward request
    resp, err := p.transport.RoundTrip(proxyReq)
    if err != nil {
        p.handleError(w, err)
        return
    }
    defer resp.Body.Close()
    
    // Apply response middleware
    ctx.SetResponse(resp)
    if err := p.middleware.ProcessResponse(ctx); err != nil {
        p.handleError(w, err)
        return
    }
    
    // Persist to database
    p.db.SaveRequest(ctx.RequestRecord)
    
    // Write response
    p.writeResponse(w, resp)
}

func (p *Proxy) resolveTarget(ctx *Context) string {
    // Support path-based routing
    // Default: prepend target_base_url
    path := ctx.Request.URL.Path
    base := p.config.Proxy.TargetBaseURL
    return base + path
}
```

---

## 5. Middleware Architecture

### Middleware Interface

```go
// src/middleware/middleware.go

type Middleware interface {
    Name() string
    Process(ctx *Context) error
    ProcessResponse(ctx *Context) error
}

type MiddlewareChain struct {
    middlewares []Middleware
    config      *MiddlewareConfig
}

func NewMiddlewareChain(cfg *Config) *MiddlewareChain {
    mc := &MiddlewareChain{
        middlewares: make([]Middleware, 0),
        config:     &cfg.Middleware,
    }
    
    if mc.config.Logging.Enabled {
        mc.middlewares = append(mc.middlewares, NewLogging())
    }
    if mc.config.CORS.Enabled {
        mc.middlewares = append(mc.middlewares, NewCORS(mc.config.CORS))
    }
    if mc.config.Auth.Enabled {
        mc.middlewares = append(mc.middlewares, NewAuth(mc.config.Auth))
    }
    if mc.config.RateLimit.Enabled {
        mc.middlewares = append(mc.middlewares, NewRateLimit(mc.config.RateLimit))
    }
    
    return mc
}

func (mc *MiddlewareChain) ProcessRequest(ctx *Context) error {
    for _, m := range mc.middlewares {
        if err := m.Process(ctx); err != nil {
            return err
        }
    }
    return nil
}

func (mc *MiddlewareChain) ProcessResponse(ctx *Context) error {
    for i := len(mc.middlewares) - 1; i >= 0; i-- {
        if err := mc.middlewares[i].ProcessResponse(ctx); err != nil {
            return err
        }
    }
    return nil
}
```

### Rate Limiting Middleware

```go
// src/middleware/ratelimit.go

type RateLimitConfig struct {
    Enabled            bool    `mapstructure:"enabled"`
    RequestsPerSecond float64 `mapstructure:"requests_per_second"`
    Burst             int     `mapstructure:"burst"`
}

type RateLimiter struct {
    config  *RateLimitConfig
    limiters map[string]*rate.Limiter
    mu      sync.RWMutex
}

func (rl *RateLimiter) Process(ctx *Context) error {
    key := rl.getClientKey(ctx)
    
    rl.mu.RLock()
    limiter, exists := rl.limiters[key]
    rl.mu.RUnlock()
    
    if !exists {
        limiter = rate.NewLimiter(
            rate.Limit(rl.config.RequestsPerSecond),
            rl.config.Burst,
        )
        
        rl.mu.Lock()
        rl.limiters[key] = limiter
        rl.mu.Unlock()
    }
    
    if !limiter.Allow() {
        return ErrRateLimited{
            RetryAfter: time.Second,
            Message:   "rate limit exceeded",
        }
    }
    
    return nil
}

func (rl *RateLimiter) getClientKey(ctx *Context) string {
    // Key by API key if authenticated, else by IP
    if apiKey := ctx.GetHeader("Authorization"); apiKey != "" {
        return hash(apiKey)
    }
    return ctx.ClientIP()
}
```

### Authentication Middleware

```go
// src/middleware/auth.go

type AuthConfig struct {
    Enabled  bool     `mapstructure:"enabled"`
    APIKeys  []string `mapstructure:"api_keys"`
}

type Auth struct {
    config *AuthConfig
}

func (a *Auth) Process(ctx *Context) error {
    authHeader := ctx.GetHeader("Authorization")
    if authHeader == "" {
        return ErrUnauthorized{
            Message: "missing authorization header",
        }
    }
    
    // Support "Bearer <token>" format
    token := strings.TrimPrefix(authHeader, "Bearer ")
    
    // Check against configured API keys
    for _, key := range a.config.APIKeys {
        if subtle.ConstantTimeCompare([]byte(token), []byte(key)) == 1 {
            ctx.SetAuthenticated(true)
            return nil
        }
    }
    
    return ErrUnauthorized{
        Message: "invalid API key",
    }
}
```

### Logging Middleware

```go
// src/middleware/logging.go

type Logger struct{}

func (l *Logger) Process(ctx *Context) error {
    start := time.Now()
    ctx.SetValue("start_time", start)
    
    log.Info().
        Str("method", ctx.Request.Method).
        Str("path", ctx.Request.URL.Path).
        Str("client_ip", ctx.ClientIP()).
        Str("user_agent", ctx.GetHeader("User-Agent")).
        Msg("request received")
    
    return nil
}

func (l *Logger) ProcessResponse(ctx *Context) error {
    start := ctx.GetValue("start_time").(time.Time)
    duration := time.Since(start)
    
    statusCode := ctx.Response.StatusCode
    
    log.Info().
        Str("method", ctx.Request.Method).
        Str("path", ctx.Request.URL.Path).
        Int("status_code", statusCode).
        Dur("duration", duration).
        Msg("request completed")
    
    return nil
}
```

---

## 6. Database Schema

### Schema Design

```sql
-- migrations/001_initial.sql

-- Requests table
CREATE TABLE IF NOT EXISTS requests (
    id TEXT PRIMARY KEY,
    method TEXT NOT NULL,
    path TEXT NOT NULL,
    query TEXT,
    
    -- Request headers (JSON)
    request_headers TEXT,
    
    -- Request body (if present)
    request_body BLOB,
    request_body_size INTEGER,
    
    -- Response
    status_code INTEGER,
    response_headers TEXT,
    response_body BLOB,
    response_body_size INTEGER,
    
    -- Timing
    duration_ms INTEGER,
    
    -- Client info
    client_ip TEXT,
    user_agent TEXT,
    
    -- Auth
    api_key_hash TEXT,
    authenticated INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TEXT NOT NULL,
    indexed_at TEXT
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_requests_created_at ON requests(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_requests_path ON requests(path);
CREATE INDEX IF NOT EXISTS idx_requests_status_code ON requests(status_code);
CREATE INDEX IF NOT EXISTS idx_requests_client_ip ON requests(client_ip);

-- Full-text search on path
CREATE VIRTUAL TABLE IF NOT EXISTS requests_fts USING fts5(
    path,
    content='requests',
    content_rowid='rowid'
);

-- Analytics aggregations (materialized)
CREATE TABLE IF NOT EXISTS analytics_hourly (
    hour TEXT NOT NULL,  -- ISO hour: "2026-04-22T15:00"
    path TEXT NOT NULL,
    
    request_count INTEGER DEFAULT 0,
    authenticated_count INTEGER DEFAULT 0,
    
    status_2xx INTEGER DEFAULT 0,
    status_3xx INTEGER DEFAULT 0,
    status_4xx INTEGER DEFAULT 0,
    status_5xx INTEGER DEFAULT 0,
    
    avg_duration_ms REAL DEFAULT 0,
    min_duration_ms INTEGER,
    max_duration_ms INTEGER,
    
    PRIMARY KEY (hour, path)
);

CREATE TABLE IF NOT EXISTS analytics_daily (
    date TEXT NOT NULL,  -- ISO date: "2026-04-22"
    path TEXT NOT NULL,
    
    request_count INTEGER DEFAULT 0,
    authenticated_count INTEGER DEFAULT 0,
    
    status_2xx INTEGER DEFAULT 0,
    status_3xx INTEGER DEFAULT 0,
    status_4xx INTEGER DEFAULT 0,
    status_5xx INTEGER DEFAULT 0,
    
    avg_duration_ms REAL DEFAULT 0,
    min_duration_ms INTEGER,
    max_duration_ms INTEGER,
    
    unique_ips INTEGER DEFAULT 0,
    unique_api_keys INTEGER DEFAULT 0,
    
    PRIMARY KEY (date, path)
);
```

### Request Record Model

```go
// src/storage/request_repo.go

type RequestRecord struct {
    ID              string    `db:"id"`
    Method          string    `db:"method"`
    Path            string    `db:"path"`
    Query           string    `db:"query"`
    
    RequestHeaders  string    `db:"request_headers"`  // JSON
    RequestBody    []byte    `db:"request_body"`
    RequestBodySize int       `db:"request_body_size"`
    
    StatusCode      int       `db:"status_code"`
    ResponseHeaders string   `db:"response_headers"`  // JSON
    ResponseBody   []byte   `db:"response_body"`
    ResponseBodySize int     `db:"response_body_size"`
    
    DurationMs     int       `db:"duration_ms"`
    
    ClientIP       string    `db:"client_ip"`
    UserAgent     string    `db:"user_agent"`
    
    APIKeyHash     string    `db:"api_key_hash"`
    Authenticated bool      `db:"authenticated"`
    
    CreatedAt     time.Time `db:"created_at"`
    IndexedAt    *time.Time `db:"indexed_at"`
}

func (db *DB) SaveRequest(r *RequestRecord) error {
    r.ID = uuid.New().String()
    r.CreatedAt = time.Now().UTC()
    
    // Truncate body if too large
    maxBodySize := db.config.MaxBodySize
    if r.RequestBodySize > maxBodySize {
        r.RequestBody = r.RequestBody[:maxBodySize]
        r.RequestBodySize = maxBodySize
    }
    if r.ResponseBodySize > maxBodySize {
        r.ResponseBody = r.ResponseBody[:maxBodySize]
        r.ResponseBodySize = maxBodySize
    }
    
    query := `
        INSERT INTO requests (
            id, method, path, query,
            request_headers, request_body, request_body_size,
            status_code, response_headers, response_body, response_body_size,
            duration_ms, client_ip, user_agent,
            api_key_hash, authenticated, created_at
        ) VALUES (
            :id, :method, :path, :query,
            :request_headers, :request_body, :request_body_size,
            :status_code, :response_headers, :response_body, :response_body_size,
            :duration_ms, :client_ip, :user_agent,
            :api_key_hash, :authenticated, :created_at
        )`
    
    _, err := db.NamedExec(query, r)
    return err
}

func (db *DB) GetRequests(filter RequestFilter) ([]RequestRecord, error) {
    // Filter by date range, path, status, etc.
    // Pagination with limit/offset
}
```

---

## 7. Dashboard API

### Dashboard Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | / | Dashboard UI |
| GET | /api/requests | List requests |
| GET | /api/requests/:id | Get request detail |
| GET | /api/analytics | Get analytics data |
| GET | /api/health | Health check |
| GET | /api/config | Get config (masked) |

### API Response Format

```json
// GET /api/requests?limit=50&offset=0

{
  "data": [
    {
      "id": "req_abc123",
      "method": "GET",
      "path": "/api/users/123",
      "status_code": 200,
      "duration_ms": 45,
      "client_ip": "192.168.1.1",
      "created_at": "2026-04-22T10:30:00Z"
    }
  ],
  "pagination": {
    "limit": 50,
    "offset": 0,
    "total": 1000
  }
}
```

```json
// GET /api/analytics?window=1h

{
  "total_requests": 5000,
  "requests_per_second": 1.4,
  "by_status": {
    "2xx": 4500,
    "3xx": 200,
    "4xx": 250,
    "5xx": 50
  },
  "by_path": [
    {"path": "/api/users", "count": 2000},
    {"path": "/api/products", "count": 1500},
    {"path": "/api/orders", "count": 1000}
  ],
  "response_time": {
    "p50": 25,
    "p90": 100,
    "p95": 200,
    "p99": 500
  },
  "top_ips": [
    {"ip": "192.168.1.1", "count": 500}
  ]
}
```

### Dashboard UI

Single-page application with:

- **Request List View** - Table with sortable columns, pagination
- **Request Detail View** - Request/response body, headers, timing
- **Analytics View** - Charts for:
  - Requests over time (line chart)
  - Status code distribution (pie chart)
  - Response time percentiles (line chart)
  - Top paths (bar chart)
- **Live Stream** - WebSocket or polling for real-time requests

```html
<!-- Dashboard sections -->
<div id="dashboard">
  <nav class="sidebar">
    <a href="/">Requests</a>
    <a href="/analytics">Analytics</a>
    <a href="/settings">Settings</a>
  </nav>
  
  <main>
    <header>
      <input type="search" placeholder="Search requests...">
      <select name="filter">
        <option value="">All</option>
        <option value="2xx">Success</option>
        <option value="4xx">Client Error</option>
        <option value="5xx">Server Error</option>
      </select>
    </header>
    
    <table>
      <thead>
        <th>Time</th>
        <th>Method</th>
        <th>Path</th>
        <th>Status</th>
        <th>Duration</th>
      </thead>
      <tbody id="requests_list">
      </tbody>
    </table>
  </main>
</div>
```

---

## 8. Analytics Computation

### Real-time Analytics

```go
// src/analytics/analytics.go

type AnalyticsService struct {
    db *storage.DB
}

func (as *AnalyticsService) ComputeHourly(hour time.Time) error {
    query := `
        INSERT INTO analytics_hourly (hour, path, request_count, ...)
        SELECT 
            strftime('%Y-%m-%dT%H:00', created_at) as hour,
            path,
            COUNT(*) as request_count,
            SUM(CASE WHEN status_code >= 200 AND status_code < 300 THEN 1 ELSE 0 END) as status_2xx,
            AVG(duration_ms) as avg_duration_ms,
            MIN(duration_ms) as min_duration_ms,
            MAX(duration_ms) as max_duration_ms
        FROM requests
        WHERE created_at >= ? AND created_at < ?
        GROUP BY hour, path
        ON CONFLICT(hour, path) DO UPDATE SET
            request_count = excluded.request_count, ...`
    
    _, err := as.db.Exec(query, hourStart, hourEnd)
    return err
}

func (as *AnalyticsService) GetAnalytics(window AnalyticsWindow) (*Analytics, error) {
    switch window {
    case Window1Hour:
        return as.getAnalyticsRange(time.Now().Add(-1*time.Hour), time.Now())
    case Window24Hours:
        return as.getAnalyticsRange(time.Now().Add(-24*time.Hour), time.Now())
    case Window7Days:
        // Use pre-aggregated daily table
        return as.getDailyAnalytics()
    }
}

// Response time percentiles using inline calculation
func (as *AnalyticsService) getPercentiles(durations []int, p50, p90, p95, p99 *float64) {
    sort.Ints(durations)
    n := len(durations)
    *p50 = float64(durations[n/2])
    *p90 = float64(int(float64(n)*0.9))
    *p95 = float64(int(float64(n)*0.95))
    *p99 = float64(int(float64(n)*0.99))
}
```

---

## 9. Error Handling

### Error Types

```go
// src/utils/errors.go

type TrafixError interface {
    error
    StatusCode() int
    Code() string
}

type BaseError struct {
    code        string
    message     string
    statusCode int
    err        error
}

func (e *BaseError) Error() string {
    return e.message
}

func (e *BaseError) StatusCode() int {
    return e.statusCode
}

func (e *BaseError) Unwrap() error {
    return e.err
}

var (
    ErrNotFound = &BaseError{
        code:        "NOT_FOUND",
        message:     "resource not found",
        statusCode: 404,
    }
    
    ErrUnauthorized = &BaseError{
        code:        "UNAUTHORIZED",
        message:     "unauthorized",
        statusCode: 401,
    }
    
    ErrForbidden = &BaseError{
        code:        "FORBIDDEN",
        message:     "forbidden",
        statusCode: 403,
    }
    
    ErrRateLimited = &BaseError{
        code:        "RATE_LIMITED",
        message:     "rate limit exceeded",
        statusCode: 429,
    }
    
    ErrBadRequest = &BaseError{
        code:        "BAD_REQUEST",
        message:     "bad request",
        statusCode: 400,
    }
    
    ErrInternalServer = &BaseError{
        code:        "INTERNAL_SERVER_ERROR",
        message:     "internal server error",
        statusCode: 500,
    }
    
    ErrBadGateway = &BaseError{
        code:        "BAD_GATEWAY",
        message:     "upstream error",
        statusCode: 502,
    }
)
```

### Error Handler Middleware

```go
func ErrorHandler(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        defer func() {
            if rec := recover(); rec != nil {
                log.Error().Any("panic", rec).Msg("panic recovered")
                WriteJSONError(w, ErrInternalServer)
            }
        }()
        
        next.ServeHTTP(w, r)
    })
}

func WriteJSONError(w http.ResponseWriter, err TrafixError) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(err.StatusCode())
    
    json.NewEncoder(w).Encode(map[string]interface{}{
        "error": map[string]string{
            "code":    err.Code(),
            "message": err.Error(),
        },
    })
}
```

---

## 10. Edge Cases

### Connection & Timeout Handling

1. **Target server unreachable** - Return 502 Bad Gateway with error message
2. **Target timeout** - Configurable timeout (default 30s), return 504 Gateway Timeout
3. **Connection reuse** - Use HTTP/1.1 keep-alive pooling
4. **TLS verification** - Default on, configurable per-target

### Body Handling

1. **Large request body** - Stream request, limit to 10MB
2. **Large response body** - Stream response, limit to 50MB
3. **Binary body** - Store as-is in SQLite (bytes)
4. **Gzip response** - Decompress before storage, don't re-compress

### Request Transformation

1. **Path routing** - Support `/api/v1/*` → `/v1/*`
2. **Host header** - Set to target host
3. **X-Forwarded headers** - Set by proxy
4. **WebSocket upgrade** - Pass through

### Database

1. **Write failure** - Log error, continue (non-blocking)
2. **Database locked** - Retry with exponential backoff
3. **Large database** - Auto-vacuum daily, TTL 30 days
4. **Migration failure** - Fail fast, require manual干预

### Security

1. **API key in logs** - Never log full API keys
2. **Sensitive headers** - Filter Authorization, Cookie
3. **Password in config** - Require env var, never store plain
4. **Dashboard auth** - HTTP Basic, change default password

### Rate Limiting

1. **Per-IP default** - 100 req/s, burst 20
2. **Per-API key** - Higher limits configurable
3. **Redis-like behavior** - Token bucket
4. **By path** - Different limits per path (future)

---

## 11. Implementation Phases

### Phase 1: Core Proxy (Week 1)

- [ ] Setup project structure
- [ ] Configuration loading
- [ ] Basic HTTP proxy
- [ ] Route handling
- [ ] Error types

### Phase 2: Middleware (Week 1-2)

- [ ] Middleware chain
- [ ] Logging middleware
- [ ] Rate limiting
- [ ] Authentication
- [ ] CORS

### Phase 3: Storage (Week 2)

- [ ] SQLite setup
- [ ] Database schema
- [ ] Request repository
- [ ] Basic queries

### Phase 4: Dashboard (Week 3)

- [ ] Dashboard API
- [ ] List requests
- [ ] Request detail
- [ ] Frontend UI

### Phase 5: Analytics (Week 3-4)

- [ ] Analytics computation
- [ ] Pre-aggregated tables
- [ ] Charts and graphs

### Phase 6: Polish (Week 4)

- [ ] Testing
- [ ] Documentation
- [ ] Performance tuning

---

## 12. Success Criteria

- [ ] Proxy can forward HTTP requests through gateway
- [ ] Rate limiting applies correctly
- [ ] Authentication validates API keys
- [ ] All requests/responses stored in SQLite
- [ ] Dashboard shows request history
- [ ] Analytics show request counts, response times, status codes
- [ ] Error handling returns appropriate codes
- [ ] Edge cases handled gracefully

---

## 13. Open Questions

1. **Path-based routing** - Support regex or prefix matching?
2. **WebSocket proxying** - Full support or pass-through?
3. **Metrics export** - Prometheus endpoint needed?
4. **API versioning** - Support multiple API versions?
5. **Plugin middleware** - Support custom middleware?
6. **TLS termination** - Handle HTTPS at proxy?

---

*Plan created: 2026-04-22*
*Version: 1.0*