"""Local zone resolver."""

import logging
from pathlib import Path
import yaml
from dnslib import DNSRecord, RR

from .base import BaseResolver

logger = logging.getLogger(__name__)


class LocalResolver(BaseResolver):
    """Resolve from local zone files.

    Format (YAML):
    zones:
      local.lan:
        - host: server
          type: A
          value: 192.168.1.10
    """

    def __init__(self, next_resolver=None, zones_config=None):
        self.next_resolver = next_resolver
        self.zones = {}
        if zones_config:
            self._load_zones(zones_config)

    def _load_zones(self, zones_config):
        """Load zones from configuration dict."""
        for zone_name, records in zones_config.items():
            self.zones[zone_name.lower()] = records

    def load_from_file(self, path):
        """Load zones from YAML file."""
        try:
            content = Path(path).read_text()
            data = yaml.safe_load(content)
            if data and "zones" in data:
                self._load_zones(data["zones"])
        except Exception as e:
            logger.error(f"Failed to load zones from {path}: {e}")

    def resolve(self, request, client_addr):
        """Check local zones first."""
        qname = str(request.q.qname).rstrip(".").lower()
        qtype = str(request.q.qtype)

        labels = qname.split(".")

        for i in range(len(labels)):
            zone = ".".join(labels[i:])
            if zone in self.zones:
                for record in self.zones[zone]:
                    if record.get("host") in qname and record.get("type") == qtype:
                        reply = request.reply()
                        reply.add_answer(
                            *RR.fromZone(
                                f"{qname}. {record.get('ttl', 300)} {record.get('type')} {record.get('value')}"
                            )
                        )
                        return reply

        if self.next_resolver:
            return self.next_resolver.resolve(request, client_addr)

        return None

    def can_resolve(self, request):
        """Can resolve if domain matches any zone."""
        qname = str(request.q.qname).rstrip(".").lower()
        return any(zone in qname for zone in self.zones)
