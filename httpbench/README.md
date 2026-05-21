# HTTPBench

An HTTP load testing CLI tool built in Go with concurrent workers, metrics, and flexible output formats.

## Features

- **Concurrent Requests**: Execute N parallel goroutines sending requests
- **Request Methods**: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- **Duration Mode**: Run load test for specified duration (e.g., 30s, 1m)
- **Count Mode**: Run exact number of requests (e.g., 10,000 requests)
- **Response Time Metrics**: Latency tracking with percentiles (p50, p95, p99)
- **RPS Metrics**: Calculate requests per second throughput
- **Custom Headers**: Add headers like Authorization, Content-Type
- **Request Body**: JSON, form-data, raw body support
- **Timeout Configuration**: Per-request timeout setting
- **Output Formats**: Text and JSON output

## Installation

### From Source

```bash
go build -o httpbench .
```

Or using Docker:

```bash
docker run --rm -v $(pwd):/app -w /app golang:1.21 go build -o httpbench .
```

### Pre-built Binary

Download a pre-built binary from the releases page and ensure it's in your PATH.

## Usage

```bash
httpbench [options] <url>
```

## Options

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--url` | - | **required** | Target URL to test |
| `--method` | `-X` | GET | HTTP method |
| `--concurrency` | `-c` | 10 | Number of concurrent workers |
| `--duration` | `-d` | 10s | Test duration (e.g., 10s, 1m, 1h) |
| `--requests` | `-n` | 0 | Total requests (0 = duration mode) |
| `--rate` | `-r` | 0 | Max RPS per worker (0 = unlimited) |
| `--timeout` | `-t` | 30s | Request timeout |
| `--header` | `-H` | none | Add header (comma-separated) |
| `--body` | - | none | Request body |
| `--body-file` | `-f` | none | File containing request body |
| `--format` | - | text | Output format (text, json) |
| `--quiet` | `-q` | false | Minimal output |

## Examples

### Basic GET test

```bash
httpbench -c 10 -d 30s https://api.example.com/endpoint
```

### POST with JSON body

```bash
httpbench -c 50 -n 10000 -X POST --body '{"key": "value"}' https://api.example.com/endpoint
```

### With authentication header

```bash
httpbench -H "Authorization: Bearer token" -c 20 -d 1m https://api.example.com/protected
```

### JSON output for scripting

```bash
httpbench -c 10 -d 30s --format json https://api.example.com/endpoint
```

### Request count mode

```bash
httpbench -c 10 -n 1000 https://api.example.com/endpoint
```

### With rate limiting

```bash
httpbench -c 5 -r 10 -d 30s https://api.example.com/endpoint
```

### Using body from file

```bash
httpbench -c 10 -d 30s -f body.json https://api.example.com/endpoint
```

## Output Example

### Text Format

```
Running 30s test @ https://api.example.com/users
 10 workers, 3008 requests completed

  RPS: 100.27
  Latency:
    min: 12ms
    avg: 45ms
    p50: 42ms
    p95: 78ms
    p99: 156ms
    max: 312ms

  HTTP Status Codes:
    200: 3008 (100.0%)

  Errors:
    connection errors: 0
    timeouts: 0
    non-2xx: 0
```

### JSON Format

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
    "success": 3008,
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
  },
  "errors": {
    "connection_errors": 0,
    "timeouts": 0,
    "non_2xx": 0
  }
}
```

## Architecture

```
httpbench/
├── cmd/flags.go       - CLI argument parsing
├── config/config.go   - Validated configuration struct
├── client/http.go     - HTTP client with timeouts
├── worker/pool.go     - Worker goroutine management
├── metrics/collector.go - Thread-safe metrics collection
├── output/formatter.go  - Text/JSON output formatting
└── main.go            - Entry point
```

## License

MIT