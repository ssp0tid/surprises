# ServiceMap

A Flask-based local network service discovery and visualization tool.

## Features

- **mDNS/DNS-SD Discovery**: Discovers services advertised via Bonjour/Avahi on your local network
- **Port Scanning**: Scans hosts for open ports with service identification
- **Topology Visualization**: Interactive network graph showing discovered services

## Requirements

- Python 3.8+
- `avahi-utils` (optional, for enhanced mDNS discovery): Install with `sudo apt install avahi-utils`

## Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Optional: Install avahi utilities for full mDNS discovery support
# Ubuntu/Debian:
sudo apt install avahi-utils

# macOS:
# mDNS utilities are included by default

# Fedora/RHEL:
sudo dnf install avahi-tools
```

## Usage

Start the web application:

```bash
python app.py
```

Open your browser to `http://localhost:5000` to access the ServiceMap dashboard.

### Controls

- **Start Scan**: Begin network service discovery
- **Host (optional)**: Specify a target host for port scanning
- **Timeout**: Maximum time to wait for responses (1-30 seconds)
- **Port Range**: Range of ports to scan (e.g., 1-1024)

## Configuration

### Common Service Ports

The port scanner includes identification for common services:

| Port | Service |
|------|---------|
| 21   | FTP     |
| 22   | SSH     |
| 80   | HTTP    |
| 443  | HTTPS   |
| 3306 | MySQL   |
| 5432 | PostgreSQL |
| 6379 | Redis   |
| 27017| MongoDB |

### mDNS Service Types

The scanner can discover these common service types:

- `_http._tcp.local` - HTTP services
- `_ssh._tcp.local` - SSH services
- `_ftp._tcp.local` - FTP services
- `_sftp-ssh._tcp.local` - SFTP services
- `_smb._tcp.local` - Windows file sharing
- `_airplay._tcp.local` - AirPlay devices
- `_hap._tcp.local` - HomeKit devices
- `_printer._tcp.local` - Printers

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard |
| `/api/scan` | POST | Start network scan |
| `/api/services` | GET | Get discovered services |
| `/api/scan/port` | POST | Scan specific host ports |

### Example: Start Scan via API

```bash
curl -X POST http://localhost:5000/api/scan \
  -H "Content-Type: application/json" \
  -d '{"timeout": 5, "port_range": [1, 1024]}'
```

### Example: Query Services

```bash
curl http://localhost:5000/api/services
```

## File Structure

```
servemap/
├── app.py              # Main Flask application
├── scanner.py          # Service discovery modules
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html     # Web UI template
└── README.md          # This file
```

## Security Considerations

- **Network Access**: The web server listens on all interfaces (`0.0.0.0`). Consider restricting access in production.
- **Port Scanning**: Port scanning may be restricted or prohibited on some networks. Use responsibly.
- **Firewall**: Ensure your firewall allows mDNS (port 5353/UDP) and the ports you want to scan.

## Troubleshooting

### No services discovered

1. Ensure `avahi-utils` is installed: `which avahi-browse`
2. Check that mDNS is enabled on your system
3. Try a longer timeout value
4. Verify you're on a network with other devices

### Port scan fails

1. Verify the target host is reachable
2. Check firewall rules on the target host
3. Ensure proper permissions (may require root for raw sockets)

## License

MIT License