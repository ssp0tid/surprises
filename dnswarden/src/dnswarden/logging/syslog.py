"""Syslog-based logger."""

import logging
import syslog
import re
from pathlib import Path

logger = logging.getLogger(__name__)


class SyslogLogger:
    """Log DNS queries to syslog.

    Uses syslog for centralized logging.
    """

    def __init__(self, ident="dnswarden", facility=syslog.LOG_DAEMON):
        self.ident = ident
        self.facility = facility
        self._open = False

    def _ensure_open(self):
        """Ensure syslog is open."""
        if not self._open:
            syslog.openlog(self.ident, 0, self.facility)
            self._open = True

    def log(self, request, response, client_addr, protocol, latency_ms):
        """Log a DNS query to syslog."""
        self._ensure_open()

        qname = str(request.q.qname).rstrip(".")
        qtype = str(request.q.qtype)
        rcode = response.header.rcode
        blocked = rcode == 3

        message = (
            f"query: {qname} type={qtype} "
            f"client={client_addr[0]}:{client_addr[1]} "
            f"rcode={rcode} protocol={protocol} "
            f"latency={latency_ms:.2f}ms blocked={blocked}"
        )

        syslog.syslog(self.facility | syslog.LOG_INFO, message)

    def close(self):
        """Close syslog."""
        if self._open:
            syslog.closelog()
            self._open = False


class QueryLogger:
    """Composite logger that supports multiple backends."""

    def __init__(self, backends=None):
        self.backends = backends or []

    def add_backend(self, backend):
        """Add logging backend."""
        self.backends.append(backend)

    def log(self, request, response, client_addr, protocol, latency_ms):
        """Log to all backends."""
        for backend in self.backends:
            try:
                backend.log(request, response, client_addr, protocol, latency_ms)
            except Exception as e:
                logger.error(f"Logging error: {e}")

    def close(self):
        """Close all backends."""
        for backend in self.backends:
            if hasattr(backend, "close"):
                backend.close()
