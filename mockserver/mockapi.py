#!/usr/bin/env python3
"""
MockAPI - Zero-Config Mock API Server

A lightweight mock REST API server for frontend developers.
No configuration needed - just run and start making requests.

Usage:
    python mockapi.py                    # Start on localhost:8080
    python mockapi.py -p 3000           # Custom port
    python mockapi.py -d 500             # Add 500ms delay
    python mockapi.py --help             # Show all options
"""

import http.server
import socketserver
import argparse
import json
import re
import sys
import threading
import time
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs, unquote
from typing import Dict, Optional, List, Tuple, Any, Callable


# =============================================================================
# Configuration
# =============================================================================


class ServerConfig:
    """Server configuration with CLI overrides."""

    def __init__(
        self,
        port: int = 8080,
        host: str = "localhost",
        delay: int = 0,
        cors: bool = True,
        log_enabled: bool = True,
    ):
        self.port = port
        self.host = host
        self.delay = delay
        self.cors = cors
        self.log_enabled = log_enabled

    def validate(self) -> bool:
        """Validate configuration values."""
        if not (1 <= self.port <= 65535):
            print(f"Error: Port must be between 1 and 65535, got {self.port}")
            return False
        return True


# =============================================================================
# Request/Response Models
# =============================================================================


class MockRequest:
    """Parsed request object with all extracted data."""

    def __init__(
        self,
        method: str,
        path: str,
        path_params: Optional[Dict[str, str]] = None,
        query: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[bytes] = None,
        json_body: Optional[Dict[str, Any]] = None,
        form_data: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ):
        self.method = method
        self.path = path
        self.path_params = path_params or {}
        self.query = query or {}
        self.headers = headers or {}
        self.body = body
        self.json_body = json_body
        self.form_data = form_data
        self.timestamp = timestamp or datetime.now(timezone.utc)


class MockResponse:
    """Response configuration."""

    def __init__(
        self,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Any] = None,
        delay: int = 0,
    ):
        self.status_code = status_code
        self.headers = headers or {}
        self.body = body
        self.delay = delay


# =============================================================================
# Router
# =============================================================================


class Route:
    """Represents a registered route."""

    def __init__(self, method: str, pattern: str, handler: Callable):
        self.method = method.upper()
        self.pattern = pattern
        self.handler = handler
        # Compiled regex and param names
        self._regex = None
        self._param_names = []
        self._compile()

    def _compile(self) -> None:
        """Compile route pattern into regex."""
        # Split pattern and convert to regex
        parts = self.pattern.split("/")
        param_names = []
        regex_parts = []

        for part in parts:
            if not part:
                regex_parts.append("")
                continue

            if part == "*":
                # Catch-all wildcard
                regex_parts.append("(.*)")
                param_names.append("__wildcard__")
            elif part.endswith("*"):
                # Wildcard parameter /files/:path*
                param_name = part[1:-1]
                param_names.append(param_name)
                regex_parts.append("(.+)")
            elif part.startswith(":"):
                # Path parameter /users/:id
                param_names.append(part[1:])
                regex_parts.append("([^/]+)")
            else:
                # Literal segment
                regex_parts.append(re.escape(part))

        regex = "^" + "/".join(regex_parts) + "$"
        self._regex = re.compile(regex)
        self._param_names = param_names

    def match(self, path: str) -> Optional[Dict[str, str]]:
        """Match a path against this route's pattern."""
        match = self._regex.match(path)
        if not match:
            return None

        # Extract parameters
        params = {}
        groups = match.groups()

        for i, name in enumerate(self._param_names):
            if i < len(groups):
                if name == "__wildcard__":
                    continue  # Skip wildcard, not stored
                params[name] = groups[i]

        return params


class Router:
    """Route registry and matcher."""

    def __init__(self):
        self._routes: List[Route] = []

    def add_route(self, method: str, pattern: str, handler: Callable) -> None:
        """Register a new route."""
        route = Route(method, pattern, handler)
        self._routes.append(route)

    def match(
        self, method: str, path: str
    ) -> Tuple[Optional[Callable], Dict[str, str]]:
        """Find matching route for method and path."""
        method = method.upper()

        for route in self._routes:
            if route.method != method:
                continue

            params = route.match(path)
            if params is not None:
                return route.handler, params

        return None, {}


# =============================================================================
# Response Generator
# =============================================================================


