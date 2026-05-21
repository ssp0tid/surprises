"""Admin HTTP API server."""

import json
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from threading import Thread

from .routes import APIError, handle_error, success_response, validate_domain, validate_limit

logger = logging.getLogger(__name__)


class DNSWardenAPIHandler(BaseHTTPRequestHandler):
    """HTTP API handler for DNSWarden admin interface."""

    def do_GET(self):
        try:
            if self.path == "/api/status":
                self._handle_status()
            elif self.path.startswith("/api/queries"):
                self._handle_queries()
            elif self.path == "/api/blockstats":
                self._handle_blockstats()
            elif self.path == "/api/config":
                self._handle_config()
            else:
                raise APIError("NOT_FOUND", "Endpoint not found", 404)
        except APIError as e:
            self._send_error(e)

    def do_POST(self):
        try:
            if self.path == "/api/blocklist/reload":
                self._handle_reload_blocklist()
            elif self.path == "/api/domains/add":
                self._handle_add_domain()
            else:
                raise APIError("NOT_FOUND", "Endpoint not found", 404)
        except APIError as e:
            self._send_error(e)

    def do_DELETE(self):
        try:
            if self.path.startswith("/api/domains/"):
                domain = self.path.split("/api/domains/")[1]
                self._handle_remove_domain(domain)
            else:
                raise APIError("NOT_FOUND", "Endpoint not found", 404)
        except APIError as e:
            self._send_error(e)

    def log_message(self, format, *args):
        logger.debug("%s - %s", self.address_string(), format % args)

    def _handle_status(self):
        data = {"version": "0.1.0", "uptime": "N/A", "queries_processed": 0, "blocked_count": 0}
        self._send_json(success_response(data))

    def _handle_queries(self):
        limit = validate_limit(self._get_query_param("limit"))
        filters = {}
        if self._get_query_param("query_name"):
            filters["query_name"] = self._get_query_param("query_name")
        if self._get_query_param("client_ip"):
            filters["client_ip"] = self._get_query_param("client_ip")

        queries = []
        self._send_json(success_response({"queries": queries, "count": 0}))

    def _handle_blockstats(self):
        data = {"total_queries": 0, "blocked_queries": 0, "unique_domains": 0, "unique_clients": 0}
        self._send_json(success_response(data))

    def _handle_config(self):
        data = {"server": {}, "upstream": [], "blocklists": {}, "logging": {}}
        self._send_json(success_response(data))

    def _handle_reload_blocklist(self):
        self._send_json(success_response({"message": "Blocklists reloaded"}))

    def _handle_add_domain(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode()
        data = json.loads(body)
        domain = validate_domain(data.get("domain"))
        self._send_json(success_response({"message": f"Domain {domain} added"}))

    def _handle_remove_domain(self, domain):
        domain = validate_domain(domain)
        self._send_json(success_response({"message": f"Domain {domain} removed"}))

    def _get_query_param(self, name):
        if "?" not in self.path:
            return None
        query = self.path.split("?")[1]
        for param in query.split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                if key == name:
                    return value
        return None

    def _send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_error(self, error):
        self.send_response(error.status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(error.to_dict()).encode())


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Threaded HTTP server for concurrent requests."""

    daemon_threads = True


class APIServer:
    """Admin API server."""

    def __init__(self, bind_address="127.0.0.1", port=8080):
        self.bind_address = bind_address
        self.port = port
        self.server = None
        self.thread = None

    def start(self):
        self.server = ThreadedHTTPServer((self.bind_address, self.port), DNSWardenAPIHandler)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        logger.info(f"API server listening on {self.bind_address}:{self.port}")

    def stop(self):
        if self.server:
            self.server.shutdown()
            logger.info("API server stopped")
