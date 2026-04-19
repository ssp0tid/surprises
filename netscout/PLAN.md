# NetworkScout - Implementation Plan

## Project Overview

**Project Name:** NetworkScout
**Type:** CLI Network Scanner & Device Discovery Tool
**Core Functionality:** Scans local networks to discover active devices, their IP addresses, hostnames, open ports, and MAC vendor information.
**Target Users:** Network administrators, security professionals, home users wanting to audit their local network.

---

## Technology Stack

| Component | Technology | Version |
|-----------|-------------|---------|
| Language | Python | 3.10+ |
| Async Runtime | asyncio | Built-in |
| Network Scanning | scapy | >=2.5.0 |
| Port Scanning | socket / asyncio | Built-in |
| mDNS/Bonjour | python-zeroconf | >=0.40.0 |
| CLI UI | rich | >=13.0.0 |
| Data Validation | pydantic | >=2.0.0 |
| Export | Built-in (json, csv) | - |

---

## 1. File Structure

```
netscout/
├── netscout/
│   ├── __init__.py           # Package initialization
│   ├── __main__.py           # CLI entry point
│   ├── cli.py                # Command-line interface
│   ├── scanner/
│   │   ├── __init__.py
│   │   ├── arp_scanner.py    # ARP discovery via scapy
│   │   ├── port_scanner.py   # TCP port scanning
│   │   ├── hostname_resolver.py  # mDNS/Bonjour resolution
│   │   └── scheduler.py      # Async task orchestration
│   ├── discovery/
│   │   ├── __init__.py
│   │   ├── device.py         # Device model
│   │   ├── oui_lookup.py     # MAC vendor lookup
│   │   └── ports.py          # Common port definitions
│   ├── output/
│   │   ├── __init__.py
│   │   ├── formatter.py      # Output formatting
│   │   ├── json_exporter.py # JSON export
│   │   ├── csv_exporter.py  # CSV export
│   │   └── progress.py      # Progress indication
│   └── utils/
│       ├── __init__.py
│       ├── network.py        # Network utilities
│       ├── logging.py       # Logging setup
│       └── errors.py        # Custom exceptions
├── tests/
│   ├── __init__.py
│   ├── test_arp_scanner.py
│   ├── test_port_scanner.py
│   ├── test_oui_lookup.py
│   └── test_output.py
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── README.md
└── PLAN.md
```

---

## 2. Core Components

### 2.1 Device Model (discovery/device.py)

```python
from pydantic import BaseModel, IPv4Address
from typing import Optional
from datetime import datetime

class Device(BaseModel):
    """Represents a discovered network device."""
    ip: IPv4Address
    mac: Optional[str] = None
    hostname: Optional[str] = None
    mac_vendor: Optional[str] = None
    ports: list[int] = []
    services: dict[int, str] = {}  # port -> service name
    discovered_at: datetime = Field(default_factory=datetime.now)
    is_alive: bool = True
    
    class Config:
        arbitrary_types_allowed = True
```

### 2.2 ARP Scanner (scanner/arp_scanner.py)

**Purpose:** Discover live hosts on local subnet using ARP.

**Implementation:**
- Use scapy's `srp()` with Ether/ARP packets
- Requires root privileges (raw sockets)
- Run in thread pool executor since scapy is blocking
- Configurable timeout (default: 3 seconds)

```python
# Key implementation points:
async def arp_scan(subnet: str, timeout: int = 3) -> list[dict]:
    """Scan subnet for active devices via ARP."""
    # Use asyncio.to_thread() to run blocking scapy code
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_arp_scan, subnet, timeout)

def _sync_arp_scan(subnet: str, timeout: int) -> list[dict]:
    """Synchronous ARP scan using scapy."""
    arp_request = ARP(pdst=subnet)
    broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = broadcast / arp_request
    
    answered, _ = srp(packet, timeout=timeout, verbose=False)
    
    results = []
    for sent, received in answered:
        results.append({
            "ip": received[ARP].psrc,
            "mac": received[ARP].hwsrc
        })
    return results
```

**Edge Cases:**
- No response (empty subnet)
- Permission denied (not root)
- Invalid subnet format
- Network interface not available

