# Local Service Mesh Proxy - Implementation Plan

**Version**: 1.0  
**Date**: April 2026  
**Status**: Design Document

---

## 1. Overview

### 1.1 Purpose

The Local Service Mesh Proxy (LSMP) is a developer tool that sits between local microservices, providing traffic control and manipulation capabilities for local development, testing, and debugging workflows.

### 1.2 Core Features

| Feature | Description |
|---------|-------------|
| Traffic Routing | Route requests to different backend services based on rules |
| Mock Responses | Return predefined responses without hitting backend |
| Delay Injection | Simulate latency and network instability |
| Circuit Breaking | Prevent cascading failures from failing backends |
| Rate Limiting | Control request throughput per client/service |
| Traffic Mirroring | Duplicate requests to shadow services for testing |

### 1.3 Target Users

- Backend developers working with microservices locally
- QA engineers testing failure scenarios
- DevOps validating deployment configurations
- Teams practicing service mesh patterns in development

---

## 2. Architecture

### 2.1 High-Level Design

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│   Client   │────▶│  LSMP       │────▶│  Backend(s)   │
│  Service   │     │  Proxy      │     │  / Mock / Null │
└─────────────┘     │              │     └────────────────┘
                    │  ┌─────────┐ │
                    │  │ Router  │ │
                    │  ├─────────┤ │
                    │  │ Circuit │─┼──▶ Traffic Mirroring
                    │  │ Breaker │ │
                    │  ├─────────┤ │
                    │  │ Rate    │ │
                    │  │ Limiter │ │
                    │  ├─────────┤ │
                    │  │ Delay   │ │
                    │  │ Injector│ │
                    │  ├─────────┤ │
                    │  │ Mock    │ │
                    │  │ Handler │ │
                    │  └─────────┘ │
                    └──────────────┘
```

### 2.2 Request Flow

```
Client Request
     │
     ▼
┌────────────┐
│ Rate Limit │──── DENY ────▶ 429 Too Many Requests
│  Checker   │
└─────┬──────┘
      │ ALLOW
      ▼
┌────────────┐
│   Delay    │──── WAIT ────▶ (injected delay)
│ Injector  │
└─────┬──────┘
      │
      ▼
┌────────────┐
│   Route    │
│  Resolver  │─────────────────────────┐
└─────┬──────┘                         │
      │ ROUTE MATCH                   │ NO MATCH
      ▼                             ▼
┌────────────┐              ┌────────────┐
│   Mock     │              │  Backend   │
│  Handler  │              │  Service   │
└─────┬──────┘              └─────┬──────┘
      │ MOCK RESPONSE               │ ACTUAL REQUEST
      ▼                            ▼
      │                     ┌──────┴─────┐
      │                     │  Circuit   │
      │                     │  Breaker   │
      │                     └──────┬─────┘
      │                            │ ALLOW
      ▼                            ▼
      │                     ┌──────────────┐
      │─────────DENY────────│   Backend    │
      │      (open)        │   Response  │
      ▼                    └──────────────┘
      │
      ▼ (async, fire-and-forget)
