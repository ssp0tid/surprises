"""BPF filter parser and validator."""

from __future__ import annotations

import re


def parse_filter(filter_str: str | None) -> str | None:
    """
    Validate and return BPF filter string.

    Args:
        filter_str: Raw filter string from user

    Returns:
        Validated filter string or None
    """
    if not filter_str:
        return None

    # Basic validation - check for obviously invalid characters
    # BPF filters can contain: alphanumeric, operators, and common keywords
    if not re.match(r"^[\w\s\.\:\/\-\(\)\[\]\=]+$", filter_str):
        raise ValueError(f"Invalid characters in filter: {filter_str}")

    return filter_str


def build_filter(
    protocol: str | None = None,
    port: int | None = None,
    host: str | None = None,
    src_host: str | None = None,
    dst_host: str | None = None,
    net: str | None = None,
) -> str | None:
    """
    Build BPF filter from components.

    Args:
        protocol: Protocol (tcp, udp, icmp, arp)
        port: Port number
        host: Any-direction host
        src_host: Source host
        dst_host: Destination host
        net: Network (CIDR notation)

    Returns:
        BPF filter string
    """
    parts: list[str] = []

    if protocol:
        parts.append(protocol.lower())

    if port:
        if protocol in ("tcp", "udp"):
            parts.append(f"port {port}")
        else:
            parts.append(f"port {port}")

    if src_host:
        parts.append(f"src host {src_host}")

    if dst_host:
        parts.append(f"dst host {dst_host}")

    if host and not src_host and not dst_host:
        parts.append(f"host {host}")

    if net:
        parts.append(f"net {net}")

    return " ".join(parts) if parts else None


SUPPORTED_FILTERS = {
    "tcp": "Match TCP packets",
    "udp": "Match UDP packets",
    "icmp": "Match ICMP packets",
    "arp": "Match ARP packets",
    "tcp port <port>": "Match TCP packets on specific port",
    "udp port <port>": "Match UDP packets on specific port",
    "host <ip>": "Match packets to/from specific IP",
    "src host <ip>": "Match packets from specific source IP",
    "dst host <ip>": "Match packets to specific destination IP",
    "net <cidr>": "Match packets in specific subnet",
    "tcp[tcpflags] & tcp-syn != 0": "Match TCP SYN packets",
    "tcp[tcpflags] & tcp-ack != 0": "Match TCP ACK packets",
}


def list_supported_filters() -> dict:
    """Return dictionary of supported filter types."""
    return SUPPORTED_FILTERS.copy()