### 2.3 Port Scanner (scanner/port_scanner.py)

**Purpose:** Scan discovered hosts for open ports.

**Implementation:**
- TCP connect scan using asyncio.open_connection
- Semaphore for concurrency control (default: 100 concurrent)
- Configurable timeout per port
- Service identification from common port numbers

```python
# Common ports configuration (discovery/ports.py)
COMMON_PORTS = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    143: "IMAP",
    443: "HTTPS",
    445: "SMB",
    993: "IMAPS",
    995: "POP3S",
    3306: "MySQL",
    3389: "RDP",
    5432: "PostgreSQL",
    8080: "HTTP-Alt",
    8443: "HTTPS-Alt",
    # Add more as needed
}

# Async port scanner
async def scan_port(ip: str, port: int, timeout: float = 1.0) -> tuple[int, bool, str]:
    """Scan a single port. Returns (port, is_open, service_name)."""
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port),
            timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        service = COMMON_PORTS.get(port, "Unknown")
        return (port, True, service)
    except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
        return (port, False, "")

async def scan_ports(ip: str, ports: list[int], 
                    concurrency: int = 100) -> dict[int, str]:
    """Scan multiple ports concurrently."""
    semaphore = asyncio.Semaphore(concurrency)
    
    async def scan_with_semaphore(port):
        async with semaphore:
            return await scan_port(ip, port)
    
    tasks = [scan_with_semaphore(port) for port in ports]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    open_ports = {}
    for result in results:
        if isinstance(result, tuple) and result[1]:  # is_open
            open_ports[result[0]] = result[2]  # port -> service
    
    return open_ports
```

**Edge Cases:**
- Connection refused (port closed)
- Timeout (host unreachable)
- Too many open files (ulimit)
- Firewall blocking
- Host down during scan

### 2.4 Hostname Resolver (scanner/hostname_resolver.py)

**Purpose:** Resolve device hostnames via mDNS/Bonjour.

**Implementation:**
- Use python-zeroconf AsyncZeroconf
- Query for .local addresses
- Fallback to reverse DNS lookup
- Configurable timeout (default: 3 seconds)

```python
from zeroconf import AsyncZeroconf, ServiceStateChange
from zeroconf.asyncio import AsyncZeroconf

async def resolve_hostname(ip: str, timeout: float = 3.0) -> Optional[str]:
    """Resolve hostname via mDNS or reverse DNS."""
    
    # Try mDNS first (for .local addresses)
    try:
        aiozc = AsyncZeroconf()
        # Query for the IP address
        # This requires service browsing which is complex
        # Simplified approach: try reverse DNS first
        await aiozc.async_close()
    except Exception:
        pass
    
    # Fallback: reverse DNS
    try:
        hostname, _, _ = await asyncio.wait_for(
            asyncio.getaddrinfo(ip, None),
            timeout=timeout
        )
        if hostname:
            return hostname[0][0]  # First result's hostname
    except (asyncio.TimeoutError, socket.gaierror):
        pass
    
    return None
```

**Alternative (simpler) approach using socket:**

```python
import socket

async def resolve_hostname(ip: str, timeout: float = 2.0) -> Optional[str]:
    """Simple hostname resolution via gethostbyaddr."""
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            socket.gethostbyaddr, 
            str(ip)
        )
        return result[0]  # hostname
    except (socket.herror, socket.gaierror, OSError):
        return None
```

**Edge Cases:**
- No hostname configured
- mDNS service not running
- Firewall blocking mDNS (port 5353)
- Slow resolution

### 2.5 OUI Lookup (discovery/oui_lookup.py)

**Purpose:** Map MAC address prefix to vendor name.

**Implementation:**
- Use local OUI database (IEEE MA-L)
- Download from: https://standards-oui.ieee.org/oui.txt
- Cache locally in CSV format
- Support incremental updates