class ResponseGenerator:
    """Generates mock responses."""

    @staticmethod
    def auto_response(request: MockRequest) -> MockResponse:
        """Generate automatic mock response with request metadata."""
        body = {
            "mock": True,
            "method": request.method,
            "path": request.path,
            "timestamp": request.timestamp.isoformat().replace("+00:00", "Z"),
            "query": request.query,
            "headers": {
                k: v
                for k, v in request.headers.items()
                if k.lower() not in ("host", "content-length")
            },
            "body": request.json_body
            if request.json_body is not None
            else request.body,
            "path_params": request.path_params,
            "matched": True,
            "message": "Mock response - customize via request body or headers",
        }

        return MockResponse(status_code=200, body=body)

    @staticmethod
    def error_response(
        status_code: int,
        message: str,
        path: str = "",
        method: str = "GET",
        details: Optional[Any] = None,
    ) -> MockResponse:
        """Generate error response."""
        body = {
            "error": True,
            "status": status_code,
            "message": message,
            "path": path,
            "method": method,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }

        if details is not None:
            body["details"] = details

        return MockResponse(status_code=status_code, body=body)

    @staticmethod
    def not_found_response(path: str, method: str) -> MockResponse:
        """Generate 404 response."""
        return ResponseGenerator.error_response(404, "Not Found", path, method)

    @staticmethod
    def method_not_allowed_response(
        path: str, method: str, allowed: List[str]
    ) -> MockResponse:
        """Generate 405 response."""
        return ResponseGenerator.error_response(
            405, "Method Not Allowed", path, method, {"allowed": allowed}
        )

    @staticmethod
    def invalid_json_response(details: str) -> MockResponse:
        """Generate 400 response for invalid JSON."""
        return ResponseGenerator.error_response(400, "Invalid JSON", details=details)

    @staticmethod
    def server_error_response() -> MockResponse:
        """Generate 500 response."""
        return ResponseGenerator.error_response(500, "Internal Server Error")


# =============================================================================
# Logger
# =============================================================================


class Logger:
    """Colored console logger."""

    # ANSI color codes
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    MAGENTA = "\033[95m"
    BOLD = "\033[1m"
    CYAN = "\033[96m"

    @classmethod
    def _color_for_status(cls, status: int) -> str:
        """Get color for HTTP status code."""
        if 200 <= status < 300:
            return cls.GREEN
        elif 300 <= status < 400:
            return cls.YELLOW
        elif 400 <= status < 500:
            return cls.RED
        elif 500 <= status:
            return cls.MAGENTA + cls.BOLD
        return cls.RESET

    @classmethod
    def log(
        cls,
        method: str,
        path: str,
        status: int,
        duration_ms: float,
        enabled: bool = True,
    ) -> None:
        """Log request to console."""
        if not enabled:
            return

        timestamp = datetime.now().strftime("%H:%M:%S")
        color = cls._color_for_status(status)

        # Color method
        method_color = cls.CYAN
        method_str = f"{method_color}{method.ljust(7)}{cls.RESET}"

        # Color status
        status_str = f"{color}{str(status).ljust(3)}{cls.RESET}"

        # Format output
        print(f"[{timestamp}] {method_str} {path} {status_str} {duration_ms:.0f}ms")


# =============================================================================
# Built-in Handlers
# =============================================================================


def handle_root(
    config: ServerConfig, router: Router
) -> Callable[[MockRequest], MockResponse]:
    """Handler for root endpoint - server info."""

    def handler(request: MockRequest) -> MockResponse:
        routes = []
        for route in router._routes:
            if route.pattern not in ["/", "/health", "/echo", "/delay/:ms"]:
                routes.append(f"{route.method} {route.pattern}")

        body = {
            "name": "MockAPI Server",
            "version": "1.0.0",
            "status": "running",
            "endpoints": [
                f"GET  /        - Server info",
                f"GET  /health  - Health check",
                f"ANY  /echo   - Echo request",
                f"GET  /delay/:ms - Test delay endpoint",
            ],
            "config": {
                "host": config.host,
                "port": config.port,
                "delay": config.delay,
                "cors": config.cors,
                "logging": config.log_enabled,
            },
            "message": "Welcome to MockAPI - Zero-Config Mock Server",
        }
        return MockResponse(status_code=200, body=body)

    return handler