┌────────────┐
│  Mirror   │
│  Handler  │
└───────────┘
```

### 2.3 Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| **Router** | Match incoming requests to route rules; determine target backend |
| **Rate Limiter** | Track and enforce request limits per key (client IP, service name, etc.) |
| **Delay Injector** | Apply artificial delays and jitter before forwarding |
| **Mock Handler** | Return configured responses without contacting backend |
| **Circuit Breaker** | Track backend health; fail fast when threshold exceeded |
| **Mirror Handler** | Duplicate requests to shadow service asynchronously |

---

## 3. File Structure

```
mesh-proxy/
├── .github/
│   └── workflows/
│       └── ci.yaml
├── cmd/
│   └── mesh-proxy/
│       └── main.go                 # Entry point
├── internal/
│   ├── config/
│   │   ├── config.go               # Configuration loading
│   │   └── loader.go              # YAML/JSON file parsing
│   ├── proxy/
│   │   ├── proxy.go               # Main HTTP proxy server
│   │   └── handler.go             # HTTP request handler
│   ├── router/
│   │   ├── router.go             # Route matching engine
│   │   └── rule.go               # Route rule definition
│   ├── circuit/
│   │   ├── circuit.go            # Circuit breaker state machine
│   │   └── metrics.go            # Success/failure tracking
│   ├── ratelimit/
│   │   ├── limiter.go             # Rate limiting logic
│   │   └── tokenbucket.go        # Token bucket implementation
│   ├── delay/
│   │   └── injector.go           # Delay injection logic
│   ├── mock/
│   │   └── handler.go           # Mock response handler
│   └── mirror/
│       └── handler.go          # Traffic mirroring handler
├── pkg/
│   └── types/
│       └── types.go             # Shared type definitions
├── configs/
│   └── default.yaml             # Default configuration example
├── go.mod
├── go.sum
├── Makefile
├── README.md
└── PLAN.md                       # This document
```

### 3.1 Module Responsibilities

| Module | Purpose |
|--------|---------|
| `cmd/` | Application entry point and CLI arguments |
| `internal/config` | Configuration loading from files, env vars |
| `internal/proxy` | Core HTTP proxy server and request handling |
| `internal/router` | Request routing based on path, method, headers |
| `internal/circuit` | Circuit breaker state management |
| `internal/ratelimit` | Token bucket rate limiting |
| `internal/delay` | Latency injection |
| `internal/mock` | Mock response generation |
| `internal/mirror` | Traffic duplication to shadow services |
| `pkg/types` | Shared type definitions for internal packages |

---

## 4. Dependencies

### 4.1 Required Dependencies

```go
// Core proxy infrastructure
github.com/vulcand/oxy/v2        // Reverse proxy, load balancing, circuit breaker
github.com/elazarl/goproxy        // HTTP CONNECT for HTTPS interception (optional)

// Resilience patterns
github.com/sony/gobreaker/v2       // Circuit breaker implementation

// HTTP and networking
github.com/gorilla/mux           // HTTP routing (path matching)
github.com/gorilla/websocket      // WebSocket support

// Configuration
gopkg.in/yaml.v3                  // YAML configuration parsing

// Logging and observability
github.com/rs/zerolog            // Structured logging

// Utilities
github.com/spf13/cobra            // CLI argument parsing
github.com/spf13/viper            // Config file and env var binding
```

### 4.2 Rationale

| Library | Purpose | Alternative Considered |
|---------|---------|-------------------|
| `vulcand/oxy/v2` | Foundation proxy with forward, buffer, circuitbreaker | Standard `httputil.ReverseProxy` - oxy provides better middleware |
| `sony/gobreaker` | Production-tested circuit breaker state machine | Custom impl - gobreaker is well-maintained (3.6k stars) |
| `gorilla/mux` | Route matching with path variables, regex | `chi` - gorilla is more familiar |
| `rs/zerolog` | Low-allocation structured logging | `zap` - zerolog has simpler API |
| `yaml.v3` | YAML config parsing | Built-in - standard library lacks YAML |

### 4.3 Minimal Core Dependencies

If minimal footprint is required:

```go
require (
    golang.org/x/time/rate        // Token bucket (standard library)
    gopkg.in/yaml.v3              // Configuration
    github.com/rs/zerolog        // Logging
    github.com/spf13/viper       // Config
)
```

---

## 5. API Design

### 5.1 HTTP API

The proxy exposes admin endpoints for dynamic configuration.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/config` | Get current configuration |
| `POST` | `/config/reload` | Reload configuration from file |
| `GET` | `/routes` | List active routes |
| `GET` | `/routes/{name}` | Get route details |
| `POST` | `/routes/{name}/enable` | Enable a route |
| `POST` | `/routes/{name}/disable` | Disable a route |
| `GET` | `/circuit/states` | Get circuit breaker states |
| `POST` | `/circuit/{name}/reset` | Reset a circuit breaker |
| `GET` | `/stats` | Statistics and metrics |

### 5.2 Admin API Response Format

