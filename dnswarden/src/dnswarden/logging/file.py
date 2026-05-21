"""File-based JSON logger."""

import json
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class FileLogger:
    """Log DNS queries to JSON lines file.

    Uses rotating file handler for log management.
    """

    def __init__(
        self, log_path="/var/log/dnswarden/queries.jsonl", max_bytes=100_000_000, backup_count=5
    ):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        self._logger = logging.getLogger("dnswarden_file")
        self._logger.setLevel(logging.INFO)
        self._logger.handlers.clear()

        handler = RotatingFileHandler(
            str(self.log_path), maxBytes=max_bytes, backupCount=backup_count
        )
        handler.setFormatter(logging.Formatter("%(message)s", style="%"))
        self._logger.addHandler(handler)
        self._logger.propagate = False

    def log(self, request, response, client_addr, protocol, latency_ms):
        """Log a DNS query as JSON."""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "client_ip": client_addr[0],
            "client_port": client_addr[1],
            "query_name": str(request.q.qname).rstrip("."),
            "query_type": str(request.q.qtype),
            "response_code": response.header.rcode,
            "response_size": len(response.pack()),
            "protocol": protocol,
            "latency_ms": latency_ms,
            "blocked": response.header.rcode == 3,
        }

        self._logger.info(json.dumps(entry))