def handle_health(config: ServerConfig) -> Callable[[MockRequest], MockResponse]:
    """Handler for health check endpoint."""

    def handler(request: MockRequest) -> MockResponse:
        body = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        return MockResponse(status_code=200, body=body)

    return handler


def handle_echo(config: ServerConfig) -> Callable[[MockRequest], MockResponse]:
    """Handler for echo endpoint - returns request as JSON."""

    def handler(request: MockRequest) -> MockResponse:
        body = {
            "request": {
                "method": request.method,
                "path": request.path,
                "path_params": request.path_params,
                "query": request.query,
                "headers": {
                    k: v
                    for k, v in request.headers.items()
                    if k.lower() not in ("host", "content-length")
                },
                "body": request.json_body
                if request.json_body is not None
                else request.body,
                "timestamp": request.timestamp.isoformat().replace("+00:00", "Z"),
            }
        }
        return MockResponse(status_code=200, body=body)

    return handler


def handle_delay(config: ServerConfig) -> Callable[[MockRequest], MockResponse]:
    """Handler for delay test endpoint."""

    def handler(request: MockRequest) -> MockResponse:
        delay_ms = config.delay
        if "ms" in request.path_params:
            try:
                delay_ms = int(request.path_params["ms"])
            except (ValueError, TypeError):
                return ResponseGenerator.error_response(
                    400,
                    "Invalid delay value",
                    path=request.path,
                    method=request.method,
                    details=f"Delay must be a valid integer, got: {request.path_params.get('ms')}",
                )

            if delay_ms < 0:
                return ResponseGenerator.error_response(
                    400,
                    "Invalid delay value",
                    path=request.path,
                    method=request.method,
                    details="Delay cannot be negative",
                )

        body = {
            "delay_applied": delay_ms,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        return MockResponse(status_code=200, body=body, delay=delay_ms)

    return handler


# =============================================================================
# Request Handler
# =============================================================================


class MockAPIHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler for MockAPI server."""

    # Class-level references (set from server)
    _config: Optional[ServerConfig] = None
    _router: Optional[Router] = None

    # Maximum body size (10MB)
    MAX_BODY_SIZE = 10 * 1024 * 1024

    # Disable logging noise
    def log_message(self, format, *args):
        pass  # We use our own logger

    def _send_response(self, response: MockResponse) -> None:
        """Send response to client."""
        # Apply delay
        delay = response.delay or self._config.delay
        if delay > 0:
            time.sleep(delay / 1000.0)

        # Send status
        self.send_response(response.status_code)

        # Prepare body bytes
        body_bytes = b""
        if response.body is not None:
            try:
                body_json = json.dumps(response.body, ensure_ascii=False, indent=None)
                body_bytes = body_json.encode("utf-8")
            except (TypeError, ValueError) as e:
                # Fallback for non-serializable bodies
                body_json = json.dumps(
                    {"error": "Response body not serializable", "detail": str(e)}
                )
                body_bytes = body_json.encode("utf-8")
        else:
            # Send null for None body
            body_bytes = b"null"

        # Set Content-Length header
        self.send_header("Content-Length", str(len(body_bytes)))

        # Set Content-Type for JSON responses
        self.send_header("Content-Type", "application/json")

        # Send custom headers
        for key, value in response.headers.items():
            self.send_header(key, value)

        # Add CORS headers if enabled
        if self._config.cors:
            self._add_cors_headers()

        self.end_headers()

        # Send body (skip for HEAD requests)
        if self.command != "HEAD" and body_bytes:
            self.wfile.write(body_bytes)

    def _add_cors_headers(self) -> None:
        """Add CORS headers to response."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, PATCH, OPTIONS"
        )
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Max-Age", "3600")

    def _parse_content_type(self) -> Tuple[Optional[str], Optional[str]]:
        """Parse Content-Type header."""
        content_type = self.headers.get("Content-Type", "")

        if ";" in content_type:
            mime_type = content_type.split(";")[0].strip()
            charset = None
            for part in content_type.split(";")[1:]:
                if "charset" in part:
                    charset = part.split("=")[1].strip()
            return mime_type, charset

        return content_type, None

    def _parse_query_params(self, path: str) -> Dict[str, Any]:
        """Parse query parameters from URL."""
        parsed = urlparse(path)
        query = parse_qs(parsed.query, keep_blank_values=True)

        # Convert to simple dict with first value
        result = {}
        for key, values in query.items():
            if len(values) == 1:
                result[key] = values[0]
            else:
                result[key] = values

        return result

    def _parse_body(self) -> Tuple[Optional[bytes], Optional[Dict], Optional[Dict]]:
        """Parse request body - JSON or form data."""
        content_length = int(self.headers.get("Content-Length", 0))

        if content_length == 0:
            return None, None, None

        # Check size limit
        if content_length > self.MAX_BODY_SIZE:
            raise ValueError(f"Request body too large: {content_length} bytes")

        body = self.rfile.read(content_length)
        mime_type, charset = self._parse_content_type()

        charset = charset or "utf-8"

        json_body = None
        form_data = None

        if mime_type == "application/json":
            try:
                json_body = json.loads(body.decode(charset))
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {str(e)}")

        elif mime_type in ("application/x-www-form-urlencoded", "multipart/form-data"):
            try:
                body_str = body.decode(charset)
                form_data = {}
                for part in body_str.split("&"):
                    if "=" in part:
                        key, value = part.split("=", 1)
                        form_data[unquote(key)] = unquote(value)
            except Exception:
                pass  # Ignore malformed form data

        return body, json_body, form_data

    def _extract_headers(self) -> Dict[str, str]:
        """Extract all request headers."""
        headers = {}
        for key, value in self.headers.items():
            headers[key] = value
        return headers

    def _handle_request(self, method: str) -> MockResponse:
        """Process incoming request."""
        start_time = time.time()

        try:
            # Parse path and query
            parsed = urlparse(self.path)
            path = parsed.path

            # Normalize path (remove double slashes)
            while "//" in path:
                path = path.replace("//", "/")

            # Get query params
            query = self._parse_query_params(self.path)

            # Get headers
            headers = self._extract_headers()

            # Parse body
            body, json_body, form_data = None, None, None
            try:
                body, json_body, form_data = self._parse_body()
            except ValueError as e:
                return ResponseGenerator.invalid_json_response(str(e))

            # Create request object
            request = MockRequest(
                method=method,
                path=path,
                path_params={},
                query=query,
                headers=headers,
                body=body,
                json_body=json_body,
                form_data=form_data,
            )

            # Match route
            handler, path_params = self._router.match(method, path)
            request.path_params = path_params

            if handler is None:
                # No route matched - return auto mock response
                response = ResponseGenerator.auto_response(request)

                # Still check for response override via request body (POST/PUT/PATCH)
                if method in ("POST", "PUT", "PATCH") and request.json_body:
                    override = request.json_body
                    if "status" in override:
                        response.status_code = override["status"]
                    if "body" in override:
                        response.body = override["body"]
                    if "headers" in override:
                        response.headers.update(override["headers"])
                    if "delay" in override:
                        response.delay = override["delay"]

                return response

            # Call handler
            response = handler(request)

            # Check for response override via request body (POST/PUT/PATCH)
            if method in ("POST", "PUT", "PATCH") and request.json_body:
                override = request.json_body

                # Override status via body
                if "status" in override:
                    response.status_code = override["status"]

                # Override body via body
                if "body" in override:
                    response.body = override["body"]

                # Override headers via body
                if "headers" in override:
                    response.headers.update(override["headers"])

                # Override delay via body
                if "delay" in override:
                    response.delay = override["delay"]

            # Check for response override via headers
            if "X-Mock-Status" in headers:
                try:
                    response.status_code = int(headers["X-Mock-Status"])
                except ValueError:
                    pass

            if "X-Mock-Delay" in headers:
                try:
                    response.delay = int(headers["X-Mock-Delay"])
                except ValueError:
                    pass

            if "X-Mock-Body" in headers:
                try:
                    response.body = json.loads(headers["X-Mock-Body"])
                except (json.JSONDecodeError, ValueError):
                    pass

            # Log request
            duration_ms = (time.time() - start_time) * 1000
            Logger.log(
                method,
                path,
                response.status_code,
                duration_ms,
                self._config.log_enabled,
            )

            return response

        except Exception as e:
            # Log error
            duration_ms = (time.time() - start_time) * 1000
            Logger.log(method, self.path, 500, duration_ms, self._config.log_enabled)

            # Return error response (never crash)
            return ResponseGenerator.server_error_response()

    def do_GET(self) -> None:
        """Handle GET requests."""
        response = self._handle_request("GET")
        self._send_response(response)

    def do_POST(self) -> None:
        """Handle POST requests."""
        response = self._handle_request("POST")
        self._send_response(response)

    def do_PUT(self) -> None:
        """Handle PUT requests."""
        response = self._handle_request("PUT")
        self._send_response(response)

    def do_DELETE(self) -> None:
        """Handle DELETE requests."""
        response = self._handle_request("DELETE")
        self._send_response(response)

    def do_PATCH(self) -> None:
        """Handle PATCH requests."""
        response = self._handle_request("PATCH")
        self._send_response(response)

    def do_OPTIONS(self) -> None:
        """Handle OPTIONS requests (CORS preflight)."""
        # Send 200 with CORS headers
        self.send_response(200)

        if self._config.cors:
            self._add_cors_headers()

        self.end_headers()


