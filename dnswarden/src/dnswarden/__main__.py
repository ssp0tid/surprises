"""CLI entry point."""

import sys
import argparse
import logging
import signal
import time
from pathlib import Path

from . import __version__
from .config import Config
from .protocol.udp import UDPHandler
from .protocol.tcp import TCPHandler
from .resolver.blocklist import BlocklistResolver
from .resolver.local import LocalResolver
from .resolver.upstream import UpstreamResolver
from .logging.sqlite import SQLiteLogger
from .logging.file import FileLogger
from .logging.syslog import QueryLogger
from .security.ratelimit import RateLimiter
from .security.allowlist import IPAllowlist
from .api.server import APIServer

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DNSWarden:
    """Main DNSWarden server."""

    def __init__(self, config_path=None):
        self.config = Config(config_path)
        self.udp_handler = None
        self.tcp_handler = None
        self.api_server = None
        self.logger = None
        self.rate_limiter = None
        self.allowlist = None
        self._running = False

    def setup(self):
        """Setup all components."""
        config = self.config

        upstream = UpstreamResolver(config.get_upstreams())
        local = LocalResolver(next_resolver=upstream)

        blocklist_dir = config.get_blocklist_dir()
        blocklist = BlocklistResolver(next_resolver=local, blocklist_dir=blocklist_dir)

        self.blocklist_resolver = blocklist

        if config.get("logging.enabled", True):
            backend = config.get("logging.backend", "sqlite")
            if backend == "sqlite":
                self.logger = SQLiteLogger(config.get_log_path())
            elif backend == "file":
                self.logger = FileLogger()
            else:
                self.logger = QueryLogger()

        if config.get("security.rate_limit.enabled", True):
            self.rate_limiter = RateLimiter(
                queries_per_second=config.get("security.rate_limit.queries_per_second", 100),
                burst=config.get("security.rate_limit.burst", 200),
            )

        if config.get("security.allowlist.enabled", False):
            self.allowlist = IPAllowlist(config.get("security.allowlist.file"))

    def start(self):
        """Start DNS server."""
        config = self.config
        bind = config.get("server.bind_address", "0.0.0.0")
        port = config.get("server.port", 53)

        self.udp_handler = UDPHandler(self.blocklist_resolver, bind, port)
        self.tcp_handler = TCPHandler(self.blocklist_resolver, bind, port)

        if config.get("admin.enabled", True):
            self.api_server = APIServer(
                config.get("admin.bind_address", "127.0.0.1"), config.get("admin.port", 8080)
            )
            self.api_server.start()

        logger.info("DNSWarden starting...")
        self._running = True

        try:
            self.udp_handler.start()
            self.tcp_handler.start()
        except PermissionError:
            logger.error("Port 53 requires root. Try running with sudo.")
            sys.exit(1)

        import threading

        udp_thread = threading.Thread(target=self.udp_handler.handle_forever, daemon=True)
        tcp_thread = threading.Thread(target=self.tcp_handler.handle_forever, daemon=True)
        udp_thread.start()
        tcp_thread.start()

        logger.info("DNSWarden running")

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        while self._running:
            time.sleep(1)

    def _signal_handler(self, signum, frame):
        logger.info("Shutting down...")
        self._running = False
        self.stop()

    def stop(self):
        """Stop DNS server."""
        if self.udp_handler:
            self.udp_handler.stop()
        if self.tcp_handler:
            self.tcp_handler.stop()
        if self.api_server:
            self.api_server.stop()
        if self.logger:
            self.logger.close()
        logger.info("DNSWarden stopped")


def main():
    """CLI main entry point."""
    parser = argparse.ArgumentParser(prog="dnswarden")
    parser.add_argument("--version", action="version", version=f"dnswarden {__version__}")
    parser.add_argument("--config", help="Path to config file")
    parser.add_argument("command", nargs="?", default="start", choices=["start", "stop", "reload"])

    args = parser.parse_args()

    if args.command == "start":
        server = DNSWarden(args.config)
        server.setup()
        server.start()
    else:
        logger.info(f"Command {args.command} not implemented")


if __name__ == "__main__":
    main()
