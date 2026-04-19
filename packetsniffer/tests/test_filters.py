"""Tests for filters module."""

import pytest
from packetsniffer.filters import parse_filter, build_filter, list_supported_filters


class TestParseFilter:
    def test_parse_filter_none(self):
        assert parse_filter(None) is None

    def test_parse_filter_empty(self):
        assert parse_filter("") is None

    def test_parse_filter_valid(self):
        assert parse_filter("tcp port 80") == "tcp port 80"

    def test_parse_filter_invalid_chars(self):
        with pytest.raises(ValueError):
            parse_filter("tcp; rm -rf /")


class TestBuildFilter:
    def test_build_filter_protocol(self):
        result = build_filter(protocol="tcp")
        assert result == "tcp"

    def test_build_filter_protocol_port(self):
        result = build_filter(protocol="tcp", port=80)
        assert result == "tcp port 80"

    def test_build_filter_host(self):
        result = build_filter(host="192.168.1.1")
        assert result == "host 192.168.1.1"

    def test_build_filter_src_host(self):
        result = build_filter(src_host="10.0.0.1")
        assert result == "src host 10.0.0.1"

    def test_build_filter_net(self):
        result = build_filter(net="192.168.1.0/24")
        assert result == "net 192.168.1.0/24"

    def test_build_filter_combined(self):
        result = build_filter(protocol="tcp", port=443, host="1.2.3.4")
        assert "tcp" in result
        assert "port 443" in result
        assert "host 1.2.3.4" in result


class TestListSupportedFilters:
    def test_list_supported_filters(self):
        filters = list_supported_filters()
        assert "tcp" in filters
        assert "udp" in filters
        assert "icmp" in filters
        assert "tcp port <port>" in filters
