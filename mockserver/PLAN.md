# Zero-Config Mock API Server - Implementation Plan

## Project Overview

**Name:** `mockapi`
**Type:** CLI tool / single-file Python application
**Core Functionality:** Instant mock REST API server with zero configuration, designed for frontend developers who need quick backend responses during development.
**Target Users:** Frontend developers, API consumers testing integrations, rapid prototyping

---

## 1. File Structure

```
mockapi.py          # Single self-contained file (~400-600 lines)
```

**No external dependencies.** Uses only Python standard library:
- `http.server` - HTTP server
- `socketserver` - TCP server
- `argparse` - CLI argument parsing
- `json` - JSON handling
- `urllib.parse` - URL parsing
- `datetime` - Timestamps
- `threading` - Concurrent request handling
- `sys` - CLI exit codes

---

## 2. Feature List

### 2.1 Core Features

| Feature | Description |
|---------|-------------|
| **Instant Startup** | No config files, no installation. Just run `python mockapi.py` |
| **Dynamic Route Matching** | Pattern-based routes: `/users/:id`, `/posts/:post_id/comments/:id` |
| **HTTP Method Support** | GET, POST, PUT, DELETE, PATCH |
| **Auto JSON Response** | Returns mock JSON with request metadata when no custom response |
| **Request Logging** | Colored console output with method, path, status, timing |
| **Delay Simulation** | Global or per-request delays to simulate network latency |
| **CORS Enabled** | Pre-flight handling, Access-Control headers on all responses |
| **Status Code Mocking** | Return custom HTTP status codes |
| **Header Inspection** | Log and expose request headers in response |
| **Body Parsing** | Parse JSON/form data request bodies |

### 2.2 CLI Flags

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--port` | `-p` | 8080 | Server port |
| `--host` | `-H` | localhost | Server host |
| `--delay` | `-d` | 0 | Global response delay (ms) |
| `--cors` | `-c` | true | Enable CORS (true/false) |
| `--log` | `-l` | true | Enable request logging |
| `--help` | `-h` | - | Show help |

### 2.3 Auto-Generated Responses

When no mock data is configured, returns:

```json
{
  "mock": true,
  "method": "GET",
  "path": "/api/users/123",
  "timestamp": "2024-01-15T10:30:00.123Z",
  "query": {},
  "headers": {},
  "body": null,
  "matched": true,
  "message": "Mock response - customize via request body or route config"
}
```

---

## 3. API Design

### 3.1 Route Matching

**Pattern Syntax:**
- `:param` - Path parameter (captures segment)
- `:param*` - Wildcard parameter (captures remaining path)
- `*` - Catch-all wildcard

**Examples:**
| Pattern | Matches |
|---------|---------|
| `/users` | `/users` |
| `/users/:id` | `/users/123` |
| `/users/:id/posts` | `/users/123/posts` |
| `/files/:path*` | `/files/a/b/c` |

**Parameter Extraction:**
- Path params available in `request.path_params`
- Query params in `request.query`

### 3.2 Request Object

```python
class MockRequest:
    method: str           # GET, POST, PUT, DELETE, PATCH
    path: str             # /api/users/123
    path_params: dict     # {'id': '123'}
    query: dict           # {'page': '1', 'limit': '10'}
    headers: dict         # All request headers
    body: bytes | None    # Raw request body
    json_body: dict       # Parsed JSON (if applicable)
    form_data: dict       # Parsed form data (if applicable)
    timestamp: datetime   # Request timestamp
```

### 3.3 Response Object

```python
class MockResponse:
    status_code: int = 200
    headers: dict = {}
    body: str = ""
    delay: int = 0  # ms, overrides global delay