```python
# oui_lookup.py
import csv
from pathlib import Path
from typing import Optional

class OUILookup:
    """MAC vendor OUI lookup."""
    
    OUI_URL = "https://standards-oui.ieee.org/oui.txt"
    CACHE_FILE = "oui_database.txt"
    
    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or Path.home() / ".netscout"
        self.cache_file = self.cache_dir / self.CACHE_FILE
        self._cache = {}
    
    def load(self):
        """Load OUI database from cache."""
        if not self.cache_file.exists():
            self.download()
        
        self._cache = {}
        with open(self.cache_file, 'r', encoding='utf-8') as f:
            for line in f:
                if '(hex)' in line:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        oui = parts[0].strip().replace('-', ':').upper()[:8]
                        vendor = parts[-1].strip()
                        self._cache[oui] = vendor
    
    def lookup(self, mac: str) -> Optional[str]:
        """Look up vendor for MAC address."""
        mac = mac.upper().replace('-', ':')
        prefix = mac[:8]  # First 3 bytes (OUI)
        return self._cache.get(prefix)
    
    def download(self):
        """Download latest OUI database."""
        import urllib.request
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(self.OUI_URL, self.cache_file)
```

**Edge Cases:**
- No internet (use cached data)
- Invalid MAC format
- Unknown OUI prefix
- Cache corrupted

---

## 3. API Design

### 3.1 CLI Interface (cli.py)

```python
import argparse
from pathlib import Path

def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="netscout",
        description="Network Scanner & Device Discovery Tool"
    )
    
    # Target specification
    parser.add_argument(
        "target",
        nargs="?",
        help="Target subnet (e.g., 192.168.1.0/24) or IP range"
    )
    
    # Scan options
    parser.add_argument(
        "-p", "--ports",
        default="common",
        help="Ports to scan: 'common', 'top100', or range (e.g., '1-1024')"
    )
    parser.add_argument(
        "--skip-arp",
        action="store_true",
        help="Skip ARP discovery, use only port scan"
    )
    parser.add_argument(
        "--skip-hostname",
        action="store_true",
        help="Skip hostname resolution"
    )
    parser.add_argument(
        "--skip-oui",
        action="store_true",
        help="Skip MAC vendor lookup"
    )
    
    # Performance
    parser.add_argument(
        "-c", "--concurrency",
        type=int,
        default=100,
        help="Max concurrent port scans (default: 100)"
    )
    parser.add_argument(
        "-t", "--timeout",
        type=float,
        default=2.0,
        help="Timeout for port checks in seconds (default: 2.0)"
    )
    
    # Output
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output file (JSON or CSV based on extension)"
    )
    parser.add_argument(
        "--format",
        choices=["json", "csv", "table"],
        default="table",
        help="Output format"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v, -vv, -vvv)"
    )
    
    # Options
    parser.add_argument(
        "--update-oui",
        action="store_true",
        help="Update OUI database before scanning"
    )
    
    return parser
```

### 3.2 Programmatic API

```python
from netscout.scanner import NetworkScanner
from netscout.discovery import Device

# Example usage
async def main():
    scanner = NetworkScanner(
        concurrency=100,
        timeout=2.0,
        scan_ports=True,
        resolve_hostnames=True,
        lookup_oui=True
    )
    
    # Scan subnet
    devices = await scanner.scan("192.168.1.0/24")
    
    for device in devices:
        print(f"{device.ip} - {device.hostname or 'Unknown'}")
        print(f"  MAC: {device.mac} ({device.mac_vendor})")
        print(f"  Ports: {device.ports}")
        print()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 4. Error Handling

### 4.1 Custom Exceptions (utils/errors.py)

```python
class NetworkScoutError(Exception):
    """Base exception for NetworkScout."""
    pass

class PermissionError(NetworkScoutError):
    """Raised when root privileges are required."""
    pass

class NetworkError(NetworkScoutError):
    """Raised for network-related errors."""
    pass

class InvalidSubnetError(NetworkScoutError):
    """Raised for invalid subnet specification."""
    pass

class ScanTimeoutError(NetworkScoutError):
    """Raised when scan times out."""
    pass
```

### 4.2 Error Recovery Strategies

| Error | Strategy |
|-------|----------|
| No root privileges | Fall back to TCP connect scan, warn user |
| Network unreachable | Skip host, continue with others |
| Port scan timeout | Mark port as closed, continue |
| OUI lookup fails | Return "Unknown" vendor |
| mDNS timeout | Skip hostname, continue |
| Export fails | Show error, keep console output |

---

## 5. Async Orchestration

### 5.1 Task Scheduler (scanner/scheduler.py)

```python
import asyncio
from typing import Optional

