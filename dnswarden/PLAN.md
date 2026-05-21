# DNSWarden Implementation Plan

**Project**: DNSWarden - Local DNS Server with Custom Domain Resolution, Ad/Tracker Blocking, DNS-over-HTTPS Proxy, and Query Logging  
**Version**: 1.0.0  
**Last Updated**: April 2026

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [File Structure](#2-file-structure)
3. [Dependencies](#3-dependencies)
4. [Core Architecture](#4-core-architecture)
5. [API Design](#5-api-design)
6. [Error Handling](#6-error-handling)
7. [Edge Cases](#7-edge-cases)
8. [Configuration](#8-configuration)
9. [Implementation Phases](#9-implementation-phases)

---

## 1. Project Overview

### 1.1 Core Features

| Feature | Description |
|---------|-------------|
| **Local DNS Server** | Run on port 53 (requires root), handle UDP/TCP |
| **Custom Resolution** | Local zone files, static mappings |
| **Ad/Tracker Blocking** | Blocklist-based domain filtering with wildcard support |
| **DoH Proxy** | Forward client queries to upstream DoH servers (RFC 8484) |
| **Query Logging** | JSON logs to SQLite/file, optional syslog |

### 1.2 Design Goals

- **Performance**: Handle 10,000+ QPS
- **Security**: Rate limiting, IP allowlisting, query validation
- **Extensible**: Plugin architecture for custom resolvers
- **Minimal dependencies**: Pure Python + dnslib

### 1.3 Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| DNS Protocol | dnslib | >=0.9.24 |
| HTTP Client | httpx | >=0.27.0 |
| Data Validation | pydantic | >=2.0 |
| Settings | pydantic-settings | >=2.0 |
| API Server | uvicorn | >=0.30.0 |
| Database | aiosqlite | >=0.19.0 |

---

## 2. File Structure

```
dnswarden/
├── pyproject.toml                 # Project metadata
├── requirements.txt             # Python dependencies
├── uv.lock                      # Locked dependencies
├── .env.example                 # Environment template
├── configs/
│   ├── dnswarden.example.toml   # Example configuration
│   └── blocklists.toml          # Blocklist URLs
├── src/
│   └── dnswarden/
│       ├── __init__.py
│       ├── __main__.py          # CLI entry point
│       ├── config.py            # Configuration loader
│       ├── protocol/
│       │   ├── __init__.py
│       │   ├── udp.py           # UDP DNS handler
│       │   ├── tcp.py           # TCP DNS handler
│       │   └── doh.py           # DoH proxy (RFC 8484)
│       ├── resolver/
│       │   ├── __init__.py
│       │   ├── base.py          # Base resolver
│       │   ├── blocklist.py     # Blocklist filter
│       │   ├── local.py         # Local zone resolver
│       │   └── upstream.py     # Upstream forwarder
│       ├── logging/
│       │   ├── __init__.py
│       │   ├── sqlite.py        # SQLite logger
│       │   ├── file.py          # File logger
│       │   └── syslog.py       # Syslog logger
│       ├── security/
│       │   ├── __init__.py
│       │   ├── ratelimit.py    # Rate limiter
│       │   └── allowlist.py    # IP allowlist
│       ├── api/
│       │   ├── __init__.py
│       │   ├── server.py       # Admin HTTP server
│       │   └── routes.py      # API routes
│       └── utils/
│           ├── __init__.py
│           ├── domain.py       # Domain utilities
│           └── cache.py        # Simple cache
├── tests/
│   ├── __init__.py
│   ├── test_resolver.py
│   ├── test_blocklist.py
│   └── test_integration.py
├── docs/
│   └── api.md
├── scripts/
│   └── update-blocklists.sh    # Blocklist update script
└── data/
    ├── blocklists/            # Downloaded blocklists
    └── logs/                  # Log files
```

### 2.1 Key Files Overview

| File | Purpose |
|------|---------|
| `src/dnswarden/__main__.py` | CLI entry point with argparse |
| `src/dnswarden/config.py` | TOML/YAML config loader |
| `src/dnswarden/protocol/udp.py` | UDP server using dnslib.server |
| `src/dnswarden/protocol/tcp.py` | TCP server with length prefix |
| `src/dnswarden/protocol/doh.py` | RFC 8484 DoH implementation |
| `src/dnswarden/resolver/base.py` | Abstract resolver interface |
| `src/dnswarden/resolver/blocklist.py` | Blocklist matching with wildcards |
| `src/dnswarden/resolver/local.py` | Local zone file resolution |
| `src/dnswarden/resolver/upstream.py` | Upstream DNS forwarding |
| `src/dnswarden/logging/sqlite.py` | SQLite-based query logging |
| `src/dnswarden/api/server.py` | FastAPI HTTP server |
| `src/dnswarden/security/ratelimit.py` | Per-client rate limiting |

---

## 3. Dependencies

### 3.1 Core Dependencies

```toml
[project.dependencies]
dnslib = ">=0.9.24"              # DNS packet parsing/building
httpx = ">=0.27.0"               # DoH client (HTTP/2 support)
pydantic = ">=2.0"              # Data validation
pydantic-settings = ">=2.0"     # Settings management
toml = ">=0.10"                # Config file parsing
python-dotenv = ">=1.0"          # Environment variables
```

### 3.2 Optional Dependencies

```toml
[project.optional-dependencies]
server = [
    "uvicorn[standard]>=0.30",   # API server
]
database = [
    "aiosqlite>=0.19",          # Async SQLite
]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=4.0",
    "ruff>=0.4",
    "mypy>=1.0",
]
```

### 3.3 Dependency Rationale

| Package | Purpose | Why |
|---------|---------|-----|
| `dnslib` | DNS protocol handling | Industry-standard, supports all DNS record types |
| `httpx` | HTTP/2 client for DoH | Connection pooling, timeouts, HTTP/2 |
| `pydantic` | Data validation | Type safety, config validation |
| `uvicorn` | ASGI server | Fast API server |
| `aiosqlite` | Async database | Non-blocking DB writes |

---

## 4. Core Architecture

### 4.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        DNSWarden                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │   UDP/TCP     │    │    DoH       │    │   HTTP       │   │
│  │   Server     │    │   Proxy      │    │   Admin     │   │
│  │   (port 53)  │    │   (port 443)│    │   (port 8080)│ │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘   │
│         │                   │                   │           │
│         └───────────────────┼───────────────────┘           │
│                             │                               │
│                    ┌────────▼────────┐                    │
│                    │   Resolver      │                    │
│                    │   Pipeline     │                    │
│                    └────────┬────────┘                    │
│                             │                               │
│         ┌───────────────────┼───────────────────┐           │
│         │                   │                   │           │
│  ┌──────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐  │
│  │  Blocklist │   │  Local      │   │  Upstream   │  │
│  │  Filter   │   │  Zones      │   │  Forwarder │  │
│  └───────────┘   └─────────────┘   └─────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────┐        │
│  │                  Query Logger                    │        │
│  │         (SQLite / File / Syslog)                  │        │
│  └──────────────────────────────────────────────────┘        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Request Flow

```
Client Query ──► Rate Limiter ──► Blocklist Check ──► Local Zone
      │            │                  │                │
      │            │                  │            (not found)
      │            │                  │                │
      │            ▼                  ▼                ▼
      │        Allow/Deny      Block/Allow      Forward to
      │            │            │              Upstream
      │            │            │                │
      │            │            │                │
      ▼            ▼            ▼                ▼
 ◄───────── Response ────────────────────────
```

### 4.3 UDP Handler Implementation

```python
# src/dnswarden/protocol/udp.py
import socket
from dnslib import DNSRecord
from dnslib.server import DNSHandler

class UDPHandler:
    """Handle DNS over UDP."""
    
    def __init__(self, resolver, bind_address="0.0.0.0", port=53):
        self.resolver = resolver
        self.bind_address = bind_address
        self.port = port
        self.socket = None
    
    def start(self):
        """Start UDP server."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.bind_address, self.port))
    
    def handle_forever(self):
        """Process queries indefinitely."""
        while True:
            data, client_addr = self.socket.recvfrom(4096)
            request = DNSRecord.parse(data)
            
            # Resolve query
            response = self.resolver.resolve(request, client_addr)
            
            # Send response
            self.socket.sendto(response.pack(), client_addr)
    
    def stop(self):
        """Stop server."""
        if self.socket:
            self.socket.close()
```

### 4.4 TCP Handler Implementation

```python
# src/dnswarden/protocol/tcp.py
import socket
import struct
from dnslib import DNSRecord

class TCPHandler:
    """Handle DNS over TCP.
    
    TCP requires length prefix (2 bytes) before DNS packet.
    RFC 7766: DNS transport independent of the query/response pattern.
    """
    
    def __init__(self, resolver, bind_address="0.0.0.0", port=53):
        self.resolver = resolver
        self.bind_address = bind_address
        self.port = port
        self.socket = None
    
    def handle_client(self, client_socket, client_addr):
        """Handle a single TCP client connection."""
        try:
            # Read length prefix (2 bytes, big-endian)
            length_data = self._recv_exact(client_socket, 2)
            if not length_data:
                return
            
            length = struct.unpack("!H", length_data)[0]
            
            # Read DNS packet
            data = self._recv_exact(client_socket, length)
            if not data:
                return
            
            request = DNSRecord.parse(data)
            response = self.resolver.resolve(request, client_addr)
            
            response_data = response.pack()
            response_length = struct.pack("!H", len(response_data))
            
            client_socket.sendall(response_length + response_data)
        except Exception as e:
            logger.error(f"TCP client error: {e}")
        finally:
            client_socket.close()
    
    def _recv_exact(self, sock, n):
        """Receive exactly n bytes."""
        data = b""
        while len(data) < n:
            chunk = sock.recv(n - len(data))
            if not chunk:
                return None
            data += chunk
        return data
```

### 4.5 DoH Handler (RFC 8484)

```python
# src/dnswarden/protocol/doh.py
import base64
import httpx
from dnslib import DNSRecord

class DoHResolver:
    """DNS-over-HTTPS proxy/forwarder.
    
    Supports RFC 8484:
    - POST: Binary DNS message in body
    - GET: base64url-encoded in ?dns= parameter
    """
    
    def __init__(self, upstream_url="https://cloudflare-dns.com/dns-query"):
        self.upstream_url = upstream_url
        self.client = httpx.Client(
            http2=True,
            timeout=10.0,
            headers={"Accept": "application/dns-message"}
        )
    
    def resolve(self, request, client_addr=None):
        """Forward DNS query via DoH."""
        wire = request.pack()
        
        # Try POST first
        response = self._do_post(wire)
        if response:
            return DNSRecord.parse(response)
        
        # Fallback to GET
        response = self._do_get(request)
        if response:
            return DNSRecord.parse(response)
        
        # Both failed - return SERVFAIL
        return self._servfail(request)
    
    def _do_post(self, wire):
        """POST method."""
        try:
            resp = self.client.post(
                self.upstream_url,
                content=wire,
                headers={"Content-Type": "application/dns-message"}
            )
            if resp.status_code == 200:
                return resp.content
        except Exception:
            pass
        return None
    
    def _do_get(self, request):
        """GET method with base64url encoding."""
        try:
            wire = request.pack()
            # base64url without padding
            b64 = base64.urlsafe_b64encode(wire).decode().rstrip("=")
            resp = self.client.get(
                self.upstream_url,
                params={"dns": b64}
            )
            if resp.status_code == 200:
                return resp.content
        except Exception:
            pass
        return None
    
    def _servfail(self, request):
        """Return SERVFAIL response."""
        reply = request.reply()
        reply.header.rcode = 2  # SERVFAIL
        return reply
```

### 4.6 Base Resolver Interface

```python
# src/dnswarden/resolver/base.py
from abc import ABC, abstractmethod

class BaseResolver(ABC):
    """Abstract base resolver.
    
    All resolvers implement this interface.
    The resolver pipeline chains multiple resolvers.
    """
    
    @abstractmethod
    def resolve(self, request, client_addr):
        """Resolve DNS query and return response.
        
        Args:
            request: DNSRecord containing the query
            client_addr: Tuple (ip, port) of client
            
        Returns:
            DNSRecord: Response to send back
        """
        pass
    
    def can_resolve(self, request):
        """Check if this resolver can handle the query.
        
        Override to implement conditional resolution.
        
        Args:
            request: DNSRecord containing the query
            
        Returns:
            bool: True if this resolver can answer
        """
        return True
```

### 4.7 Blocklist Resolver

```python
# src/dnswarden/resolver/blocklist.py
import re
from pathlib import Path
from dnslib import DNSRecord, RR, RCODE

class BlocklistResolver(BaseResolver):
    """Filter domain queries against blocklists.
    
    Supports:
    - Simple domain matching (exact)
    - Wildcard matching (*.example.com)
    - Regex patterns
    - Return NXDOMAIN or 0.0.0.0
    """
    
    def __init__(self, next_resolver=None, blocklist_dir="/etc/dnswarden/blocklists"):
        self.next_resolver = next_resolver
        self.blocklist_dir = Path(blocklist_dir)
        self.exact_domains = set()
        self.wildcard_patterns = []
        self.regex_patterns = []
        self._load_blocklists()
    
    def _load_blocklists(self):
        """Load all blocklist files."""
        if not self.blocklist_dir.exists():
            return
        
        for f in self.blocklist_dir.glob("*.txt"):
            self._load_file(f)
    
    def _load_file(self, path):
        """Load a single blocklist file."""
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            # Parse format: "0.0.0.0 domain.com" or just "domain.com"
            parts = line.split()
            domain = parts[-1] if parts else line
            
            if domain.startswith("*."):
                # Wildcard: *.ads.example.com
                pattern = domain[1:].replace(".", r"\.").replace("*", ".*")
                self.wildcard_patterns.append(re.compile(pattern))
            elif domain.startswith("^") or domain.endswith("$"):
                # Regex pattern
                try:
                    self.regex_patterns.append(re.compile(domain))
                except re.error:
                    pass
            else:
                # Exact match
                self.exact_domains.add(domain.lower())
    
    def resolve(self, request, client_addr):
        """Check if domain is blocked."""
        qname = str(request.q.qname).rstrip(".").lower()
        
        if self._is_blocked(qname):
            reply = request.reply()
            # Return NXDOMAIN for strict blocking
            # Or return 0.0.0.0 for stealth blocking
            reply.add_answer(*RR.fromZone(f"{qname}. 300 A 0.0.0.0"))
            return reply
        
        # Not blocked - pass to next resolver
        if self.next_resolver:
            return self.next_resolver.resolve(request, client_addr)
        
        # No resolver - forward to upstream
        upstream = UpstreamResolver()
        return upstream.resolve(request, client_addr)
    
    def _is_blocked(self, domain):
        """Check if domain is in any blocklist."""
        # Check exact match
        if domain in self.exact_domains:
            return True
        
        # Check wildcards
        for pattern in self.wildcard_patterns:
            if pattern.match(domain):
                return True
        
        # Check regex
        for pattern in self.regex_patterns:
            if pattern.search(domain):
                return True
        
        return False
```

### 4.8 Local Zone Resolver

```python
# src/dnswarden/resolver/local.py
from dnslib import DNSRecord, RR

class LocalResolver(BaseResolver):
    """Resolve from local zone files.
    
    Format (YAML):
    zones:
      local.lan:
        - host: server
          type: A
          value: 192.168.1.10
        - host: printer
          type: A
          value: 192.168.1.20
    """
    
    def __init__(self, next_resolver=None, zones_config=None):
        self.next_resolver = next_resolver
        self.zones = {}
        self._load_zones(zones_config or {})
    
    def _load_zones(self, zones_config):
        """Load zones from configuration."""
        for zone_name, records in zones_config.items():
            self.zones[zone_name.lower()] = records
    
    def resolve(self, request, client_addr):
        """Check local zones first."""
        qname = str(request.q.qname).rstrip(".").lower()
        qtype = str(request.q.qtype)
        
        # Split domain into labels and check each parent zone
        labels = qname.split(".")
        
        for i in range(len(labels)):
            zone = ".".join(labels[i:])
            if zone in self.zones:
                for record in self.zones[zone]:
                    if record.get("host") in qname and record.get("type") == qtype:
                        reply = request.reply()
                        reply.add_answer(*RR.fromZone(
                            f"{qname}. {record.get('ttl', 300)} {record.get('type')} {record.get('value')}"
                        ))
                        return reply
        
        # Not in local zones - pass to next resolver
        if self.next_resolver:
            return self.next_resolver.resolve(request, client_addr)
        
        return None
```

### 4.9 Upstream Resolver

```python
# src/dnswarden/resolver/upstream.py
from dnslib import DNSRecord, QTYPE
import socket

class UpstreamResolver(BaseResolver):
    """Forward queries to upstream DNS servers.
    
    Supports multiple upstream servers with load balancing.
    Fallback on SERVFAIL.
    """
    
    def __init__(self, upstreams=None):
        # Default upstreams
        self.upstreams = upstreams or [
            ("1.1.1.1", 53),      # Cloudflare
            ("1.0.0.1", 53),      # Cloudflare
            ("8.8.8.8", 53),      # Google
        ]
        self.current = 0
    
    def resolve(self, request, client_addr):
        """Forward to upstream."""
        qname = str(request.q.qname)
        qtype = QTYPE[request.q.qtype]
        
        # Try each upstream in order
        for upstream in self.upstreams:
            try:
                response = self._forward(request, upstream)
                if response and response.header.rcode == 0:  # NOERROR
                    return response
            except Exception as e:
                continue
        
        # All failed - return SERVFAIL
        reply = request.reply()
        reply.header.rcode = 2  # SERVFAIL
        return reply
    
    def _forward(self, request, upstream):
        """Send query to upstream."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5.0)
        
        try:
            data = request.pack()
            sock.sendto(data, upstream)
            response_data, _ = sock.recvfrom(4096)
            return DNSRecord.parse(response_data)
        finally:
            sock.close()
```

---

## 5. API Design

### 5.1 Admin HTTP API

Server runs on `http://localhost:8080` by default.

#### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/status` | Server status |
| GET | `/api/queries` | Query logs |
| GET | `/api/queries/{id}` | Single query |
| GET | `/api/blockstats` | Block statistics |
| POST | `/api/blocklist/reload` | Reload blocklists |
| GET | `/api/config` | Current config |
| PUT | `/api/config` | Update config |
| POST | `/api/domains/add` | Add domain to blocklist |
| DELETE | `/api/domains/{domain}` | Remove from blocklist |

#### Response Format

```json
{
  "success": true,
  "data": {...},
  "timestamp": "2026-04-20T10:30:00Z"
}
```

#### Error Format

```json
{
  "success": false,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Query parameter required"
  }
}
```

### 5.2 Example API Calls

```bash
# Get server status
curl http://localhost:8080/api/status

# Get recent queries
curl http://localhost:8080/api/queries?limit=100

# Get block statistics
curl http://localhost:8080/api/blockstats

# Add domain to blocklist
curl -X POST http://localhost:8080/api/domains/add \
  -H "Content-Type: application/json" \
  -d '{"domain": "tracker.example.com"}'

# Reload blocklists
curl -X POST http://localhost:8080/api/blocklist/reload
```

---

## 6. Error Handling

### 6.1 Error Types

| Code | HTTP Status | Description |
|------|------------|-------------|
| INVALID_REQUEST | 400 | Malformed request |
| NOT_FOUND | 404 | Resource not found |
| RATE_LIMITED | 429 | Too many requests |
| SERVER_ERROR | 500 | Internal error |
| UNAVAILABLE | 503 | Service unavailable |

### 6.2 Implementation

```python
from enum import Enum

class ErrorCode(Enum):
    INVALID_REQUEST = "INVALID_REQUEST"
    NOT_FOUND = "NOT_FOUND"
    RATE_LIMITED = "RATE_LIMITED"
    SERVER_ERROR = "SERVER_ERROR"
    UNAVAILABLE = "UNAVAILABLE"

class APIError(Exception):
    def __init__(self, code, message, status=400):
        self.code = code
        self.message = message
        self.status = status
        super().__init__(message)
    
    def to_dict(self):
        return {
            "success": False,
            "error": {
                "code": self.code.value,
                "message": self.message
            }
        }

def handle_error(error):
    """Global error handler."""
    if isinstance(error, APIError):
        return json.dumps(error.to_dict()), error.status
    else:
        return json.dumps({
            "success": False,
            "error": {
                "code": "SERVER_ERROR",
                "message": str(error)
            }
        }), 500
```

### 6.3 DNS Error Codes

| Code | Value | Description |
|------|-------|-------------|
| NOERROR | 0 | No error (successful) |
| FORMERR | 1 | Format error |
| SERVFAIL | 2 | Server failure |
| NXDOMAIN | 3 | Name does not exist (blocked) |
| NOTIMP | 4 | Not implemented |
| REFUSED | 5 | Query refused |

---

## 7. Edge Cases

### 7.1 DNS Protocol Edge Cases

| Edge Case | Handling |
|----------|----------|
| **TCP truncation** | RFC 7766: Enable TCP, set TC flag when response >512 bytes |
| **EDNS0 (packet size)** | Support extended packet sizes up to 4096 bytes |
| **Duplicate queries** | Cache responses, handle with TXID matching |
| **Case insensitivity** | DNS is case-insensitive; normalize all domain names |
| **Empty queries** | Return FORMERR |
| **Unknown types** | Return NOERROR with empty answer (RFC 1035) |
| **IPv6 (AAAA)** | Return :: for blocked AAAA queries |
| **DNSSEC** | Forward or reject; validate if enabled |

### 7.2 Blocking Edge Cases

| Edge Case | Handling |
|----------|----------|
| **Subdomain wildcards** | Check each label in domain hierarchy |
| **IDN (unicode domains)** | Convert from punycode for matching |
| **Case variations** | Normalize to lowercase before check |
| **Trailing dots** | Strip trailing dot before matching |
| **Large blocklists** | Use hash table, lazy load, memory-map files |
| **Empty blocklist** | Skip check, forward immediately |

### 7.3 Performance Edge Cases

| Edge Case | Handling |
|----------|----------|
| **DNS amplification** | Require authentication, disable ANY queries |
| **Slow upstream** | 5-second timeout, failover to backup |
| **Cache exhaustion** | LRU eviction, max 10,000 entries |
| **Connection exhaustion** | Connection pooling with limits |
| **UDP packet loss** | Implement retry (client-side concern) |
| **High QPS** | Async I/O, worker threads |

### 7.4 Security Edge Cases

| Edge Case | Handling |
|----------|----------|
| **Spoofed source IP** | Rate limiting per source port + IP combo |
| **Cache poisoning** | Validate upstream responses |
| **DNS tunneling** | Inspect query lengths, block base32/hex patterns |
| **Reflection attack** | Drop responses to unknown sources |

---

## 8. Configuration

### 8.1 dnswarden.toml

```toml
# DNSWarden Configuration

[dns]
bind_address = "0.0.0.0"
port = 53

[upstream]
# Upstream DNS servers
hosts = [
    "1.1.1.1",
    "8.8.8.8"
]

# DNS-over-HTTPS (optional)
[dns.doh]
enabled = true
url = "https://cloudflare-dns.com/dns-query"

[blocklist]
enabled = true
sources = [
    "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts",
    "https://adaway.org/hosts.txt"
]
reload_interval = 86400  # 24 hours in seconds

[zones.local]
# Local zone definitions
local.lan = [
    {host = "server", type = "A", value = "192.168.1.10"},
    {host = "printer", type = "A", value = "192.168.1.20"}
]

[logging]
enabled = true
backend = "sqlite"  # sqlite, file, syslog
path = "/var/lib/dnswarden/logs.db"
level = "info"  # debug, info, warning, error

[security.ratelimit]
enabled = true
queries_per_second = 100
burst = 200

[security.allowlist]
enabled = false
file = "/etc/dnswarden/allowlist.txt"

[admin]
enabled = true
bind_address = "127.0.0.1"
port = 8080
```

### 8.2 Command Line Interface

```bash
# Start DNS server
dnswarden start

# Start with custom config
dnswarden start --config /etc/dnswarden/config.toml

# Update blocklists
dnswarden update-blocklists

# View logs
dnswarden logs --limit 100

# Reload configuration
dnswarden reload

# Stop server
dnswarden stop
```

---

## 9. Implementation Phases

### Phase 1: Core DNS Server (Week 1-2)

- [ ] Set up project structure
- [ ] Implement UDP/TCP handlers
- [ ] Basic resolver with logging
- [ ] Configuration loader
- [ ] Unit tests for core modules

### Phase 2: Blocking & Zones (Week 3)

- [ ] Blocklist resolver
- [ ] Wildcard matching
- [ ] Regex support
- [ ] Local zone resolver
- [ ] Blocklist update script

### Phase 3: DoH Proxy (Week 4)

- [ ] Upstream forwarding
- [ ] DoH client (RFC 8484)
- [ ] DoH-to-DNS proxy

### Phase 4: Logging & API (Week 5)

- [ ] SQLite logger
- [ ] File logger
- [ ] Admin HTTP API
- [ ] Query browser

### Phase 5: Security (Week 6)

- [ ] Rate limiter
- [ ] IP allowlist
- [ ] DNSSEC support (optional)

### Phase 6: Production Hardening (Week 7)

- [ ] Performance optimization
- [ ] Integration tests
- [ ] Documentation
- [ ] Packaging

---

## Appendix A: DNS Packet Structure

```
DNS Header (12 bytes)
+---------+---------+---------+---------+
| ID      | Flags   | QDCOUNT | ANCOUNT |
+---------+---------+---------+---------+
| NSCOUNT | ARCOUNT                    |
+---------+---------------------------+
```

### Header Flags

| Flag | Bit | Description |
|------|-----|-------------|
| QR | 15 | Query(0)/Response(1) |
| OPCODE | 11-14 | Operation code (0=QUERY) |
| AA | 10 | Authoritative answer |
| TC | 9 | Truncated |
| RD | 8 | Recursion desired |
| RA | 7 | Recursion available |
| Z | 6 | Reserved |
| RCODE | 0-3 | Response code |

---

## Appendix B: Record Types

| Type | Value | Description |
|------|-------|-------------|
| A | 1 | IPv4 address |
| NS | 2 | Name server |
| CNAME | 5 | Canonical name |
| SOA | 6 | Start of authority |
| PTR | 12 | Pointer |
| MX | 15 | Mail exchange |
| TXT | 16 | Text |
| AAAA | 28 | IPv6 address |
| SRV | 33 | Service |
| ANY | 255 | Any type |

---

## Appendix C: Logging Format

JSON query log entry:

```json
{
  "timestamp": "2026-04-20T10:30:00.123Z",
  "client_ip": "192.168.1.100",
  "client_port": 52341,
  "query_name": "ads.example.com",
  "query_type": "A",
  "response_code": 3,
  "response_size": 45,
  "protocol": "UDP",
  "latency_ms": 12.5,
  "blocked": true
}
```

---

## References

- [RFC 1035](https://rfc-editor.org/rfc/rfc1035.html) - Domain Names: Implementation and Specification
- [RFC 7766](https://rfc-editor.org/rfc/rfc7766.html) - DNS Transport over TCP
- [RFC 8484](https://rfc-editor.org/rfc/rfc8484.html) - DNS Queries over HTTPS
- [dnslib Documentation](https://github.com/paulc/dnslib)
- [Pi-hole Documentation](https://docs.pi-hole.net/)

---

*End of Implementation Plan*