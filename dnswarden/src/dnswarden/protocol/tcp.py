"""DNS over TCP protocol handler."""

import socket
import struct
import logging
import threading
from dnslib import DNSRecord

logger = logging.getLogger(__name__)


class TCPHandler:
    """Handle DNS over TCP.

    TCP requires length prefix (2 bytes) before DNS packet per RFC 7766.
    """

    def __init__(self, resolver, bind_address="0.0.0.0", port=53):
        self.resolver = resolver
        self.bind_address = bind_address
        self.port = port
        self.socket = None
        self._running = False
        self._threads = []

    def start(self):
        """Start TCP DNS server."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.socket.bind((self.bind_address, self.port))
            self.socket.listen(5)
            logger.info(f"TCP DNS server listening on {self.bind_address}:{self.port}")
        except PermissionError:
            logger.error("Port 53 requires root privileges")
            raise

    def handle_forever(self):
        """Accept and handle connections."""
        self._running = True
        while self._running:
            try:
                client_socket, client_addr = self.socket.accept()
                thread = threading.Thread(
                    target=self._handle_client, args=(client_socket, client_addr), daemon=True
                )
                thread.start()
                self._threads.append(thread)
            except Exception as e:
                if self._running:
                    logger.error(f"TCP accept error: {e}")

    def _handle_client(self, client_socket, client_addr):
        """Handle single TCP client connection."""
        try:
            length_data = self._recv_exact(client_socket, 2)
            if not length_data:
                return

            length = struct.unpack("!H", length_data)[0]
            if length > 65535:
                logger.warning(f"TCP packet too large: {length}")
                return

            data = self._recv_exact(client_socket, length)
            if not data:
                return

            request = DNSRecord.parse(data)
            response = self.resolver.resolve(request, client_addr)

            if response:
                response_data = response.pack()
                response_length = struct.pack("!H", len(response_data))
                client_socket.sendall(response_length + response_data)
        except Exception as e:
            logger.error(f"TCP client error from {client_addr}: {e}")
        finally:
            client_socket.close()

    def _recv_exact(self, sock, n):
        """Receive exactly n bytes."""
        data = b""
        while len(data) < n:
            chunk = sock.recv(n - len(data))
            if not chunk:
                return None
            data += chunk
        return data

    def stop(self):
        """Stop server gracefully."""
        self._running = False
        if self.socket:
            self.socket.close()
        for thread in self._threads:
            thread.join(timeout=1.0)
        logger.info("TCP DNS server stopped")
