# mesh-proxy

Local service mesh proxy for development — traffic routing, mock responses, delay injection, circuit breaking, rate limiting, and traffic mirroring.

## Features

- **Traffic Routing** — Route requests to backends by path, method, headers
- **Mock Responses** — Serve mock responses without hitting real backends
- **Delay Injection** — Simulate network latency/jitter
- **Circuit Breaking** — Prevent cascade failures
- **Rate Limiting** — Token bucket rate limiting per route
- **Traffic Mirroring** — Mirror requests to shadow services
- **Admin API** — Hot-reload config, view stats

## Quick Start

```bash
go build -o mesh-proxy ./cmd/mesh-proxy
./mesh-proxy --config configs/default.yaml
```

## Configuration

Edit `configs/default.yaml`:

```yaml
server:
  host: "0.0.0.0"
  port: 8080

routes:
  - name: "api"
    match:
      path: "/api/*"
    backend:
      url: "http://localhost:3000"
    rate_limit:
      enabled: true
      rps: 100
      burst: 200
    circuit_breaker:
      enabled: true
      failure_rate: 0.5
      window_seconds: 60
      recovery_seconds: 30
```

## Admin API

- `GET /health` — Health check
- `GET /admin/config` — Current config
- `GET /admin/routes` — Route list
- `GET /admin/circuit/breakers` — Circuit breaker states
- `GET /admin/stats` — Runtime stats
- `POST /admin/reload` — Reload config

## Example: Mock Response

```yaml
routes:
  - name: "mock-users"
    match:
      path: "/users"
      methods: ["GET"]
    mock:
      enabled: true
      status_code: 200
      headers:
        Content-Type: "application/json"
      body: '[{"id": 1, "name": "Alice"}]'
```

## Example: Delay Injection

```yaml
routes:
  - name: "slow-api"
    match:
      path: "/api/slow"
    backend:
      url: "http://localhost:3000"
    delay:
      enabled: true
      fixed: 2000
      jitter: 500
```

## Example: Traffic Mirroring

```yaml
routes:
  - name: "mirror-api"
    match:
      path: "/api/*"
    backend:
      url: "http://localhost:3000"
    mirror:
      enabled: true
      url: "http://localhost:4000"
      percentage: 10
```