```json
{
  "status": "ok",
  "data": {
    "routes": [
      {
        "name": "api-v1",
        "pattern": "/api/v1/*",
        "backend": "http://localhost:8080",
        "enabled": true,
        "circuit_breaker": "enabled"
      }
    ],
    "circuit_breakers": [
      {
        "name": "backend-8080",
        "state": "closed",
        "failure_count": 0,
        "success_count": 42
      }
    ],
    "stats": {
      "requests_total": 1000,
      "requests_allowed": 950,
      "requests_denied": 50,
      "latency_p50_ms": 12,
      "latency_p99_ms": 45
    }
  }
}
```

### 5.3 Error Response Format

```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Request rate exceeded",
    "details": {
      "limit": 100,
      "window": "1s",
      "retry_after_ms": 850
    }
  }
}
```

### 5.4 Error Codes

| Code | HTTP Status | Description |
|------|------------|-------------|
| `RATE_LIMITED` | 429 | Rate limit exceeded |
| `CIRCUIT_OPEN` | 503 | Circuit breaker open |
| `TIMEOUT` | 504 | Request timeout |
| `INVALID_ROUTE` | 404 | No matching route |
| `BACKEND_ERROR` | 502 | Backend returned error |
| `CONFIG_ERROR` | 500 | Configuration error |

---

## 6. YAML Configuration Schema

### 6.1 Full Configuration Example

```yaml
# mesh-proxy configuration
version: "1.0"

# Server configuration
server:
  host: "0.0.0.0"
  port: 8080
  read_timeout: 30s
  write_timeout: 30s
  idle_timeout: 120s

# Admin server configuration
admin:
  host: "127.0.0.1"
  port: 9090
  enabled: true

# Default backend (fallback)
defaults:
  timeout: 10s
  retry_attempts: 0

# Circuit breaker defaults
circuit_breaker:
  max_requests: 100
  interval: 10s
  timeout: 60s
  ready_to_trip:
    failure_rate_threshold: 0.5
    minimum_requests: 5

# Rate limiting defaults
rate_limit:
  requests_per_second: 100
  burst: 20

# Logging configuration
logging:
  level: "info"
  format: "json"

# Route definitions
routes:
  - name: "api-service"
    enabled: true
    priority: 100
    
    # Route matching
    match:
      path: "/api/v1/*"
      # OR: path_prefix: "/api/"
      # OR: method: ["GET", "POST"]
      # OR: header:
      #   X-Service: "api"
    
    # Backend configuration
    backend:
      url: "http://localhost:8080"
      # Multiple backends for load balancing (optional)
      # urls:
      #   - "http://localhost:8080"
      #   - "http://localhost:8081"
    
    # Circuit breaker (optional)
    circuit_breaker:
      enabled: true
      failure_rate_threshold: 0.5
      timeout: 30s
      half_open_requests: 3
    
    # Rate limiting (optional)
    rate_limit:
      requests_per_second: 50
      burst: 10
      key: "header:X-Client-ID"  # Rate limit key source
    
    # Mock response (optional, overrides backend)
    mock:
      enabled: true
      status_code: 200
      headers:
        Content-Type: "application/json"
      body: '{"status": "ok", "version": "1.0"}'
      # OR: body_file: "./mocks/api-response.json
    
    # Delay injection (optional)
    delay:
      fixed: 500ms
      # OR:
      # min: 100ms
      # max: 1000ms
      # jitter: 50ms
    
    # Traffic mirroring (optional)
    mirror:
      enabled: true
      target: "http://localhost:8081"
      percentage: 100
      # OR: header for percentage: X-Mirror-Percentage
    
    # Timeout (optional, overrides default)
    timeout: 5s

  - name: "api-service-v2"
    enabled: true
    priority: 50
    match:
      path: "/api/v2/*"
    backend:
      url: "http://localhost:8082"

  - name: "health-check"
    enabled: true
    priority: 1
    match:
      path: "/health"
    mock:
      enabled: true
      status_code: 200
      body: '{"status": "ok"}'

  - name: "legacy-service"
    enabled: false
    match:
      path: "/legacy/*"
    backend:
      url: "http://localhost:9000"

# Error responses (custom error pages)
errors:
  404:
    status_code: 404
    body: "Not Found"
  429:
    status_code: 429
    headers:
      X-RateLimit-Reset: "{{retry_after}}"
    body: "Rate limit exceeded"
  500:
    status_code: 500
    body: "Internal Server Error"
  503:
    status_code: 503
    body: "Service Unavailable"
```

