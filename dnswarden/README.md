# DNSWarden

A local DNS server with custom domain resolution, ad/tracker blocking, DNS-over-HTTPS proxy, and query logging.

## Features

- **Local DNS Server** - Run on port 53 (requires root), handle UDP/TCP
- **Custom Resolution** - Local zone files, static mappings
- **Ad/Tracker Blocking** - Blocklist-based domain filtering with wildcard support
- **DoH Proxy** - Forward client queries to upstream DoH servers (RFC 8484)
- **Query Logging** - JSON logs to SQLite/file, optional syslog
- **Rate Limiting** - Prevent DNS amplification attacks
- **IP Allowlist** - Restrict access to trusted networks

## Requirements

- Python 3.10+
- Root privileges (for port 53)

## Installation

### From Source

```bash
git clone https://github.com/yourorg/dnswarden.git
cd dnswarden
pip install -r requirements.txt
pip install -e .
```

### Quick Start

```bash
# Edit configuration
vi config/config.yaml

# Run the server (requires root)
sudo dnswarden start
```

## Configuration

Edit `config/config.yaml`:

```yaml
server:
  bind_address: "0.0.0.0"
  port: 53

upstream:
  - host: "1.1.1.1"
    port: 53
  - host: "8.8.8.8"
    port: 53

doh:
  enabled: true
  url: "https://cloudflare-dns.com/dns-query"

blocklists:
  enabled: true
  sources:
    - url: "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts"

logging:
  enabled: true
  backend: "sqlite"
  path: "/var/lib/dnswarden/logs.db"

security:
  rate_limit:
    enabled: true
    queries_per_second: 100
    burst: 200

admin:
  enabled: true
  bind_address: "127.0.0.1"
  port: 8080
```

## Usage

### CLI Commands

```bash
# Start DNS server
sudo dnswarden start

# Start with custom config
sudo dnswarden start --config /path/to/config.yaml

# Stop server
dnswarden stop
```

### Admin API

The admin API runs on port 8080 by default:

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

## Local Zones

Define local zones in `config/zones/local.zone`:

```yaml
zones:
  local.lan:
    - host: server
      type: A
      value: 192.168.1.10
      ttl: 300
    - host: printer
      type: A
      value: 192.168.1.20
      ttl: 300
```

## Blocklists

Blocklist files are stored in `/etc/dnswarden/blocklists/` (or configured directory).
Each `.txt` file contains one domain per line:

```
ads.example.com
tracker.example.com
*.ads.example.com
```

## Architecture

```
┌─────────────────────────────────────┐
│           DNSWarden                  │
├─────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌────────┐ │
│  │   UDP   │ │   TCP   │ │  DoH   │ │
│  │ Server  │ │ Server  │ │ Proxy  │ │
│  └────┬────┘ └────┬────┘ └───┬────┘ │
│       └──────────┼────────────┘      │
│                  │                   │
│           ┌──────▼──────┐           │
│           │  Resolver   │           │
│           │  Pipeline  │           │
│           └──────┬──────┘           │
│       ┌─────────┼─────────┐        │
│  ┌────▼────┐ ┌──▼────┐ ┌──▼─────┐ │
│  │Blocklist│ │ Local │ │Upstream│ │
│  │ Filter │ │ Zones │ │Forward │ │
│  └────────┘ └───────┘ └────────┘ │
└─────────────────────────────────────┘
```

## Security Notes

- Run as non-root user with capability `cap_net_bind_service+ep` for port 53
- Enable rate limiting in production
- Use IP allowlist for trusted networks
- Keep blocklists updated

## Troubleshooting

### Port 53 Permission Denied

```bash
# Option 1: Run with sudo
sudo dnswarden start

# Option 2: Set capability
sudo setcap 'cap_net_bind_service+ep' /usr/bin/python3.10
```

### Check Logs

```bash
# View logs
tail -f /var/log/dnswarden/queries.jsonl

# Or query SQLite
sqlite3 /var/lib/dnswarden/logs.db "SELECT * FROM dns_queries LIMIT 10;"
```

## License

MIT