class ScanScheduler:
    """Orchestrates async scanning tasks."""
    
    def __init__(
        self,
        concurrency: int = 100,
        timeout: float = 2.0
    ):
        self.concurrency = concurrency
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(concurrency)
    
    async def run_arp_scan(self, subnet: str) -> list[dict]:
        """Run ARP discovery scan."""
        from netscout.scanner.arp_scanner import arp_scan
        return await arp_scan(subnet, timeout=self.timeout)
    
    async def run_port_scan(
        self, 
        ip: str, 
        ports: list[int]
    ) -> dict[int, str]:
        """Run port scan on a single host."""
        from netscout.scanner.port_scanner import scan_ports
        return await scan_ports(
            ip, 
            ports,
            concurrency=self.concurrency
        )
    
    async def run_hostname_resolve(self, ip: str) -> Optional[str]:
        """Resolve hostname for an IP."""
        from netscout.scanner.hostname_resolver import resolve_hostname
        return await resolve_hostname(ip, timeout=self.timeout)
    
    async def scan_all(
        self,
        subnet: str,
        ports: list[int],
        skip_hostname: bool = False
    ) -> list[Device]:
        """Run full scan pipeline."""
        
        # Phase 1: ARP discovery
        arp_results = await self.run_arp_scan(subnet)
        
        # Phase 2: For each discovered device, run port scan + hostname
        devices = []
        for result in arp_results:
            device = Device(
                ip=result["ip"],
                mac=result["mac"]
            )
            
            # Port scan
            if ports:
                device.ports = await self.run_port_scan(device.ip, ports)
            
            # Hostname resolution
            if not skip_hostname:
                device.hostname = await self.run_hostname_resolve(device.ip)
            
            devices.append(device)
        
        return devices
```

---

## 6. Output Formatting

### 6.1 Console Output (output/formatter.py)

```python
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

class OutputFormatter:
    """Format and display scan results."""
    
    def __init__(self, verbose: int = 0):
        self.console = Console()
        self.verbose = verbose
    
    def display_devices(self, devices: list[Device]):
        """Display devices in table format."""
        table = Table(title="Discovered Devices")
        
        table.add_column("IP Address", style="cyan")
        table.add_column("Hostname", style="green")
        table.add_column("MAC Address", style="yellow")
        table.add_column("Vendor", style="magenta")
        table.add_column("Open Ports", style="red")
        
        for device in devices:
            ports_str = ", ".join(map(str, device.ports)) or "None"
            table.add_row(
                str(device.ip),
                device.hostname or "N/A",
                device.mac or "N/A",
                device.mac_vendor or "N/A",
                ports_str
            )
        
        self.console.print(table)
    
    def display_progress(self, current: int, total: int, message: str):
        """Display progress update."""
        if self.verbose > 0:
            self.console.print(f"[{current}/{total}] {message}")
```

### 6.2 JSON Export (output/json_exporter.py)

```python
import json
from datetime import datetime
from pathlib import Path

def export_json(devices: list[Device], output_path: Path):
    """Export devices to JSON."""
    data = {
        "scan_time": datetime.now().isoformat(),
        "total_devices": len(devices),
        "devices": [
            {
                "ip": str(d.ip),
                "mac": d.mac,
                "hostname": d.hostname,
                "mac_vendor": d.mac_vendor,
                "ports": d.ports,
                "services": d.services,
                "discovered_at": d.discovered_at.isoformat()
            }
            for d in devices
        ]
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
```

### 6.3 CSV Export (output/csv_exporter.py)

```python
import csv
from pathlib import Path

def export_csv(devices: list[Device], output_path: Path):
    """Export devices to CSV."""
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "IP Address", "Hostname", "MAC Address", 
            "Vendor", "Open Ports", "Services", "Discovered At"
        ])
        
        for device in devices:
            writer.writerow([
                str(device.ip),
                device.hostname or "",
                device.mac or "",
                device.mac_vendor or "",
                ",".join(map(str, device.ports)),
                ",".join(f"{p}:{s}" for p, s in device.services.items()),
                device.discovered_at.isoformat()
            ])