### 6.2 Configuration Schema (JSON Schema Reference)

```yaml
# Root Configuration
configuration:
  version:           string             # Config version (required)
  server:             ServerConfig       # HTTP server settings
  admin:              AdminConfig        # Admin API settings
  defaults:           DefaultsConfig    # Default settings
  circuit_breaker:    CBDefaults        # Default CB settings
  rate_limit:         RLDefaults        # Default rate limit
  logging:            LoggingConfig     # Logging settings
  routes:             []Route            # Route definitions
  errors:             ErrorsConfig       # Custom error pages

# Server Configuration
ServerConfig:
  host:               string             # Bind host
  port:               int                # Bind port
  read_timeout:       duration           # Read timeout
  write_timeout:      duration           # Write timeout
  idle_timeout:       duration           # Idle timeout

# Route Configuration
Route:
  name:               string             # Route name (required, unique)
  enabled:            bool               # Enable/disable route
  priority:           int               # Route priority (higher = first)
  match:              RouteMatch        # Matching rules
  backend:            BackendConfig      # Backend settings
  circuit_breaker:     CBConfig          # Circuit breaker (optional)
  rate_limit:         RLConfig          # Rate limit (optional)
  mock:               MockConfig        # Mock response (optional)
  delay:              DelayConfig      # Delay injection (optional)
  mirror:             MirrorConfig     # Traffic mirror (optional)
  timeout:             duration          # Request timeout

# Route Match
RouteMatch:
  path:               string           # Exact path match (* for wildcard)
  path_prefix:         string           # Path prefix match
  method:             []string        # HTTP methods
  header:             map[string]string # Header match

# Backend Configuration
BackendConfig:
  url:                 string          # Single backend URL
  urls:                []string         # Multiple backends (load balancing)
  # OR
  service:             string           # Service name (for service discovery)

# Circuit Breaker Configuration
CBConfig:
  enabled:              bool           # Enable CB
  failure_rate_threshold: float          # Failure rate to open (0.0-1.0)
  timeout:              duration       # Time in open state
  half_open_requests:   int            # Probes in half-open state
  min_requests:        int             # Minimum requests before evaluation

# Rate Limit Configuration
RLConfig:
  requests_per_second: float          # Requests per second
  burst:               int            # Burst allowance
  key:                 string          # Rate limit key (header:HeaderName, ip, etc)

# Mock Configuration
MockConfig:
  enabled:              bool           # Enable mock
  status_code:          int             # HTTP status code
  headers:             map[string]string # Response headers
  body:                string          # Response body
  body_file:            string          # File containing body

# Delay Configuration
DelayConfig:
  fixed:                duration       # Fixed delay
  min:                  duration       # Minimum delay
  max:                  duration       # Maximum delay
  jitter:               duration       # Random jitter (±)

# Mirror Configuration
MirrorConfig:
  enabled:              bool           # Enable mirroring
  target:               string          # Shadow service URL
  percentage:           float          # % of traffic to mirror (0.0-100.0)
  percentage_header:   string          # Header containing percentage

# Duration format
# Examples: 100ms, 1s, 30s, 1m, 2h
```

---

## 7. Core Implementation Details

### 7.1 Routing Engine