```

### 3.4 Dynamic Response via Request Body

**POST/PUT/PATCH requests can include response config in body:**

```json
{
  "status": 201,
  "body": {
    "id": 123,
    "name": "Created Resource"
  },
  "headers": {
    "X-Custom-Header": "value"
  },
  "delay": 500
}
```

**Headers override:**
```
X-Mock-Status: 201
X-Mock-Delay: 500
X-Mock-Body: {"key": "value"}
```

### 3.5 Built-in Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Server info, available routes |
| `/health` | GET | Health check |
| `/echo` | * | Echo back the request as JSON |
| `/delay/:ms` | GET | Test endpoint with configurable delay |

---

## 4. Architecture

### 4.1 Components

```
┌─────────────────────────────────────────────────────┐
│                    mockapi.py                       │
├─────────────────────────────────────────────────────┤
│  CLI Parser (argparse)                              │
│    └─> Config (port, host, delay, cors)            │
├─────────────────────────────────────────────────────┤
│  Router                                             │
│    ├─> Pattern compiler (regex-based)              │
│    ├─> Route registry (method + path patterns)     │
│    └─> Matcher (returns handler + params)          │
├─────────────────────────────────────────────────────┤
│  Request Handler                                    │
│    ├─> Parse incoming request                      │
│    ├─> Extract path params                          │
│    ├─> Parse body (JSON/form)                       │
│    ├─> Apply delay                                  │
│    ├─> Generate response                            │
│    └─> Log request                                  │
├─────────────────────────────────────────────────────┤
│  Response Generator                                 │
│    ├─> Auto-response (mock metadata)               │
│    ├─> Custom body response                         │
│    ├─> Status code handling                        │
│    └─> CORS header injection                       │
├─────────────────────────────────────────────────────┤
│  Logger                                             │
│    └─> Colored console output                      │
└─────────────────────────────────────────────────────┘
```

### 4.2 Class Design

```python
# Configuration
@dataclass
class ServerConfig:
    port: int = 8080
    host: str = "localhost"
    delay: int = 0  # milliseconds
    cors: bool = True
    log_enabled: bool = True

# Request/Response models
@dataclass
class MockRequest:
    method: str
    path: str
    path_params: dict
    query: dict
    headers: dict
    body: bytes
    json_body: Optional[dict]
    form_data: Optional[dict]
    timestamp: datetime

@dataclass
class MockResponse:
    status_code: int = 200
    headers: Optional[dict] = None
    body: Optional[str] = None
    delay: int = 0

# Router
class Router:
    def add_route(self, method: str, pattern: str, handler: Callable)
    def match(self, method: str, path: str) -> Tuple[Optional[Handler], dict]

# Server
class MockAPIServer(BaseHTTPRequestHandler):
    def do_GET(self)
    def do_POST(self)
    def do_PUT(self)
    def do_DELETE(self)
    def do_PATCH(self)
    def do_OPTIONS(self)  # CORS preflight
```

---

## 5. Error Handling

### 5.1 HTTP Error Responses

| Scenario | Status | Response Body |
|----------|--------|---------------|
| Route not found | 404 | `{"error": "Not Found", "path": "/xyz"}` |
| Method not allowed | 405 | `{"error": "Method Not Allowed", "allowed": ["GET", "POST"]}` |
| Invalid JSON body | 400 | `{"error": "Invalid JSON", "detail": "..."}` |
| Server error | 500 | `{"error": "Internal Server Error"}` |

### 5.2 Error Response Format

```json
{
  "error": true,
  "status": 404,
  "message": "Route not found",
  "path": "/unknown",
  "method": "GET",
  "timestamp": "2024-01-15T10:30:00.123Z"
}
```

### 5.3 Exception Handling

- All exceptions caught at handler level
- Never crash server on bad request
- Log errors with stack trace in debug mode

---

## 6. Edge Cases

### 6.1 Request Handling

| Edge Case | Handling |
|-----------|----------|
| Empty body | `body=None`, `json_body=None` |
| Invalid JSON body | Return 400 with parse error |
| Form data (x-www-form-urlencoded) | Parse into dict |
| Multipart/form-data | Basic field extraction |
| Binary body | Keep as bytes, don't parse |
| Very large body | Limit to 10MB, return 413 if exceeded |
| Unicode in body | Handle UTF-8 properly |
| Missing Content-Type | Default to no body parsing |
| Duplicate headers | Take first value |
| Non-ASCII path | URL-decode properly |

### 6.2 Route Matching

| Edge Case | Handling |
|-----------|----------|
| Trailing slash | `/users` != `/users/` (no redirect) |
| Double slashes | Normalize `//` to `/` |
| URL encoding | Decode `%20` etc. before matching |
| Case sensitivity | Paths are case-sensitive |
| Overlapping patterns | First registered wins |

### 6.3 Response Generation

| Edge Case | Handling |
|-----------|----------|
| None as body | Return `null` in JSON |
| Dict/list as body | JSON-encode automatically |
| Non-UTF-8 bytes | Base64 encode in JSON |
| Empty response | Return `{}` |
| Very large response | No limit, stream if needed |

