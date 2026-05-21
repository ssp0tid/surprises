"""Blocklist resolver for ad/tracker blocking."""

import re
import logging
from pathlib import Path
from dnslib import DNSRecord, RR, RCODE

from .base import BaseResolver

logger = logging.getLogger(__name__)


class BlocklistResolver(BaseResolver):
    """Filter domain queries against blocklists.

    Supports:
    - Simple domain matching (exact)
    - Wildcard matching (*.example.com)
    - Regex patterns
    - Return NXDOMAIN or 0.0.0.0
    """

    def __init__(self, next_resolver=None, blocklist_dir="/etc/dnswarden/blocklists"):
        self.next_resolver = next_resolver
        self.blocklist_dir = Path(blocklist_dir)
        self.exact_domains = set()
        self.wildcard_patterns = []
        self.regex_patterns = []
        self._load_blocklists()

    def _load_blocklists(self):
        """Load all blocklist files."""
        if not self.blocklist_dir.exists():
            logger.warning(f"Blocklist directory not found: {self.blocklist_dir}")
            return

        for f in self.blocklist_dir.glob("*.txt"):
            self._load_file(f)

    def _load_file(self, path):
        """Load a single blocklist file."""
        try:
            content = path.read_text()
        except Exception as e:
            logger.error(f"Failed to read blocklist {path}: {e}")
            return

        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            domain = parts[-1] if parts else line

            if domain.startswith("*."):
                pattern = domain[1:].replace(".", r"\.").replace("*", ".*")
                try:
                    self.wildcard_patterns.append(re.compile(pattern))
                except re.error:
                    pass
            elif domain.startswith("^") or domain.endswith("$"):
                try:
                    self.regex_patterns.append(re.compile(domain))
                except re.error:
                    pass
            else:
                self.exact_domains.add(domain.lower())

        logger.info(f"Loaded {len(self.exact_domains)} domains from {path.name}")

    def resolve(self, request, client_addr):
        """Check if domain is blocked and return NXDOMAIN or 0.0.0.0."""
        qname = str(request.q.qname).rstrip(".").lower()

        if self._is_blocked(qname):
            reply = request.reply()
            reply.add_answer(*RR.fromZone(f"{qname}. 300 A 0.0.0.0"))
            return reply

        if self.next_resolver:
            return self.next_resolver.resolve(request, client_addr)

        return None

    def can_resolve(self, request):
        """Can resolve any query."""
        return True

    def _is_blocked(self, domain):
        """Check if domain is in any blocklist."""
        if domain in self.exact_domains:
            return True

        for pattern in self.wildcard_patterns:
            if pattern.match(domain):
                return True

        for pattern in self.regex_patterns:
            if pattern.search(domain):
                return True

        return False

    def add_domain(self, domain):
        """Add domain to blocklist."""
        domain = domain.lower()
        self.exact_domains.add(domain)

    def remove_domain(self, domain):
        """Remove domain from blocklist."""
        domain = domain.lower()
        self.exact_domains.discard(domain)

    def reload(self):
        """Reload all blocklists."""
        self.exact_domains.clear()
        self.wildcard_patterns.clear()
        self.regex_patterns.clear()
        self._load_blocklists()
