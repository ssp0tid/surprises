"""Tests for resolver modules."""

import pytest
from dnslib import DNSRecord, RR

from dnswarden.resolver.base import BaseResolver, ChainedResolver
from dnswarden.resolver.upstream import UpstreamResolver


class TestBaseResolver:
    def test_interface(self):
        class DummyResolver(BaseResolver):
            def resolve(self, request, client_addr):
                return request.reply()

        resolver = DummyResolver()
        request = DNSRecord(q=DNSRecord.question("test.com"))
        response = resolver.resolve(request, ("127.0.0.1", 12345))
        assert response is not None


class TestChainedResolver:
    def test_chain_empty(self):
        chain = ChainedResolver()
        assert chain.resolve(None, None) is None

    def test_chain_single(self):
        class FirstResolver(BaseResolver):
            def resolve(self, request, client_addr):
                return request.reply()

        chain = ChainedResolver(FirstResolver())
        request = DNSRecord(q=DNSRecord.question("test.com"))
        response = chain.resolve(request, ("127.0.0.1", 12345))
        assert response is not None


class TestUpstreamResolver:
    def test_upstream_config(self):
        resolver = UpstreamResolver(upstreams=[("1.1.1.1", 53), ("8.8.8.8", 53)])
        assert len(resolver.upstreams) == 2
        assert resolver.upstreams[0] == ("1.1.1.1", 53)


class TestDomainUtils:
    def test_normalize_domain(self):
        from dnswarden.utils.domain import normalize_domain

        assert normalize_domain("EXAMPLE.COM") == "example.com"
        assert normalize_domain("example.com.") == "example.com"
        assert normalize_domain("  Example.Com  ") == "example.com"

    def test_is_valid_domain(self):
        from dnswarden.utils.domain import is_valid_domain

        assert is_valid_domain("example.com") is True
        assert is_valid_domain("sub.example.com") is True
        assert is_valid_domain("") is False
        assert is_valid_domain("-invalid.com") is False


class TestLRUCache:
    def test_cache_operations(self):
        from dnswarden.utils.cache import LRUCache

        cache = LRUCache(max_size=3)

        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)

        assert cache.get("a") == 1
        assert cache.get("b") == 2
        assert cache.get("c") == 3
        assert cache.get("d") is None

    def test_cache_eviction(self):
        from dnswarden.utils.cache import LRUCache

        cache = LRUCache(max_size=2)

        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)

        assert cache.get("a") is None
        assert cache.get("c") == 3
