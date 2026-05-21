"""Tests for blocklist resolver."""

import pytest
import tempfile
from pathlib import Path
from dnslib import DNSRecord

from dnswarden.resolver.blocklist import BlocklistResolver
from dnswarden.resolver.base import BaseResolver
from dnswarden.security.allowlist import IPAllowlist


class TestBlocklistResolver:
    def test_exact_match(self):
        resolver = BlocklistResolver(blocklist_dir="/nonexistent")
        resolver.exact_domains = {"ads.example.com", "tracker.example.com"}

        assert resolver._is_blocked("ads.example.com") is True
        assert resolver._is_blocked("tracker.example.com") is True
        assert resolver._is_blocked("example.com") is False

    def test_add_remove_domain(self):
        resolver = BlocklistResolver(blocklist_dir="/nonexistent")

        resolver.add_domain("malware.example.com")
        assert resolver._is_blocked("malware.example.com") is True

        resolver.remove_domain("malware.example.com")
        assert resolver._is_blocked("malware.example.com") is False

    def test_wildcard_matching(self):
        resolver = BlocklistResolver(blocklist_dir="/nonexistent")
        resolver.wildcard_patterns.append(__import__("re").compile(r"ads\..*"))

        assert resolver._is_blocked("ads.example.com") is True
        assert resolver._is_blocked("ads.google.com") is True
        assert resolver._is_blocked("notads.example.com") is False


class TestRateLimiter:
    def test_rate_limiting(self):
        from dnswarden.security.ratelimit import RateLimiter

        limiter = RateLimiter(queries_per_second=10, burst=10)

        for _ in range(10):
            assert limiter.allow("192.168.1.1") is True

        assert limiter.allow("192.168.1.1") is False

    def test_different_ips(self):
        from dnswarden.security.ratelimit import RateLimiter

        limiter = RateLimiter(queries_per_second=10, burst=10)

        assert limiter.allow("192.168.1.1") is True
        assert limiter.allow("192.168.1.2") is True


class TestIPAllowlist:
    def test_no_allowlist(self):
        from dnswarden.security.allowlist import IPAllowlist

        allowlist = IPAllowlist(allowlist_file="/nonexistent")

        assert allowlist.is_allowed("192.168.1.100") is True

    def test_allowlist_match(self):
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("192.168.1.0/24\n")
            f.write("10.0.0.0/8\n")
            path = f.name

        try:
            allowlist = IPAllowlist(allowlist_file=path)
            assert allowlist.is_allowed("192.168.1.50") is True
            assert allowlist.is_allowed("10.1.2.3") is True
            assert allowlist.is_allowed("172.16.0.1") is False
        finally:
            os.unlink(path)


class TestLocalResolver:
    def test_local_zone_resolution(self):
        from dnswarden.resolver.local import LocalResolver

        zones = {
            "local.lan": [{"host": "server", "type": "A", "value": "192.168.1.10", "ttl": 300}]
        }
        resolver = LocalResolver(zones_config=zones)
        assert len(resolver.zones) == 1
