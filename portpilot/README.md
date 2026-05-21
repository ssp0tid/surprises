# PortPilot

A Python CLI tool for port management with features for listing open ports, detecting conflicts, and managing port forwarding.

## Features

- **List Open Ports**: View all listening and established ports with process information using `ss` or `netstat`
- **Port Conflict Detection**: Identify ports being used by multiple processes
- **Port Forwarding Proxy**: Simple TCP port forwarding for development and testing
- **CLI Interface**: Built with Click for intuitive command-line usage
- **TUI Support**: Optional Textual-based terminal UI

## Installation

### Requirements

- Python 3.8+
- click
- textual (optional, for TUI)

### Install Dependencies

```bash
pip install click
pip install textual  # Optional, for TUI
```

### Installation Options

#### From Source

```bash
# Clone or download the repository
cd portpilot

# Install in development mode
pip install -e .

# Or install as a standalone script
chmod +x portpilot.py
./portpilot.py --help
```

## Usage

### List Ports

View all open ports with process information:

```bash
portpilot list
```

Output:
```
Protocol  Local Address      Port   State        PID    Process
--------------------------------------------------------------------------------
tcp       0.0.0.0            22     LISTEN       682    sshd
tcp       127.0.0.1          631    LISTEN       1001   cupsd
tcp       0.0.0.0            8000   LISTEN       1234   python
udp      0.0.0.0            68     UNKNOWN      -      dhclient
```

Options:
- `--json` / `-j`: Output as JSON
- `--protocol` / `-p`: Filter by protocol (tcp, udp, all)
- `--state` / `-s`: Filter by state (listening, established, all)

### Check Port Conflicts

Detect ports being used by multiple processes:

```bash
portpilot conflicts
```

Check a specific port:

```bash
portpilot conflicts 8080
```

### Check Port Availability

Check if a specific port is available:

```bash
portpilot check 8080
```

Find an available port in a range:

```bash
portpilot available --start 8000 --end 9000
```

### Port Forwarding

Start a port forwarder:

```bash
portpilot forward add 8080 localhost 3000
```

This forwards all incoming connections on port 8080 to localhost:3000.

List active forwarders:

```bash
portpilot forward list
```

Stop a forwarder:

```bash
portpilot forward remove 8080
```

Stop all forwarders:

```bash
portpilot forward stop
```

### Textual TUI (Optional)

Launch the terminal UI:

```bash
portpilot tui
```

Requires `textual` to be installed.

## Configuration

### Using as a Python Module

```python
from portpilot.scanner import get_open_ports, check_port_available
from portpilot.proxy import get_manager

# Get open ports
ports = get_open_ports()
for port in ports:
    print(f"{port.local_port}: {port.process_name}")

# Start a forwarder
manager = get_manager()
manager.start_forwarder(8080, 'localhost', 3000)
```

## Command Reference

| Command | Description |
|---------|-------------|
| `portpilot list` | List all open ports |
| `portpilot conflicts [PORT]` | Detect port conflicts |
| `portpilot check PORT` | Check if port is available |
| `portpilot available` | Find available port |
| `portpilot forward add SOURCE DEST` | Add port forwarder |
| `portpilot forward remove PORT` | Remove port forwarder |
| `portpilot forward list` | List active forwarders |
| `portpilot tui` | Launch TUI (optional) |

## Development

### Running Tests

```bash
python -m pytest
```

### Code Style

The project uses standard Python conventions. Run linters as needed.

## License

MIT License

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.