# =============================================================================
# Server
# =============================================================================


class ThreadedTCPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """Threaded HTTP server for concurrent requests."""

    daemon_threads = True
    allow_reuse_address = True


def create_server(config: ServerConfig) -> Tuple[ThreadedTCPServer, Router]:
    """Create and configure the server."""
    # Create router and register routes
    router = Router()

    # Register built-in routes
    router.add_route("GET", "/", handle_root(config, router))
    router.add_route("GET", "/health", handle_health(config))
    router.add_route("GET", "/echo", handle_echo(config))
    router.add_route("POST", "/echo", handle_echo(config))
    router.add_route("PUT", "/echo", handle_echo(config))
    router.add_route("DELETE", "/echo", handle_echo(config))
    router.add_route("PATCH", "/echo", handle_echo(config))
    router.add_route("GET", "/delay/:ms", handle_delay(config))

    # Set up handler class with config and router
    MockAPIHandler._config = config
    MockAPIHandler._router = router

    # Create server
    server = ThreadedTCPServer((config.host, config.port), MockAPIHandler)

    return server, router


def run_server(config: ServerConfig) -> None:
    """Run the mock API server."""
    if not config.validate():
        sys.exit(1)

    try:
        server, router = create_server(config)

        print(f"MockAPI Server starting on http://{config.host}:{config.port}")
        print(f"  Port: {config.port}")
        print(f"  Host: {config.host}")
        print(f"  Delay: {config.delay}ms")
        print(f"  CORS: {'enabled' if config.cors else 'disabled'}")
        print(f"  Logging: {'enabled' if config.log_enabled else 'disabled'}")
        print("")
        print("Endpoints:")
        print("  GET  /        - Server info")
        print("  GET  /health  - Health check")
        print("  ANY  /echo   - Echo request")
        print("  GET  /delay/:ms - Test delay")
        print("")
        print("Press Ctrl+C to stop")

        server.serve_forever()

    except KeyboardInterrupt:
        print("\nShutting down server...")
        sys.exit(0)
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"Error: Port {config.port} is already in use")
            print(f"Try a different port: python mockapi.py -p {config.port + 1}")
            sys.exit(1)
        else:
            print(f"Error: {e}")
            sys.exit(1)


