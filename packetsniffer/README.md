# PacketSniffer

A Python CLI network packet analyzer using Scapy with Rich CLI for live stats display.

## Features

- Packet capture using Scapy
- Protocol dissection (Ethernet, IP, TCP, UDP, ICMP, DNS, ARP)
- BPF filter support
- Export to JSON/CSV
- Live statistics dashboard with Rich CLI

## Requirements

- Python 3.10+
- libpcap development headers

## Installation

```bash
# Install dependencies
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

### Linux (Debian/Ubuntu)

```bash
sudo apt-get install libpcap-dev
```

### macOS

```bash
brew install libpcap
```

### Windows

Install Npcap from https://npcap.com/

## Usage

### List available interfaces

```bash
packetsniffer interfaces
```

### Capture packets

```bash
# Capture 10 packets
packetsniffer capture --count 10

# Capture with filter
packetsniffer capture -f "tcp port 80" --count 100

# Export to JSON
packetsniffer capture -o output.json --format json

# Export to CSV
packetsniffer capture -o output.csv --format csv

# Specify interface
packetsniffer --iface eth0 capture --count 50
```

### Live dashboard

```bash
# Live stats with TCP filter
packetsniffer live -f "tcp"

# Live stats with port filter
packetsniffer live -f "udp port 53"
```

### Capture and display statistics

```bash
# Capture 100 packets and show stats
packetsniffer stats

# With filter
packetsniffer stats -f "tcp port 443" --count 50
```

## BPF Filter Examples

| Filter | Description |
|--------|-------------|
| `tcp` | All TCP packets |
| `udp` | All UDP packets |
| `icmp` | All ICMP packets |
| `tcp port 80` | TCP on port 80 |
| `host 10.0.0.1` | Specific IP |
| `src host 10.0.0.1` | Source only |
| `net 192.168.1.0/24` | Subnet |
| `tcp[tcpflags] & tcp-syn != 0` | SYN packets only |

## Development

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=packetsniffer
```