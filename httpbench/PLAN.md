# HTTPBench - HTTP Load Testing CLI Tool

## Project Overview

**Project Name:** HTTPBench  
**Type:** CLI Load Testing Tool  
**Language:** Go (recommended for performance) or Node.js/TypeScript  
**Core Functionality:** Send concurrent HTTP requests and collect performance metrics  

---

## Feature Specification

### 1. Core Features

| Feature | Description |
|---------|-------------|
| **Concurrent Requests** | Execute N parallel goroutines/workers sending requests |
| **Request Methods** | Support GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS |
| **Duration Mode** | Run load test for specified duration (e.g., 30s, 1m) |
| **Count Mode** | Run exact number of requests (e.g., 10,000 requests) |
| **Response Time Metrics** | Capture latency for each request |
| **RPS Metrics** | Calculate requests per second throughput |
| **HTTP Headers** | Custom headers support (e.g., Authorization, Content-Type) |
| **Request Body** | JSON, form-data, raw body support |
| **Timeout Configuration** | Per-request timeout setting |

### 2. User Interface

#### CLI Arguments

```bash
httpbench [options] <url>
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--url` | - | **required** | Target URL to test |
| `--method` | `-X` | GET | HTTP method |
| `--concurrency` | `-c` | 10 | Number of concurrent workers |
| `--duration` | `-d` | 10s | Test duration (e.g., 10s, 1m, 1h) |
| `--requests` | `-n` | 0 | Total requests (0 = duration mode) |
| `--rate` | `-r` | 0 | Max RPS per worker (0 = unlimited) |
| `--timeout` | `-t` | 30s | Request timeout |
| `--header` | `-H` | none | Add header (repeatable) |
| `--body` | `-d` | none | Request body |
| `--body-file` | `-f` | none | File containing request body |
| `--format` | | text | Output format (text, json) |
| `--quiet` | `-q` | false | Minimal output |

#### Example Usage

```bash
# Basic GET test, 10 concurrent, 30 seconds
httpbench -c 10 -d 30s https://api.example.com/endpoint

# POST test with body, 50 concurrent, 10000 requests
httpbench -c 50 -n 10000 -X POST -d '{"key": "value"}' https://api.example.com/endpoint

# With auth header
httpbench -H "Authorization: Bearer token" -c 20 -d 1m https://api.example.com/protected

# JSON output for scripting
httpbench -c 10 -d 30s --format json https://api.example.com/endpoint
```

### 3. Metrics Output

#### Text Format (Default)

```
Running 30s test @ https://api.example.com/users
 10 workers, 3008 requests completed
  RPS: 100.3
  Latency:
    min: 12ms
    avg: 45ms
    p50: 42ms
    p95: 78ms
    p99: 156ms
    max: 312ms
  HTTP Status Codes:
    200: 3008 (100%)
  Errors:
    connection errors: 0
    timeouts: 0
    non-2xx: 0
```

#### JSON Format

```json
{
  "test": {
    "url": "https://api.example.com/users",
    "method": "GET",
    "concurrency": 10,
    "duration_seconds": 30,
    "timestamp": "2026-04-19T10:30:00Z"
  },
  "summary": {
    "requests": 3008,
    "rps": 100.27,
    " Success": 3008,
    "errors": 0
  },
  "latency": {
    "min_ms": 12,
    "avg_ms": 45,
    "p50_ms": 42,
    "p95_ms": 78,
    "p99_ms": 156,
    "max_ms": 312
  },
  "status_codes": {
    "200": 3008
  }
}
```

### 4. Internal Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        httpbench                            │
├─────────────────────────────────────────────────────────────┤
│  CLI Args                                                   │
│    │                                                        │
│    ▼                                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Config / Options                         │  │
│  └──────────────────────────────────────────────────────┘  │
│    │                                                        │
│    ▼                                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Worker Pool (goroutines)                     │  │
│  │    ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                   │  │
│  │    │ W1  │ │ W2  │ │ W3  │ │ Wn  │ ──► Send HTTP      │  │
│  │    └─────┘ └─────┘ └─────┘ └─────┘                     │  │
│  └──────────────────────────────────────────────────────┘  │
│    │                                                        │
│    ▼                                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Metrics Collector                         │  │
│  │   - Response times (slice of durations)             │  │
│  │   - Status code counts (map)                         │  │
│  │   - Error counts                                     │  │
│  │   - Request counter                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│    │                                                        │
│    ▼                                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Result Formatter                        │  │
│  │   - Text output                                     │  │
│  │   - JSON output                                      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 5. Key Modules

| Module | Responsibility |
|--------|----------------|
| `cmd/flags.go` | CLI argument parsing |
| `config/config.go` | Validated configuration struct |
| `client/http.go` | HTTP client with timeouts |
| `worker/pool.go` | Worker goroutine management |
| `worker/worker.go` | Individual worker execution |
| `metrics/collector.go` | Thread-safe metrics collection |
| `metrics/stats.go` | Statistical calculations (p50, p95, p99) |
| `output/formatter.go` | Text/JSON output formatting |
| `main.go` | Entry point |

---

## Technical Decisions

### Language: Go

**Rationale:**
- Native goroutines for true concurrency (not async/await emulation)
- Low memory footprint for high RPS
- No runtime overhead
- Single binary deployment

### Concurrency Model

- Use `sync.WaitGroup` + channel for result collection
- Each worker is a goroutine that loops until test ends
- Results sent to channel, single collector goroutine
- Atomic counters for shared metrics

### Rate Limiting (Optional)

- Token bucket per worker if `--rate` specified
- Allows controlled RPS testing

---

## Implementation Phases

### Phase 1: Basic Core
- CLI argument parsing with flag library
- Basic HTTP client with timeout
- Worker pool with concurrent workers
- Duration-based test execution
- Simple text output

### Phase 2: Metrics
- Response time collection
- Status code tracking
- Error counting
- Statistical calculations

### Phase 3: Features
- Request count mode (instead of duration)
- Custom headers
- Request body support
- JSON output

### Phase 4: Polish
- Progress bar (optional)
- Better error messages
- Help text
- Version info

---

## Acceptance Criteria

- [ ] CLI runs without errors on `httpbench -h`
- [ ] Basic GET request to valid URL completes
- [ ] Concurrent requests work (verifiable via logs/timing)
- [ ] Response time metrics display correctly (min/avg/max)
- [ ] P50, P95, P99 percentiles calculated correctly
- [ ] RPS throughput reported accurately
- [ ] Errors captured and reported (connection failed, timeouts)
- [ ] JSON output valid and parseable
- [ ] Custom headers added to requests
- [ ] POST with body works
- [ ] Timeout respected
- [ ] Duration mode stops after specified time
- [ ] Request count mode stops after N requests

---

## Future Enhancements (Out of Scope)

- WebSocket support
- HTTP/2 multiplexing
- SSL certificate validation options
- CSV export
- Live dashboard with WebSocket stats
- Scenario scripting (JSON/YAML config files)
- Request templates
- Response body validation/assertions
- Graph generation (ASCII charts)