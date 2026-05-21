"""IP allowlist for trusted clients."""

import ipaddress
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class IPAllowlist:
    """Allowlist for trusted client IPs."""

    def __init__(self, allowlist_file=None):
        self.networks = []
        self._load(allowlist_file or "/etc/dnswarden/allowlist.txt")

    def _load(self, path):
        """Load allowlist from file."""
        p = Path(path)
        if not p.exists():
            return

        try:
            content = p.read_text()
        except Exception as e:
            logger.error(f"Failed to read allowlist: {e}")
            return

        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            try:
                network = ipaddress.ip_network(line, strict=False)
                self.networks.append(network)
            except ValueError:
                pass

        logger.info(f"Loaded allowlist with {len(self.networks)} networks")

    def is_allowed(self, client_ip):
        """Check if IP is allowlisted."""
        if not self.networks:
            return True

        try:
            ip = ipaddress.ip_address(client_ip)
            for network in self.networks:
                if ip in network:
                    return True
        except ValueError:
            pass

        return False

    def reload(self):
        """Reload allowlist from file."""
        pass
