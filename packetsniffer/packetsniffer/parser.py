"""Protocol dissection and parsing module."""

from __future__ import annotations

from scapy.layers.dns import DNS
from scapy.layers.inet import ICMP, IP, TCP, UDP
from scapy.layers.l2 import ARP, Ether
from scapy.packet import Packet


def dissect_packet(pkt: Packet) -> dict:
    """
    Dissect packet into protocol layers.

    Args:
        pkt: Scapy packet object

    Returns:
        Dictionary containing parsed protocol data
    """
    result: dict = {"timestamp": float(pkt.time)}

    # Ether layer
    if Ether in pkt:
        result["eth"] = {
            "src": pkt[Ether].src,
            "dst": pkt[Ether].dst,
            "type": hex(pkt[Ether].type),
        }

    # IP layer
    if IP in pkt:
        result["ip"] = {
            "src": pkt[IP].src,
            "dst": pkt[IP].dst,
            "proto": pkt[IP].proto,
            "ttl": pkt[IP].ttl,
            "len": pkt[IP].len,
            "id": pkt[IP].id,
        }

    # Transport layer
    if TCP in pkt:
        result["tcp"] = {
            "sport": pkt[TCP].sport,
            "dport": pkt[TCP].dport,
            "flags": str(pkt[TCP].flags),
            "seq": pkt[TCP].seq,
            "ack": pkt[TCP].ack,
            "window": pkt[TCP].window,
        }
    elif UDP in pkt:
        result["udp"] = {
            "sport": pkt[UDP].sport,
            "dport": pkt[UDP].dport,
            "len": pkt[UDP].len,
        }
    elif ICMP in pkt:
        result["icmp"] = {
            "type": pkt[ICMP].type,
            "code": pkt[ICMP].code,
        }

    # Application layer - DNS
    if DNS in pkt and pkt[DNS].qr is not None:
        result["dns"] = parse_dns(pkt[DNS])

    # Packet length
    result["length"] = len(pkt)

    return result


def parse_dns(dns_layer: DNS) -> dict:
    """Parse DNS layer."""
    result: dict = {}

    if dns_layer.qr:
        result["qr"] = "response"
    else:
        result["qr"] = "query"

    if dns_layer.qd:
        result["query"] = dns_layer.qd.qname.decode() if dns_layer.qd.qname else ""

    if dns_layer.an:
        result["answers"] = []
        for ans in dns_layer.an:
            if hasattr(ans, "rdata"):
                result["answers"].append(str(ans.rdata))

    return result


def parse_tcp_flags(flags) -> str:
    """
    Convert TCP flags to string representation.

    Args:
        flags: Scapy TCP flags object

    Returns:
        Comma-separated flag names
    """
    flag_map = {
        "F": "FIN",
        "S": "SYN",
        "R": "RST",
        "P": "PSH",
        "A": "ACK",
        "U": "URG",
        "E": "ECE",
        "C": "CWR",
    }

    flags_str = str(flags)
    return ",".join(f for f, v in flag_map.items() if f in flags_str)


def get_protocol_name(proto: int) -> str:
    """Get protocol name from IP protocol number."""
    proto_map = {
        1: "icmp",
        6: "tcp",
        17: "udp",
        47: "gre",
        50: "esp",
        51: "ah",
        89: "ospf",
    }
    return proto_map.get(proto, f"proto-{proto}")