```go
// internal/router/router.go

type Router struct {
    rules    []Rule
    matcher *Matcher
}

type Rule struct {
    Name        string
    Priority    int
    Enabled     bool
    Match       RouteMatch
    Handler     http.Handler
    Middleware []Middleware
}

type RouteMatch struct {
    Path        string            // exact or /* wildcard
    PathPrefix  string            // prefix match
    Methods     []string          // HTTP methods
    Headers     map[string]string // header matching
}

// Match determines if a request matches a route rule
func (r *Rule) Match(req *http.Request) bool {
    // Path matching
    if r.Match.Path != "" {
        if !matchPath(r.Match.Path, req.URL.Path) {
            return false
        }
    }
    if r.Match.PathPrefix != "" {
        if !strings.HasPrefix(req.URL.Path, r.Match.PathPrefix) {
            return false
        }
    }
    
    // Method matching
    if len(r.Match.Methods) > 0 {
        found := false
        for _, m := range r.Match.Methods {
            if req.Method == m {
                found = true
                break
            }
        }
        if !found {
            return false
        }
    }
    
    // Header matching
    for k, v := range r.Match.Headers {
        if req.Header.Get(k) != v {
            return false
        }
    }
    
    return true
}

// matchPath handles wildcard matching
func matchPath(pattern, path string) bool {
    if strings.HasSuffix(pattern, "/*") {
        prefix := strings.TrimSuffix(pattern, "/*")
        return strings.HasPrefix(path, prefix)
    }
    return pattern == path
}
```

### 7.2 Circuit Breaker (using gobreaker)

```go
// internal/circuit/circuit.go

import (
    "errors"
    "github.com/sony/gobreaker/v2"
)

var (
    ErrCircuitOpen = errors.New("circuit breaker is open")
)

type CircuitBreaker struct {
    name    string
    cb      *gobreaker.CircuitBreaker
    service string
}

// New creates a new circuit breaker
func New(name, service string, opts ...Option) *CircuitBreaker {
    settings := gobreaker.Settings{
        Name:        name,
        MaxRequests: 3,           // max requests in half-open state
        Interval:   10 * 1e9,     // 10 seconds (in nanoseconds)
        Timeout:    60 * 1e9,     // 60 seconds (in nanoseconds)
        ReadyToTrip: func(c gobreaker.Counts) bool {
            failureRatio := float64(c.TotalFailures) / float64(c.Requests)
            return c.Requests >= 5 && failureRatio >= 0.5
        },
        IsSuccessful: func(err error) bool {
            if err == nil {
                return true
            }
            // Consider 5xx errors as failures
            return strings.Contains(err.Error(), "5")
        },
    }
    
    for _, opt := range opts {
        opt(&settings)
    }
    
    return &CircuitBreaker{
        name:    name,
        cb:      gobreaker.NewCircuitBreaker(settings),
        service: service,
    }
}

// Execute runs the function with circuit breaker protection
func (cb *CircuitBreaker) Execute(fn func() error) error {
    result, err := cb.cb.Execute(func() (interface{}, error) {
        return nil, fn()
    })
    if err != nil {
        return err
    }
    return result.(error)
}

// State returns the current state of the circuit breaker
func (cb *CircuitBreaker) State() gobreaker.State {
    return cb.cb.State()
}
```

### 7.3 Rate Limiter (using golang.org/x/time/rate)

```go
// internal/ratelimit/limiter.go

import (
    "errors"
    "golang.org/x/time/rate"
    "sync"
)

var (
    ErrRateLimited = errors.New("rate limit exceeded")
)

type Limiter struct {
    limiters map[string]*rate.Limiter
    mu      sync.RWMutex
    config   *Config
}

type Config struct {
    RPS    float64 // requests per second
    Burst  int    // burst allowance
}

// New creates a new rate limiter
func New(config *Config) *Limiter {
    return &Limiter{
        limiters: make(map[string]*rate.Limiter),
        config:  config,
    }
}

// getKey extracts the rate limit key from request
func (l *Limiter) getKey(r *http.Request) string {
    if l.config.KeyHeader != "" {
        return r.Header.Get(l.config.KeyHeader)
    }
    return r.RemoteAddr
}

// Allow checks if request is allowed and consumes a token if so
func (l *Limiter) Allow(r *http.Request) error {
    key := l.getKey(r)
    
    l.mu.RLock()
    limiter, exists := l.limiters[key]
    l.mu.RUnlock()
    
    if !exists {
        l.mu.Lock()
        // Double-check after acquiring write lock
        if l.limiters[key] == nil {
            l.limiters[key] = rate.NewLimiter(
                rate.Limit(l.config.RPS),
                l.config.Burst,
            )
        }
        limiter = l.limiters[key]
        l.mu.Unlock()
    }
    
    if !limiter.Allow() {
        return ErrRateLimited
    }
    return nil
}

// Wait blocks until a token is available (with context)
func (l *Limiter) Wait(r *http.Request, ctx context.Context) error {
    // ... similar implementation using limiter.Wait(ctx)
    return nil
}
```

