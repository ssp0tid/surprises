# Trafix

A local HTTP API gateway and traffic inspector that sits between client applications and target APIs. Provides middleware-based request transformation, persistent request/response history in SQLite, a web dashboard for real-time traffic inspection, and built-in analytics.

## Features

- **HTTP Proxy**: Forward requests to target APIs with path-based routing
- **Rate Limiting**: Per-IP or per-API key rate limiting with configurable limits
- **Authentication**: API key-based authentication
- **Request Logging**: Log all requests and responses with configurable body size limits
- **CORS Support**: Configurable CORS middleware
- **SQLite Storage**: Persistent storage of all request/response data
- **Dashboard**: Web-based dashboard for viewing traffic and analytics
- **Analytics**: Real-time metrics including requests/sec, response times, error rates

## Requirements

- Go 1.22 or later
- SQLite3
- CGO enabled (for SQLite driver)

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/trafix.git
cd trafix

# Build
make build

# Or run directly
make run-dev
```

### Using Make

```bash
# Install dependencies
make deps

# Build the binary
make build

# Run the application
make run

# Run tests
make test

# Clean build artifacts
make clean

# Install to ~/go/bin
make install
```

## Configuration

Configuration is loaded from `config.yaml` in the following order:
1. Current directory
2. `./config` directory
3. `$HOME/.trafix`

Environment variables can override config values. Prefix with `TRAFIX_`:

```bash
TRAFIX_SERVER_HOST=0.0.0.0
TRAFIX_SERVER_PORT=8080
TRAFIX_PROXY_TARGET=http://localhost:3000
TRAFIX_RATE_LIMIT_ENABLED=true
TRAFIX_RATE_LIMIT_RPS=100
```

### Configuration Options

| Section | Option | Description | Default |
|---------|--------|-------------|---------|
| server.host | string | Server bind address | 127.0.0.1 |
| server.port | int | Server port | 8080 |
| server.log_level | string | Log level (debug, info, warn, error) | info |
| dashboard.host | string | Dashboard bind address | 127.0.0.1 |
| dashboard.port | int | Dashboard port | 8081 |
| dashboard.username | string | Dashboard basic auth username | admin |
| dashboard.password | string | Dashboard basic auth password | changeme |
| proxy.host | string | Proxy bind address | 127.0.0.1 |
| proxy.port | int | Proxy port | 8082 |
| proxy.target_base_url | string | Target API base URL | http://localhost:3000 |
| proxy.timeout | duration | Request timeout | 30s |
| storage.database | string | SQLite database path | ./trafix.db |
| storage.max_connections | int | Max DB connections | 10 |
| middleware.rate_limit.enabled | bool | Enable rate limiting | true |
| middleware.rate_limit.requests_per_second | int | Requests per second | 100 |
| middleware.rate_limit.burst | int | Burst size | 20 |
| middleware.auth.enabled | bool | Enable API key auth | false |
| middleware.auth.api_keys | []string | Valid API keys | [] |
| middleware.logging.enabled | bool | Enable request logging | true |
| middleware.logging.max_body_size | int | Max body size to log | 10240 |
| middleware.cors.enabled | bool | Enable CORS | false |
| middleware.cors.allowed_origins | []string | Allowed origins | [] |

## Usage

### Running the Server

```bash
# Default configuration
./bin/trafix

# With custom config
./bin/trafix -config /path/to/config.yaml
```

### Accessing the Dashboard

Navigate to `http://127.0.0.1:8081` in your browser. You'll be prompted for basic auth credentials (default: admin/changeme).

### Making Proxy Requests

```bash
# Forward request through proxy
curl http://127.0.0.1:8080/api/v1/users

# With API key (if auth is enabled)
curl -H "Authorization: sk-test-12345" http://127.0.0.1:8080/api/v1/users

# POST request
curl -X POST http://127.0.0.1:8080/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"name": "test"}'
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /health | GET | Health check |
| /api/v1/* | * | Proxy to target API |
| /dashboard | GET | Dashboard UI |

## Architecture

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

## Development

### Running Tests

```bash
make test
```

### Code Formatting

```bash
make fmt
```

### Linting

```bash
make lint
```

## License

MIT License - see LICENSE file for details