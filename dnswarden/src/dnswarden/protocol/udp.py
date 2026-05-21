"""DNS over UDP protocol handler."""

import socket
import logging
from dnslib import DNSRecord

logger = logging.getLogger(__name__)


class UDPHandler:
    """Handle DNS over UDP."""

    def __init__(self, resolver, bind_address="0.0.0.0", port=53):
        self.resolver = resolver
        self.bind_address = bind_address
        self.port = port
        self.socket = None
        self._running = False

    def start(self):
        """Start UDP DNS server."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.socket.bind((self.bind_address, self.port))
            logger.info(f"UDP DNS server listening on {self.bind_address}:{self.port}")
        except PermissionError:
            logger.error("Port 53 requires root privileges")
            raise

    def handle_forever(self):
        """Process queries indefinitely."""
        self._running = True
        while self._running:
            try:
                data, client_addr = self.socket.recvfrom(4096)
                if not data:
                    continue

                request = DNSRecord.parse(data)
                response = self.resolver.resolve(request, client_addr)

                if response:
                    self.socket.sendto(response.pack(), client_addr)
            except Exception as e:
                logger.error(f"UDP handling error: {e}")

    def stop(self):
        """Stop server gracefully."""
        self._running = False
        if self.socket:
            self.socket.close()
            logger.info("UDP DNS server stopped")


class DNSResolver:
    """DNS resolver interface for protocol handlers."""

    def __init__(self):
        self.resolver = None

    def resolve(self, request, client_addr):
        """Resolve DNS query."""
        if self.resolver:
            return self.resolver.resolve(request, client_addr)
        return None

    def set_resolver(self, resolver):
        """Set the actual resolver."""
        self.resolver = resolver