### 7.4 Delay Injection

```go
// internal/delay/injector.go

import (
    "math/rand"
    "time"
)

type Config struct {
    Fixed  time.Duration
    Min    time.Duration
    Max    time.Duration
    Jitter time.Duration
}

type Injector struct {
    config *Config
    rand   *rand.Rand
    mu     sync.Mutex
}

func New(config *Config) *Injector {
    return &Injector{
        config: config,
        rand:   rand.New(rand.NewSource(time.Now().UnixNano())),
    }
}

// Delay returns the configured delay for a request
func (i *Injector) Delay() time.Duration {
    var delay time.Duration
    
    if i.config.Fixed > 0 {
        delay = i.config.Fixed
    } else if i.config.Min > 0 && i.config.Max > 0 {
        // Random between min and max
        rangeNs := i.config.Max.Nanoseconds() - i.config.Min.Nanoseconds()
        delay = i.config.Min + time.Duration(i.rand.Int63n(rangeNs))
    }
    
    // Add jitter
    if i.config.Jitter > 0 {
        jitterNs := i.config.Jitter.Nanoseconds()
        jitter := time.Duration(i.rand.Int63n(jitterNs*2)) - i.config.Jitter
        delay += jitter
    }
    
    return delay
}
```

### 7.5 Traffic Mirroring

```go
// internal/mirror/handler.go

import (
    "bytes"
    "io"
    "log"
    "net/http"
    "sync"
)

type MirrorHandler struct {
    Target    string
    Percentage float64
    Client   *http.Client
    rand     *rand.Rand
    mu       sync.Mutex
}

func New(target string, percentage float64) *MirrorHandler {
    return &MirrorHandler{
        Target:    target,
        Percentage: percentage,
        Client: &http.Client{
            Timeout: 5 * time.Second,
        },
        rand: rand.New(rand.NewSource(time.Now().UnixNano())),
    }
}

// Mirror sends a copy of the request to the shadow service
func (m *MirrorHandler) Mirror(req *http.Request) {
    // Check percentage
    if m.Percentage < 100 && m.rand.Float64()*100 > m.Percentage {
        return
    }
    
    // Create mirror request
    body, _ := io.ReadAll(req.Body)
    req.Body = io.NopCloser(bytes.NewReader(body))
    
    mirrorReq, err := http.NewRequest(
        req.Method,
        m.Target+req.URL.Path,
        bytes.NewReader(body),
    )
    if err != nil {
        log.Printf("[mirror] create failed: %v", err)
        return
    }
    
    // Copy headers, add shadow identification
    for k, v := range req.Header {
        mirrorReq.Header[k] = v
    }
    mirrorReq.Header.Set("X-Mirror-Service", "true")
    
    // Fire and forget - discard response
    go func() {
        resp, err := m.Client.Do(mirrorReq)
        if err != nil {
            log.Printf("[mirror] request failed: %v", err)
            return
        }
        defer resp.Body.Close()
        
        // Always discard body to free resources
        io.Copy(io.Discard, resp.Body)
        
        log.Printf("[mirror] completed: status=%d", resp.StatusCode)
    }()
}
```

### 7.6 Mock Handler

```go
// internal/mock/handler.go

type MockHandler struct {
    StatusCode int
    Headers   http.Header
    Body      []byte
    bodyFile  string
}

func NewMock(config *MockConfig) *MockHandler {
    body := []byte(config.Body)
    if config.BodyFile != "" {
        body, _ = os.ReadFile(config.BodyFile)
    }
    
    return &MockHandler{
        StatusCode: config.StatusCode,
        Headers:   config.Headers,
        Body:     body,
    }
}

func (m *MockHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
    // Set headers
    for k, v := range m.Headers {
        w.Header()[k] = v
    }
    
    // Write response
    w.WriteHeader(m.StatusCode)
    w.Write(m.Body)
}
```