```

---

## 7. Dependencies

### 7.1 requirements.txt

```
scapy>=2.5.0
python-zeroconf>=0.40.0
rich>=13.0.0
pydantic>=2.0.0
```

### 7.2 requirements-dev.txt

```
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
black>=23.0.0
mypy>=1.0.0
```

### 7.3 pyproject.toml

```toml
[project]
name = "netscout"
version = "1.0.0"
description = "Network Scanner & Device Discovery Tool"
requires-python = ">=3.10"
dependencies = [
    "scapy>=2.5.0",
    "python-zeroconf>=0.40.0",
    "rich>=13.0.0",
    "pydantic>=2.0.0",
]

[project.scripts]
netscout = "netscout.cli:main"

[build-system]
requires = ["setuptools>=65.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.black]
line-length = 88

[tool.mypy]
python_version = "3.10"
```

---

## 8. Implementation Roadmap

### Phase 1: Core Scanning
1. [ ] Project scaffolding
2. [ ] Device model with Pydantic
3. [ ] ARP scanner with scapy
4. [ ] Basic CLI interface

### Phase 2: Port Scanning
1. [ ] Async port scanner
2. [ ] Common port definitions
3. [ ] Service identification
4. [ ] Concurrency control

### Phase 3: Enhancement
1. [ ] Hostname resolution (mDNS/DNS)
2. [ ] OUI lookup with caching
3. [ ] Progress indication

### Phase 4: Output
1. [ ] Rich console formatting
2. [ ] JSON export
3. [ ] CSV export

### Phase 5: Polish
1. [ ] Error handling
2. [ ] Edge case handling
3. [ ] Documentation
4. [ ] Tests

---

## 9. Edge Cases & Mitigations

| Edge Case | Impact | Mitigation |
|-----------|--------|-------------|
| No root privileges | ARP scan fails | Fall back to TCP connect scan, warn user |
| Invalid subnet | Crash | Validate CIDR format before scan |
| Network timeout | Partial results | Continue with reachable hosts |
| Firewall blocking | Incomplete scan | Adjust timeouts, retry once |
| No internet for OUI | Unknown vendor | Use cached database |
| mDNS not available | No hostname | Fall back to reverse DNS |
| Too many open files | Scan stops | Use semaphore to limit concurrency |
| Host down during scan | Partial results | Mark device as unreachable |

---

## 10. Usage Examples

```bash
# Basic scan of local subnet
sudo netscout 192.168.1.0/24

# Scan with specific ports
sudo netscout 192.168.1.0/24 -p 22,80,443

# Scan top 100 ports
sudo netscout 192.168.1.0/24 -p top100

# Skip hostname resolution (faster)
sudo netscout 192.168.1.0/24 --skip-hostname

# Export to JSON
sudo netscout 192.168.1.0/24 -o results.json

# Export to CSV
sudo netscout 192.168.1.0/24 -o results.csv --format csv

# Verbose output
sudo netscout 192.168.1.0/24 -vvv

# Lower concurrency (for slow networks)
sudo netscout 192.168.1.0/24 -c 50 -t 5.0

# Update OUI database
sudo netscout --update-oui
```

---

## 11. Security Considerations

1. **Authorization:** Only scan networks you own or have permission to scan
2. **Rate Limiting:** Default concurrency of 100 may trigger IDS - use `-c` to reduce
3. **Data Handling:** Results may contain sensitive network information
4. **Logging:** Avoid logging sensitive data (MAC addresses, IPs in detail)
5. **Dependencies:** Keep scapy and other dependencies updated

---

## Summary

NetworkScout implements a robust network scanning solution with:
- **ARP discovery** via scapy for reliable local subnet scanning
- **Async port scanning** with asyncio for concurrent checks
- **Hostname resolution** via mDNS/DNS for device identification
- **OUI lookup** for MAC vendor identification
- **Multiple export formats** (JSON, CSV, table) for results
- **Rich CLI** with progress indication and verbose options
- **Comprehensive error handling** for edge cases

The architecture separates concerns into scanner, discovery, and output modules, making it maintainable and extensible.