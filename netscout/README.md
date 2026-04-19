# NetworkScout

A local network scanner and device discovery tool that scans local networks to find active devices with their IP addresses, hostnames, open ports, and MAC vendor information.

## Features

- **Subnet scanning** - Discover devices on local networks via ARP or TCP fallback
- **Port scanning** - Scan for common services with configurable concurrency
- **Hostname resolution** - Resolve device hostnames via reverse DNS
- **MAC vendor lookup** - Identify device manufacturers via OUI database
- **Results export** - Export to JSON or CSV formats
- **CLI output** - Clean table output with Rich formatting

## Requirements

- Python 3.10+
- Root privileges (for ARP scanning)

## Installation

```bash
pip install -e .
```

Or install dependencies manually:

```bash
pip install -r requirements.txt
```

## Usage

```bash
sudo netscout 192.168.1.0/24
```

### Scan Options

| Flag | Description | Default |
|------|-----------|---------|
| `-p, --ports` | Ports: common, top100, range | common |
| `--skip-arp` | Skip ARP, use TCP fallback | false |
| `--skip-hostname` | Skip hostname resolution | false |
| `--skip-oui` | Skip MAC vendor lookup | false |
| `-c, --concurrency` | Max concurrent scans | 100 |
| `-t, --timeout` | Port timeout (seconds) | 2.0 |

### Output Options

| Flag | Description |
|------|-----------|
| `-o, --output` | Output file (JSON/CSV) |
| `--format` | Output format: json, csv, table |
| `-v, --verbose` | Increase verbosity |

### Examples

```bash
sudo netscout 192.168.1.0/24
sudo netscout 192.168.1.0/24 -p 22,80,443
sudo netscout 192.168.1.0/24 -p top100
sudo netscout 192.168.1.0/24 --skip-hostname
sudo netscout 192.168.1.0/24 -o results.json
sudo netscout 192.168.1.0/24 -o results.csv --format csv
sudo netscout 192.168.1.0/24 -vvv
sudo netscout 192.168.1.0/24 -c 50 -t 5.0
sudo netscout --update-oui
```

## Programmatic API

```python
import asyncio
from netscout.scanner.scheduler import ScanScheduler

async def main():
    scanner = ScanScheduler(
        concurrency=100,
        timeout=2.0,
        skip_hostname=False,
        skip_oui=False,
        use_tcp_fallback=False,
    )

    from netscout.discovery.ports import parse_port_spec
    ports = parse_port_spec("common")

    devices = await scanner.scan_all("192.168.1.0/24", ports)

    for device in devices:
        print(f"{device.ip} - {device.hostname or 'Unknown'}")
        print(f"  MAC: {device.mac} ({device.mac_vendor})")
        print(f"  Ports: {device.ports}")

asyncio.run(main())
```

## Security Considerations

- Only scan networks you own or have permission to scan
- Default concurrency of 100 may trigger IDS on some networks
- Results may contain sensitive network information

## License

MIT