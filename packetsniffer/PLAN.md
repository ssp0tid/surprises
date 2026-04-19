# PacketSniffer - Implementation Plan

## Overview

A Python CLI network packet analyzer using Scapy with Rich CLI for live stats display. Features capture, protocol breakdown, BPF filters, JSON/CSV export, and real-time dashboard.

---

## File Structure

```
packetsniffer/
├── packetsniffer/
│   ├── __init__.py
│   ├── cli.py              # Click CLI entry point
│   ├── capture.py        # Scapy packet capture logic
│   ├── parser.py       # Protocol dissection/parsing
│   ├── filters.py     # BPF filter parser
│   ├── export.py      # JSON/CSV export
│   ├── dashboard.py  # Rich live stats display
│   └── stats.py       # Statistics tracking
├── pyproject.toml
├── uv.lock
├── README.md
└── tests/
    ├── __init__.py
    ├── test_capture.py
    ├── test_parser.py
    ├── test_filters.py
    └── test_export.py
```

---

## Dependencies

```toml
[project]
dependencies = [
    "scapy>=2.5.0",
    "rich>=13.0.0",
    "click>=8.1.0",
    "python-dateutil>=2.8.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.1.0",
]
```

---

## Core Modules

### 1. `capture.py` - Packet Capture

Based on Scapy best practices:

```python
from scapy.all import sniff, BPFFilter
from threading import Thread, Event

def capture_packets(
    iface: str | None = None,
    bpf_filter: str | None = None,
    count: int | None = None,
    prn: callable | None = None,
    store: bool = False,
) -> list[Packet]:
    """Capture packets using Scapy sniff()."""
    return sniff(
        iface=iface,
        filter=bpf_filter,
        count=count,
        prn=prn,
        store=store,
        stop_filter=lambda: False,  # Allow interrupt
    )
```

**Key Patterns:**
- BPF filters applied at kernel level (via libpcap) for performance
- Use `store=False` to avoid memory buildup
- Capture in background thread, process in main
- Use `stop_event` for graceful interrupt

### 2. `parser.py` - Protocol Dissection

**Layer Access Pattern:**

```python
from scapy.layers.inet import IP, TCP, UDP, ICMP
from scapy.layers.l2 import Ether, ARP
from scapy.layers.dns import DNS

def dissect_packet(pkt) -> dict:
    """Dissect packet into protocol layers."""
    result = {"timestamp": float(pkt.time)}

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
        }

    # Transport layer
    if TCP in pkt:
        result["tcp"] = {
            "sport": pkt[TCP].sport,
            "dport": pkt[TCP].dport,
            "flags": str(pkt[TCP].flags),
            "seq": pkt[TCP].seq,
            "ack": pkt[TCP].ack,
        }
    elif UDP in pkt:
        result["udp"] = {
            "sport": pkt[UDP].sport,
            "dport": pkt[UDP].dport,
        }
    elif ICMP in pkt:
        result["icmp"] = {
            "type": pkt[ICMP].type,
            "code": pkt[ICMP].code,
        }

    # Application layer
    if DNS in pkt:
        result["dns"] = parse_dns(pkt[DNS])

    return result

def parse_tcp_flags(flags) -> str:
    """Convert TCP flags to string representation."""
    flag_map = {"F": "FIN", "S": "SYN", "R": "RST", "P": "PSH", "A": "ACK", "U": "URG"}
    return ",".join(f for f, v in flag_map.items() if flags & v)
```

### 3. `filters.py` - BPF Filter Parser

**Supported Filter Syntax:**

| Filter | Description |
|--------|-------------|
| `tcp` | All TCP packets |
| `udp` | All UDP packets |
| `icmp` | All ICMP packets |
| `arp` | All ARP packets |
| `tcp port 80` |TCP on port 80 |
| `host 10.0.0.1` | Specific IP |
| `src host 10.0.0.1` | Source only |
| `net 192.168.1.0/24` | Subnet |
| `tcp[tcpflags] & tcp-syn != 0` | SYN packets only |

**Parser:**

```python
def parse_filter(filter_str: str) -> str | None:
    """Validate and return BPF filter string."""
    if not filter_str:
        return None

    # Basic validation
    valid_protocols = {"tcp", "udp", "icmp", "arp"}
    words = filter_str.split()

    if words and words[0].lower() in valid_protocols:
        return filter_str

    return filter_str  # Pass through - scapy/libpcap validates
```

### 4. `export.py` - JSON/CSV Export

```python
import json
import csv
from pathlib import Path

def export_json(packets: list[dict], output: Path) -> None:
    """Export packets to JSON."""
    with open(output, "w") as f:
        json.dump(packets, f, indent=2, default=str)

def export_csv(packets: list[dict], output: Path) -> None:
    """Export packets to CSV (flattened)."""
    if not packets:
        return

    # Flatten nested dicts
    flattened = [flatten_packet(p) for p in packets]

    # Get all unique keys
    keys = set()
    for p in flattened:
        keys.update(p.keys())

    with open(output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=sorted(keys))
        writer.writeheader()
        writer.writerows(flattened)

def flatten_packet(pkt: dict) -> dict:
    """Flatten nested packet dict for CSV."""
    result = {"timestamp": pkt.get("timestamp", "")}

    if eth := pkt.get("eth"):
        result["eth_src"] = eth.get("src", "")
        result["eth_dst"] = eth.get("dst", "")
        result["eth_type"] = eth.get("type", "")

    if ip := pkt.get("ip"):
        result["ip_src"] = ip.get("src", "")
        result["ip_dst"] = ip.get("dst", "")
        result["ip_proto"] = ip.get("proto", "")
        result["ip_ttl"] = ip.get("ttl", "")

    # Flatten other layers similarly...

    return result
```