### 6.4 Server Behavior

| Edge Case | Handling |
|-----------|----------|
| Port already in use | Print error, exit(1) |
| Invalid port number | Validate 1-65535 |
| Ctrl+C | Clean shutdown |
| Concurrent requests | ThreadingTCPServer |
| Slow client | No timeout (developer tooling) |

---

## 7. CORS Implementation

### 7.1 Default CORS Headers

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
Access-Control-Allow-Headers: *
Access-Control-Max-Age: 3600
```

### 7.2 Preflight (OPTIONS)

- All OPTIONS requests return 200
- Include CORS headers
- No body

### 7.3 Disable CORS

```bash
python mockapi.py --cors=false
```

---

## 8. Logging Format

### 8.1 Console Output

```
[10:30:00] GET  /api/users/123  200  15ms
[10:30:01] POST /api/data       201  32ms
[10:30:02] GET  /unknown        404   2ms
```

### 8.2 Color Coding

| Status Range | Color |
|--------------|-------|
| 2xx | Green |
| 3xx | Yellow |
| 4xx | Red |
| 5xx | Magenta (bold) |

### 8.3 Verbose Mode (future)

```
[10:30:00] GET  /api/users/123  200  15ms
           Headers: {"Content-Type": "application/json", ...}
           Query: {"page": "1"}
           Body: None
```

---

## 9. Usage Examples

### 9.1 Basic Usage

```bash
# Default: localhost:8080
python mockapi.py

# Custom port
python mockapi.py --port 3000

# With delay
python mockapi.py --delay 500

# Disable CORS
python mockapi.py --cors=false

# Combine options
python mockapi.py -p 3000 -d 200 -c=true
```

### 9.2 Client Usage

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

### 9.3 Browser Usage

Open browser at `http://localhost:8080` to see server info.

---

## 10. Implementation Phases

### Phase 1: Core Server (Foundation)
- [ ] Basic HTTP server with threading
- [ ] CLI argument parsing
- [ ] GET/POST/PUT/DELETE/PATCH handlers
- [ ] Basic response generation
- [ ] Console logging with colors

### Phase 2: Routing Engine
- [ ] Route pattern compiler
- [ ] Path parameter extraction
- [ ] Route matching logic
- [ ] Built-in endpoints (/, /health, /echo)

### Phase 3: Request Parsing
- [ ] JSON body parsing
- [ ] Form data parsing
- [ ] Header extraction
- [ ] Query parameter parsing
- [ ] Error handling for malformed requests

### Phase 4: Response Features
- [ ] Custom status codes via headers
- [ ] Custom response body via headers
- [ ] Delay simulation
- [ ] Auto-response with request metadata

### Phase 5: CORS
- [ ] CORS header injection
- [ ] OPTIONS preflight handling
- [ ] CORS disable flag

### Phase 6: Polish
- [ ] Color-coded logging
- [ ] Request/response timing
- [ ] Error formatting
- [ ] Help text
- [ ] Edge case handling

---

## 11. Code Style Guidelines

- **No external dependencies** - Pure standard library only
- **Single file** - All code in one `.py` file
- **No type: ignore** - Full type safety
- **No @dataclass** - Explicit class definitions for compatibility
- **No walrus operator** - Python 3.7+ compatible
- **Explicit over implicit** - Clear, readable code
- **Fail gracefully** - Never crash on bad input
- **Helpful defaults** - Sensible out of the box

---

## 12. Success Criteria

1. **Zero config**: `python mockapi.py` just works
2. **Instant startup**: < 100ms to ready
3. **All methods work**: GET, POST, PUT, DELETE, PATCH
4. **CORS ready**: Browser fetch works without issues
5. **Request inspection**: See all request details in response
6. **Customizable**: Override status/body via headers or body
7. **No crashes**: Handles malformed requests gracefully
8. **Clear logging**: See what's happening at a glance
9. **Self-contained**: Single file, no dependencies, no install

---

## 13. Future Enhancements (Out of Scope)

These are NOT in the initial implementation:

- [ ] Response from file (`--file routes.json`)
- [ ] WebSocket support
- [ ] Request recording/playback
- [ ] Proxy mode
- [ ] HTTPS support
- [ ] Config file support
- [ ] Templating (${variable} substitution)
- [ ] Response randomization
- [ ] Rate limiting simulation
