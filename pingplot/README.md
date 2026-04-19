# PingPlot

Network latency visualizer that pings hosts and displays ASCII sparkline graphs with colored output.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python pingplot.py -H google.com -c 10
```

### Options

- `-H, --host HOST` - Host to ping (required)
- `-c, --count COUNT` - Number of pings to send (default: 5)
- `--csv FILE` - Output results to CSV file
- `--help` - Show help message

## Features

- ASCII sparkline visualization
- Colored output based on latency (green = fast, red = slow)
- Packet loss percentage display
- CSV export for further analysis
- Handles host not found and ping command missing errors
