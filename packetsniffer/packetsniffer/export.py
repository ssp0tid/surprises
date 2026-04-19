"""JSON and CSV export module."""

from __future__ import annotations

import csv
import json
from pathlib import Path


def export_json(packets: list[dict], output: Path) -> None:
    """Export packets to JSON file."""
    with open(output, "w") as f:
        json.dump(packets, f, indent=2, default=str)


def export_csv(packets: list[dict], output: Path) -> None:
    """Export packets to CSV file (flattened)."""
    if not packets:
        return

    flattened = [flatten_packet(p) for p in packets]

    keys: set = set()
    for p in flattened:
        keys.update(p.keys())

    with open(output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=sorted(keys))
        writer.writeheader()
        writer.writerows(flattened)


def flatten_packet(pkt: dict) -> dict:
    """Flatten nested packet dict for CSV export."""
    result: dict = {"timestamp": str(pkt.get("timestamp", ""))}

    if eth := pkt.get("eth"):
        result["eth_src"] = eth.get("src", "")
        result["eth_dst"] = eth.get("dst", "")
        result["eth_type"] = eth.get("type", "")

    if ip := pkt.get("ip"):
        result["ip_src"] = ip.get("src", "")
        result["ip_dst"] = ip.get("dst", "")
        result["ip_proto"] = ip.get("proto", "")
        result["ip_ttl"] = ip.get("ttl", "")
        result["ip_len"] = ip.get("len", "")

    if tcp := pkt.get("tcp"):
        result["tcp_sport"] = tcp.get("sport", "")
        result["tcp_dport"] = tcp.get("dport", "")
        result["tcp_flags"] = tcp.get("flags", "")
        result["tcp_seq"] = tcp.get("seq", "")
        result["tcp_ack"] = tcp.get("ack", "")

    if udp := pkt.get("udp"):
        result["udp_sport"] = udp.get("sport", "")
        result["udp_dport"] = udp.get("dport", "")

    if icmp := pkt.get("icmp"):
        result["icmp_type"] = icmp.get("type", "")
        result["icmp_code"] = icmp.get("code", "")

    if dns := pkt.get("dns"):
        result["dns_qr"] = dns.get("qr", "")
        result["dns_query"] = dns.get("query", "")

    result["length"] = pkt.get("length", "")

    return result