### 7.7 Main Proxy Server

```go
// internal/proxy/proxy.go

type Proxy struct {
    router     *router.Router
    client     *http.Client
    defaults   *DefaultsConfig
}

func NewProxy(cfg *Config) (*Proxy, error) {
    p := &Proxy{
        router: router.NewRouter(),
        client: &http.Client{
            Timeout: cfg.Server.ReadTimeout,
            Transport: &http.Transport{
                MaxIdleConns:        100,
                MaxIdleConnsPerHost: 10,
                IdleConnTimeout:    90 * time.Second,
            },
        },
        defaults: &cfg.Defaults,
    }
    
    // Load routes
    for _, route := range cfg.Routes {
        if err := p.router.AddRoute(route); err != nil {
            return nil, err
        }
    }
    
    return p, nil
}

func (p *Proxy) ServeHTTP(w http.ResponseWriter, r *http.Request) {
    // Find matching route
    route, handler := p.router.Match(r)
    if route == nil {
        http.NotFound(w, r)
        return
    }
    
    // Apply handlers in order
    handler.ServeHTTP(w, r)
}
```

---

## 8. Error Handling

### 8.1 Error Categories

| Category | Description | Handling |
|----------|------------|----------|
| `ConfigurationError` | Invalid config file | Log and exit on startup |
| `RoutingError` | No matching route | Return 404 |
| `RateLimitError` | Rate limit exceeded | Return 429 with Retry-After |
| `CircuitOpenError` | Circuit breaker open | Return 503 |
| `TimeoutError` | Backend timeout | Return 504 |
| `BackendError` | Backend returned error | Return 502 with error details |
| `MirrorError` | Mirror request failed | Log and continue (non-blocking) |

### 8.2 Error Recovery Strategies

```go
// Circuit breaker open - fail fast with 503
if errors.Is(err, ErrCircuitOpen) {
    w.Header().Set("Retry-After", "30")
    http.Error(w, "Service Unavailable", http.StatusServiceUnavailable)
    return
}

// Rate limit exceeded - return 429
if errors.Is(err, ErrRateLimited) {
    w.Header().Set("Retry-After", "1")
    http.Error(w, "Too Many Requests", http.StatusTooManyRequests)
    return
}

// Backend timeout - return 504 with context
if errors.Is(err, ErrTimeout) {
    http.Error(w, "Gateway Timeout", http.StatusGatewayTimeout)
    return
}

// Mirror failure - log and continue (non-critical)
log.Printf("[mirror] shadow request failed: %v", err)
// Primary request continues normally
```

### 8.3 Logging Structure

All errors should be logged with sufficient context:

```go
log.Error().
    Str("component", "circuit_breaker").
    Str("backend", service).
    Int("failure_count", count).
    Err(err).
    Msg("circuit opened")
```

### 8.4 Graceful Degradation

| Component | Degradation Mode |
|-----------|----------------|
| Circuit Breaker | Return 503, do not crash |
| Rate Limiter | Return 429, do not crash |
| Delay Injection | Skip delay on error, continue |
| Mirror | Log failure, continue |
| Mock | Return 500 with error message |

---

## 9. Edge Cases

### 9.1 Request Edge Cases

| Edge Case | Expected Behavior |
|----------|----------------|
| Request body > 1MB | Read and buffer efficiently; reject if > 10MB |
| Request with trailer headers | Buffer entire body; include trailers in mirrored request |
| WebSocket request | Proxy upgrade handshake; stream data |
| Request to offline backend | Open circuit after threshold |
| Concurrent requests exceed burst | Queue and process in order |
| Malformed URL | Return 400 Bad Request |
| Missing Content-Length with chunked | Handle chunked transfer properly |

### 9.2 Configuration Edge Cases

