"""Upstream DNS resolver."""

import socket
import logging
from dnslib import DNSRecord, QTYPE, RCODE

from .base import BaseResolver

logger = logging.getLogger(__name__)


class UpstreamResolver(BaseResolver):
    """Forward queries to upstream DNS servers.

    Supports multiple upstream servers with failover.
    """

    def __init__(self, upstreams=None):
        self.upstreams = upstreams or [
            ("1.1.1.1", 53),
            ("1.0.0.1", 53),
            ("8.8.8.8", 53),
        ]
        self.current = 0

    def resolve(self, request, client_addr):
        """Forward to upstream with failover."""
        for upstream in self.upstreams:
            try:
                response = self._forward(request, upstream)
                if response and response.header.rcode == RCODE.NOERROR:
                    return response
            except Exception as e:
                logger.debug(f"Upstream {upstream} failed: {e}")
                continue

        reply = request.reply()
        reply.header.rcode = RCODE.SERVFAIL
        return reply

    def _forward(self, request, upstream):
        """Send query to upstream."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5.0)

        try:
            data = request.pack()
            sock.sendto(data, upstream)
            response_data, _ = sock.recvfrom(4096)
            return DNSRecord.parse(response_data)
        finally:
            sock.close()

    def can_resolve(self, request):
        """Can resolve any query."""
        return True
