"""Tests for parser module."""

import pytest
from unittest.mock import Mock, MagicMock
from packetsniffer.parser import dissect_packet, parse_tcp_flags, get_protocol_name


class TestDissectPacket:
    def test_dissect_packet_with_ip_tcp(self):
        pkt = Mock()
        pkt.time = 1234567890.0
        pkt.__contains__ = lambda self, layer: layer in ["Ether", "IP", "TCP"]

        ether_layer = Mock()
        ether_layer.src = "00:11:22:33:44:55"
        ether_layer.dst = "aa:bb:cc:dd:ee:ff"
        ether_layer.type = 0x0800

        ip_layer = Mock()
        ip_layer.src = "192.168.1.1"
        ip_layer.dst = "192.168.1.2"
        ip_layer.proto = 6
        ip_layer.ttl = 64
        ip_layer.len = 100
        ip_layer.id = 1234

        tcp_layer = Mock()
        tcp_layer.sport = 8080
        tcp_layer.dport = 80
        tcp_layer.flags = "S"
        tcp_layer.seq = 1000
        tcp_layer.ack = 0
        tcp_layer.window = 65535

        pkt.getlayer = lambda layer: {
            "Ether": ether_layer,
            "IP": ip_layer,
            "TCP": tcp_layer,
        }.get(layer)

        from scapy.layers.l2 import Ether
        from scapy.layers.inet import IP, TCP

        result = dissect_packet.__wrapped__(pkt)

        assert result["timestamp"] == 1234567890.0
        assert result["ip"]["src"] == "192.168.1.1"
        assert result["tcp"]["dport"] == 80


class TestParseTcpFlags:
    def test_parse_tcp_flags_syn(self):
        flags = Mock()
        flags.__str__ = lambda self: "S"

        result = parse_tcp_flags(flags)
        assert "SYN" in result

    def test_parse_tcp_flags_ack(self):
        flags = Mock()
        flags.__str__ = lambda self: "A"

        result = parse_tcp_flags(flags)
        assert "ACK" in result


class TestGetProtocolName:
    def test_get_protocol_name_tcp(self):
        assert get_protocol_name(6) == "tcp"

    def test_get_protocol_name_udp(self):
        assert get_protocol_name(17) == "udp"

    def test_get_protocol_name_icmp(self):
        assert get_protocol_name(1) == "icmp"

    def test_get_protocol_name_unknown(self):
        assert get_protocol_name(255) == "proto-255"
