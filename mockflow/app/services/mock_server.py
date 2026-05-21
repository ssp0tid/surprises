"""Mock HTTP server implementation."""

import json
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from flask import Flask

from app.models import db, Endpoint, Log, Project
from app.services.matcher import RequestMatcher, DynamicResolver


class MockServer:
    """HTTP mock server running in a separate thread."""

    def __init__(
        self,
        host="0.0.0.0",
        port=8080,
        project_id=None,
        cors_enabled=True,
        cors_origins="*",
        flask_app=None,
    ):
        self.host = host
        self.port = port
        self.project_id = project_id
        self.cors_enabled = cors_enabled
        self.cors_origins = cors_origins
        self.flask_app = flask_app
        self.server = None
        self.thread = None
        self.running = False

    def start(self):
        """Start the mock server in a new thread."""
        if self.running:
            return

        handler = self._create_handler()
        self.server = HTTPServer((self.host, self.port), handler)
        self.running = True

        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the mock server."""
        self.running = False
        if self.server:
            self.server.shutdown()
            self.server.server_close()

    def _run_server(self):
        """Run the server in thread."""
        self.server.serve_forever()

    def _create_handler(self):
        """Create custom request handler."""
        project_id = self.project_id
        cors_enabled = self.cors_enabled
        cors_origins = self.cors_origins

        class MockRequestHandler(BaseHTTPRequestHandler):
            project_id = project_id
            cors_enabled = cors_enabled
            cors_origins = cors_origins
            matcher = RequestMatcher()

            def log_message(self, format, *args):
                pass

            def do_OPTIONS(self):
                self._send_cors_headers()
                self.send_response(204)
                self.end_headers()

            def do_GET(self):
                self._handle_request("GET")

            def do_POST(self):
                self._handle_request("POST")

            def do_PUT(self):
                self._handle_request("PUT")

            def do_PATCH(self):
                self._handle_request("PATCH")

            def do_DELETE(self):
                self._handle_request("DELETE")

            def do_HEAD(self):
                self._handle_request("HEAD")

            def _handle_request(self, method):
                start_time = time.time()

                parsed = urlparse(self.path)
                path = parsed.path
                query_params = {
                    k: v[0] if len(v) == 1 else v
                    for k, v in parse_qs(parsed.query).items()
                }

                headers = dict(self.headers)
                content_length = int(headers.get("Content-Length", 0))
                body = (
                    self.rfile.read(content_length).decode("utf-8")
                    if content_length > 0
                    else ""
                )

                endpoint, response = self._match_request(
                    method, path, headers, query_params, body
                )

                resp_status = 404
                resp_body = '{"error": "Not found"}'
                resp_headers = {"Content-Type": "application/json"}
                matched = False

                if endpoint and response:
                    matched = True
                    resp_status = response.status_code
                    resp_headers["Content-Type"] = response.content_type

                    if response.delay_ms > 0:
                        time.sleep(response.delay_ms / 1000)

                    resolver = DynamicResolver(
                        {
                            "method": method,
                            "path": path,
                            "headers": headers,
                            "query_params": query_params,
                            "body": body,
                        }
                    )
                    resolved = resolver.resolve(response.body)
                    if isinstance(resolved, dict):
                        resp_body = json.dumps(resolved)
                    else:
                        resp_body = str(resolved)

                self._send_cors_headers()
                self.send_response(resp_status)
                for key, value in resp_headers.items():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(resp_body.encode("utf-8"))

                self._log_request(
                    method,
                    path,
                    query_params,
                    headers,
                    body,
                    resp_status,
                    resp_headers,
                    resp_body,
                    matched,
                    start_time,
                )

            def _match_request(self, method, path, headers, query_params, body):
                """Match request to endpoint."""
                from flask import current_app

                try:
                    endpoints = (
                        Endpoint.query.filter_by(
                            project_id=self.project_id, method=method, enabled=True
                        )
                        .order_by(Endpoint.priority.desc())
                        .all()
                    )

                    return self.matcher.match_endpoint(
                        endpoints, method, path, headers, query_params, body
                    )
                except Exception:
                    return None, None

            def _send_cors_headers(self):
                """Send CORS headers."""
                if self.cors_enabled:
                    origins = self.cors_origins or "*"
                    self.send_header("Access-Control-Allow-Origin", origins)
                    self.send_header(
                        "Access-Control-Allow-Methods",
                        "GET, POST, PUT, PATCH, DELETE, OPTIONS",
                    )
                    self.send_header(
                        "Access-Control-Allow-Headers", "Content-Type, Authorization"
                    )

            def _log_request(
                self,
                method,
                path,
                query_params,
                headers,
                body,
                resp_status,
                resp_headers,
                resp_body,
                matched,
                start_time,
            ):
                """Log request to database."""
                from flask import current_app

                try:
                    with current_app.app_context():
                        log = Log(
                            project_id=self.project_id,
                            method=method,
                            path=path,
                            query_params=query_params,
                            request_headers=headers,
                            request_body=body,
                            response_status=resp_status,
                            response_headers=resp_headers,
                            response_body=resp_body[:1000] if resp_body else "",
                            matched=matched,
                            response_time_ms=int((time.time() - start_time) * 1000),
                        )
                        db.session.add(log)
                        db.session.commit()
                except Exception:
                    pass

        return MockRequestHandler


class MockServerManager:
    """Manages multiple mock server instances."""

    def __init__(self, app=None):
        self.app = app
        self.servers = {}

    def start(self, project_id, host="0.0.0.0", port=8080, **kwargs):
        """Start mock server for project."""
        if project_id in self.servers:
            self.stop(project_id)

        server = MockServer(
            host=host, port=port, project_id=project_id, flask_app=self.app, **kwargs
        )
        server.start()
        self.servers[project_id] = server
        return server

    def stop(self, project_id):
        """Stop mock server for project."""
        if project_id in self.servers:
            self.servers[project_id].stop()
            del self.servers[project_id]

    def stop_all(self):
        """Stop all mock servers."""
        for project_id in list(self.servers.keys()):
            self.stop(project_id)

    def get_status(self, project_id):
        """Get server status."""
        if project_id in self.servers:
            server = self.servers[project_id]
            return {"running": server.running, "host": server.host, "port": server.port}
        return {"running": False}
