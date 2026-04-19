"""Statistics tracking module."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass
class PacketStats:
    """Thread-safe packet statistics tracker."""

    tcp: int = 0
    udp: int = 0
    icmp: int = 0
    arp: int = 0
    dns: int = 0
    other: int = 0
    total_bytes: int = 0
    _lock: Lock = field(default_factory=Lock, repr=False)

    def record(self, packet: dict[str, Any]) -> None:
        """Record a parsed packet."""
        with self._lock:
            if packet.get("tcp"):
                self.tcp += 1
            elif packet.get("udp"):
                self.udp += 1
            if packet.get("dns"):
                self.dns += 1
            elif packet.get("icmp"):
                self.icmp += 1
            elif packet.get("arp"):
                self.arp += 1
            else:
                if packet.get("ip"):
                    self.other += 1

            self.total_bytes += packet.get("length", 0)

    def get_snapshot(self) -> dict[str, Any]:
        """Get current stats snapshot."""
        with self._lock:
            return {
                "tcp": self.tcp,
                "udp": self.udp,
                "icmp": self.icmp,
                "arp": self.arp,
                "dns": self.dns,
                "other": self.other,
                "total": self.tcp + self.udp + self.icmp + self.arp + self.dns + self.other,
                "total_bytes": self.total_bytes,
            }

    def reset(self) -> None:
        """Reset all statistics."""
        with self._lock:
            self.tcp = 0
            self.udp = 0
            self.icmp = 0
            self.arp = 0
            self.dns = 0
            self.other = 0
            self.total_bytes = 0
