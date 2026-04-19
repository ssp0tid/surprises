"""Tests for export module."""

import json
import csv
import tempfile
from pathlib import Path

import pytest
from packetsniffer.export import export_json, export_csv, flatten_packet


class TestExportJson:
    def test_export_json(self):
        packets = [
            {"timestamp": 1234567890.0, "ip": {"src": "192.168.1.1"}},
            {"timestamp": 1234567891.0, "ip": {"src": "192.168.1.2"}},
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            path = Path(f.name)

        try:
            export_json(packets, path)

            with open(path) as f:
                result = json.load(f)

            assert len(result) == 2
            assert result[0]["ip"]["src"] == "192.168.1.1"
        finally:
            path.unlink()


class TestExportCsv:
    def test_export_csv(self):
        packets = [
            {"timestamp": 1234567890.0, "ip": {"src": "192.168.1.1", "dst": "192.168.1.2"}},
            {"timestamp": 1234567891.0, "ip": {"src": "192.168.1.3", "dst": "192.168.1.4"}},
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            path = Path(f.name)

        try:
            export_csv(packets, path)

            with open(path) as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 2
            assert rows[0]["ip_src"] == "192.168.1.1"
        finally:
            path.unlink()

    def test_export_csv_empty(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            path = Path(f.name)

        try:
            export_csv([], path)
            assert not path.exists() or path.stat().st_size == 0
        finally:
            if path.exists():
                path.unlink()


class TestFlattenPacket:
    def test_flatten_packet_eth_ip_tcp(self):
        pkt = {
            "timestamp": 1234567890.0,
            "eth": {"src": "00:11:22:33:44:55", "dst": "aa:bb:cc:dd:ee:ff", "type": "0x800"},
            "ip": {"src": "192.168.1.1", "dst": "192.168.1.2", "proto": 6, "ttl": 64},
            "tcp": {"sport": 8080, "dport": 80, "flags": "S", "seq": 1000, "ack": 0},
        }

        result = flatten_packet(pkt)

        assert result["timestamp"] == "1234567890.0"
        assert result["eth_src"] == "00:11:22:33:44:55"
        assert result["ip_src"] == "192.168.1.1"
        assert result["tcp_sport"] == "8080"

    def test_flatten_packet_udp(self):
        pkt = {
            "timestamp": 1234567890.0,
            "udp": {"sport": 53, "dport": 53},
        }

        result = flatten_packet(pkt)

        assert result["udp_sport"] == "53"
        assert result["udp_dport"] == "53"

    def test_flatten_packet_icmp(self):
        pkt = {
            "timestamp": 1234567890.0,
            "icmp": {"type": 8, "code": 0},
        }

        result = flatten_packet(pkt)

        assert result["icmp_type"] == "8"
        assert result["icmp_code"] == "0"