### 5. `dashboard.py` - Rich Live Display

**Live Table Pattern:**

```python
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich import box

console = Console()

def build_stats_table(stats: dict) -> Table:
    """Build protocol breakdown table."""
    table = Table(
        title="Protocol Breakdown",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("Protocol", justify="center")
    table.add_column("Packets", justify="right")
    table.add_column("Bytes", justify="right")

    total = sum(stats.values())
    for proto, count in stats.items():
        pct = (count / total * 100) if total > 0 else 0
        table.add_row(proto.upper(), str(count), f"{pct:.1f}%")

    return table

def live_display(stats_func: callable, stop_event: Event):
    """Render live stats dashboard."""
    with Live(screen=True, refresh_per_second=4) as live:
        while not stop_event.is_set():
            stats = stats_func()
            table = build_stats_table(stats)
            live.update(table)
```

### 6. `stats.py` - Statistics Tracking

```python
from dataclasses import dataclass, field
from threading import Lock

@dataclass
class PacketStats:
    """Thread-safe packet statistics."""
    tcp: int = 0
    udp: int = 0
    icmp: int = 0
    arp: int = 0
    other: int = 0
    total_bytes: int = 0
    _lock: Lock = field(default_factory=Lock, repr=False)

    def record(self, packet: dict):
        """Record a parsed packet."""
        with self._lock:
            proto = packet.get("ip", {}).get("proto") or packet.get(" eth", {}).get("type", "other")

            if tcp_layer := packet.get("tcp"):
                self.tcp += 1
            elif packet.get("udp"):
                self.udp += 1
            elif packet.get("icmp"):
                self.icmp += 1
            elif packet.get("arp"):
                self.arp += 1
            else:
                self.other += 1

    def get_snapshot(self) -> dict:
        """Get current stats (thread-safe)."""
        with self._lock:
            return {
                "tcp": self.tcp,
                "udp": self.udp,
                "icmp": self.icmp,
                "arp": self.arp,
                "other": self.other,
                "total": self.tcp + self.udp + self.icmp + self.arp + self.other,
                "total_bytes": self.total_bytes,
            }
```

### 7. `cli.py` - Click CLI Entry Point

```python
import click
from pathlib import Path

@click.group()
@click.option("--iface", default=None, help="Network interface to capture on")
@click.option("--verbose", "-v", is_count=True, help="Increase verbosity")
@click.pass_context
def cli(ctx, iface, verbose):
    """PacketSniffer - Network packet analyzer."""
    ctx.ensure_object(dict)
    ctx.obj["iface"] = iface
    ctx.obj["verbose"] = verbose

@cli.command()
@click.option("--count", type=int, help="Number of packets to capture")
@click.option("--filter", "-f", "bpf_filter", help="BPF filter (e.g., 'tcp port 80')")
@click.option("--output", "-o", type=click.Path(), help="Export file")
@click.option("--format", type=click.Choice(["json", "csv"]), default="json")
@click.pass_context
def capture(ctx, count, bpf_filter, output, format):
    """Capture network packets."""
    from .capture import capture_packets
    from .parser import dissect_packet
    from .export import export_json, export_csv

    packets = capture_packets(
        iface=ctx.obj.get("iface"),
        bpf_filter=bpf_filter,
        count=count,
    )

    parsed = [dissect_packet(pkt) for pkt in packets]

    if output:
        path = Path(output)
        if format == "json":
            export_json(parsed, path)
        else:
            export_csv(parsed, path)
        click.echo(f"Exported {len(packets)} packets to {output}")
    else:
        for pkt in parsed:
            click.echo(pkt)

@cli.command()
@click.option("--filter", "-f", "bpf_filter", help="BPF filter")
@click.option("--duration", type=int, help="Capture duration in seconds")
@click.pass_context
def live(ctx, bpf_filter, duration):
    """Live capture with stats dashboard."""
    from .capture import start_capture
    from .dashboard import live_display
    from .stats import PacketStats
    import threading
    from threading import Event

    stats = PacketStats()
    stop_event = Event()

    def packet_handler(pkt):
        stats.record(pkt)

    capture_thread = threading.Thread(
        target=start_capture,
        args=(ctx.obj.get("iface"), bpf_filter, packet_handler, stop_event),
    )
    capture_thread.start()

    try:
        live_display(stats.get_snapshot, stop_event)
    except KeyboardInterrupt:
        stop_event.set()

    capture_thread.join()

if __name__ == "__main__":
    cli()
```

---

## CLI Commands

```bash
# Quick capture
packetsniffer capture --count 100

# Filtered capture
packetsniffer capture -f "tcp port 443" -o output.json

# Live dashboard
packetsniffer live -f "tcp"

# Export to CSV
packetsniffer capture --output traffic.csv --format csv
```

---

## Implementation Priority

1. **Phase 1** - Core capture + parsing
   - `capture.py`, `parser.py`, `filters.py`
2. **Phase 2** - Export functionality
   - `export.py`, `stats.py`
3. **Phase 3** - CLI integration
   - `cli.py`
4. **Phase 4** - Rich dashboard
   - `dashboard.py`

---

## Key References

- Scapy sniff(): https://github.com/secdev/scapy/blob/master/doc/scapy/usage.rst
- Rich Live: https://rich.readthedocs.io/en/latest/live.html
- Rich Tables: https://rich.readthedocs.io/en/latest/tables.html