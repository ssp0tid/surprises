# DockerWatch

Real-time Docker container monitoring dashboard with TUI interface.

## Prerequisites

- Go 1.21 or later
- Docker daemon running (local socket or TCP)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/dockerwatch.git
cd dockerwatch

# Download dependencies
go mod download

# Build
make build

# Or directly:
go build -o dockerwatch ./cmd/dockerwatch
```

## Usage

```bash
# Run the application
./dockerwatch

# Or with make:
make run
```

## Configuration

Edit `config.yaml` to customize:

- `docker.host` - Docker socket path or TCP address (default: local socket)
- `docker.timeout` - API request timeout
- `ui.theme` - UI theme (dark, light, auto)
- `ui.show_stopped` - Display stopped containers
- `shortcuts.*` - Custom keyboard shortcuts

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `q` | Quit |
| `?` | Help |
| `r` | Refresh |
| `↑/↓` | Navigate containers |
| `Enter` | View container details |
| `s` | Start container |
| `x` | Stop container |
| `l` | View logs |

## Project Structure

```
dockerwatch/
├── cmd/dockerwatch/      # Entry point
├── internal/
│   ├── config/           # Configuration
│   ├── docker/           # Docker client
│   ├── models/           # Data models
│   ├── tui/              # TUI components
│   └── utils/            # Utilities
├── config.yaml           # Default config
└── Makefile              # Build automation
```

## License

MIT