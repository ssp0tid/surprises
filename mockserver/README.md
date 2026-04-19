# MockAPI - Zero-Config Mock API Server

A lightweight mock REST API server for frontend developers. No configuration needed - just run and start making requests.

## Quick Start

```bash
python mockapi.py
```

Server starts on `http://localhost:8080`. Open in browser to see server info.

## Installation

Zero installation required. Just clone and run:

```bash
git clone <repo>
cd mockserver
python mockapi.py
```

## CLI Flags

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--port` | `-p` | 8080 | Server port |
| `--host` | `-H` | localhost | Server host |
| `--delay` | `-d` | 0 | Global response delay (ms) |
| `--cors` | `-c` | true | Enable CORS (true/false) |
| `--log` | `-l` | true | Enable request logging |

## Examples

```bash
# Default: localhost:8080
python mockapi.py

# Custom port
python mockapi.py -p 3000

# With delay
python mockapi.py -d 500

# Disable CORS
python mockapi.py -c false

# Combine options
python mockapi.py -p 3000 -d 200 -c true
```

## Features

- **Zero config**: Just run, no setup needed
- **Dynamic routes**: Pattern-based matching with `:param` syntax
- **All HTTP methods**: GET, POST, PUT, DELETE, PATCH
- **Auto mock responses**: Returns request metadata when no custom response
- **CORS enabled**: Works with browser fetch/XHR
- **Delay simulation**: Test slow network scenarios
- **Request inspection**: See all request details in response
- **Custom responses**: Override status/body via headers or request body

## Built-in Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Server info, available routes |
| `/health` | GET | Health check |
| `/echo` | * | Echo back the request as JSON |
| `/delay/:ms` | GET | Test endpoint with configurable delay |

## Client Usage

```bash
# GET request (auto mock response)
curl http://localhost:8080/api/users/123

# POST with custom response
curl -X POST http://localhost:8080/api/users \
  -H "Content-Type: application/json" \
  -d '{"status": 201, "body": {"id": 1, "name": "Test"}}'

# Test delay
curl http://localhost:8080/delay/1000
```

## Response Override

### Via Request Body (POST/PUT/PATCH)

```json
{
  "status": 201,
  "body": {"id": 123, "name": "Created"},
  "headers": {"X-Custom-Header": "value"},
  "delay": 500
}
```

### Via Headers

```
X-Mock-Status: 201
X-Mock-Delay: 500
X-Mock-Body: {"key": "value"}
```

## Route Patterns

| Pattern | Matches |
|---------|---------|
| `/users` | `/users` |
| `/users/:id` | `/users/123` |
| `/users/:id/posts` | `/users/123/posts` |
| `/files/:path*` | `/files/a/b/c` |

## Requirements

- Python 3.7+
- No external dependencies (standard library only)