# =============================================================================
# CLI
# =============================================================================


def parse_args() -> ServerConfig:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="MockAPI - Zero-Config Mock API Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python mockapi.py                    # Start on localhost:8080
  python mockapi.py -p 3000           # Custom port
  python mockapi.py -d 500            # Add 500ms delay
  python mockapi.py -c false          # Disable CORS
  python mockapi.py -p 3000 -d 200    # Combine options
        """,
    )

    parser.add_argument(
        "-p", "--port", type=int, default=8080, help="Server port (default: 8080)"
    )

    parser.add_argument(
        "-H",
        "--host",
        type=str,
        default="localhost",
        help="Server host (default: localhost)",
    )

    parser.add_argument(
        "-d",
        "--delay",
        type=int,
        default=0,
        help="Global response delay in milliseconds (default: 0)",
    )

    parser.add_argument(
        "-c",
        "--cors",
        type=str,
        default="true",
        choices=["true", "false"],
        help="Enable CORS (default: true)",
    )

    parser.add_argument(
        "-l",
        "--log",
        type=str,
        default="true",
        choices=["true", "false"],
        help="Enable request logging (default: true)",
    )

    args = parser.parse_args()

    return ServerConfig(
        port=args.port,
        host=args.host,
        delay=args.delay,
        cors=args.cors.lower() == "true",
        log_enabled=args.log.lower() == "true",
    )


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    config = parse_args()
    run_server(config)