| Edge Case | Expected Behavior |
|----------|----------------|
| Duplicate route names | Error on load with clear message |
| Circular backend references | Detect and error on load |
| Invalid regex in path | Validate on load |
| Backend URL unreachable | Log warning, continue startup |
| Missing required field | Error on load |
| Unknown field in config | Log warning, ignore |

### 9.3 Traffic Mirroring Edge Cases

| Edge Case | Expected Behavior |
|----------|----------------|
| Mirror target offline | Log error, continue primary |
| Mirror returns 5xx | Log but don't trip circuit on primary |
| Large response body from mirror | Discard immediately |
| Slow mirror response | Timeout after 5s |

### 9.4 Circuit Breaker Edge Cases

| Edge Case | Expected Behavior |
|----------|----------------|
| All backends fail | Open circuit, return 503 |
| Backend recovers quickly | Close circuit faster (half-open works) |
| Flapping circuit | Increase timeout after repeated opens |
| No requests for long time | Reset failure count |
| Concurrent failures | Account for race conditions |

### 9.5 Rate Limiting Edge Cases

| Edge Case | Expected Behavior |
|----------|----------------|
| First request of window | Allow (bucket has burst tokens) |
| Multiple concurrent requests | Process all up to burst |
| Client IP changes mid-window | New bucket per IP |
| Invalid rate limit key | Fall back to client IP |
| RPS < 1 | Allow fractional requests |

---

## 10. Testing Strategy

### 10.1 Test Types

| Test Type | Coverage |
|----------|---------|
| Unit tests | Individual components (router, circuit, rate limiter) |
| Integration tests | Full request flow through proxy |
| Integration tests with backends | Real HTTP calls |
| Chaos tests | Simulate backend failures |

### 10.2 Test Infrastructure

```yaml
# docker-compose.yml for testing
services:
  proxy:
    build: .
    ports:
      - "8080:8080"
      - "9090:9090"
  
  backend-v1:
    image: mock-backend:1.0
    ports:
      - "8080:8080"
  
  backend-v2:
    image: mock-backend:2.0
    ports:
      - "8081:8080"
  
  shadow:
    image: mock-shadow
    ports:
      - "8082:8080"
```

---

## 11. Acceptance Criteria

### 11.1 Functional Requirements

- [ ] Routes requests to configured backends
- [ ] Supports wildcard path matching
- [ ] Returns mock responses when configured
- [ ] Injects configurable delays
- [ ] Opens circuit after failure threshold
- [ ] Returns 503 when circuit is open
- [ ] Limits rate per client
- [ ] Returns 429 when rate limited
- [ ] Mirrors traffic to shadow service
- [ ] Loads configuration from YAML
- [ ] Exposes health check endpoint

### 11.2 Non-Functional Requirements

- [ ] Startup time < 1 second
- [ ] Memory usage < 50MB idle
- [ ] Latency overhead < 5ms (no delays)
- [ ] Graceful shutdown support

### 11.3 Configuration Requirements

- [ ] Single YAML config file
- [ ] Environment variable substitution
- [ ] Config hot reload via API

---

## 12. Future Considerations

### 12.2 Phase 2 Features

- **Service Discovery**: Integration with Consul, etcd
- **Metrics Export**: Prometheus, OpenTelemetry
- **Distributed Rate Limiting**: Redis-backed
- **Request/Response Logging**: JSON structured logs
- **gRPC Support**: Proxy gRPC traffic

### 12.3 Phase 3 Features

- **Dynamic Routes**: Update routes without restart
- **Traffic Splitting**: A/B testing with percentage
- **OAuth/Auth**: Request authentication
- **WASM Filters**: Custom request processing

---

## References

- Service Mesh: [Istio Traffic Mirroring](https://istio.io/docs/tasks/traffic-management/mirroring/)
- Circuit Breaker: [Sony gobreaker](https://github.com/sony/gobreaker)
- Rate Limiting: [golang.org/x/time/rate](https://pkg.go.dev/golang.org/x/time/rate)
- Proxy Framework: [vulcand/oxy](https://github.com/vulcand/oxy)

---

*Document Version: 1.0*
*Last Updated: April 2026*