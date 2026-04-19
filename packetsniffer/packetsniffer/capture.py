"""Packet capture module using Scapy."""

from __future__ import annotations

import threading
from threading import Event
from typing import Any, Callable

from scapy.all import Packet, PacketList, sniff


def capture_packets(
    iface: str | None = None,
    bpf_filter: str | None = None,
    count: int | None = None,
    store: bool = False,
) -> list[Packet]:
    """
    Capture packets using Scapy sniff().

    Args:
        iface: Network interface to capture on (None = all interfaces)
        bpf_filter: BPF filter string (e.g., "tcp port 80")
        count: Number of packets to capture (None = infinite)
        store: Whether to store packets in memory

    Returns:
        List of captured packets
    """
    return sniff(
        iface=iface,
        filter=bpf_filter,
        count=count,
        store=store,
        stop_filter=lambda _: False,
    )


def start_capture(
    iface: str | None,
    bpf_filter: str | None,
    packet_handler: Callable[[Packet], Any],
    stop_event: Event,
) -> None:
    """
    Start continuous packet capture in a background thread.

    Args:
        iface: Network interface to capture on
        bpf_filter: BPF filter string
        packet_handler: Callback function for each captured packet
        stop_event: Event to signal capture stop
    """

    def stop_filter(_) -> bool:
        return stop_event.is_set()

    sniff(
        iface=iface,
        filter=bpf_filter,
        prn=packet_handler,
        store=False,
        stop_filter=stop_filter,
    )


def capture_with_thread(
    iface: str | None = None,
    bpf_filter: str | None = None,
    count: int | None = None,
    store: bool = False,
) -> tuple[list[Packet], threading.Thread, Event]:
    """
    Start capture in a separate thread with stop event.

    Args:
        iface: Network interface
        bpf_filter: BPF filter
        count: Packet count limit
        store: Store packets in memory

    Returns:
        Tuple of (packets list, thread, stop_event)
    """
    packets: list[Packet] = []
    stop_event = Event()
    lock = threading.Lock()

    def handler(pkt: Packet) -> None:
        with lock:
            if store:
                packets.append(pkt)

    thread = threading.Thread(
        target=start_capture,
        args=(iface, bpf_filter, handler, stop_event),
        daemon=True,
    )
    thread.start()

    return packets, thread, stop_event
