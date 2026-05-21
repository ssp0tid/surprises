# DevDash - Local Developer Dashboard

DevDash is a Flask web application that discovers and monitors local development servers (Node.js, Python, Go, etc.) running on common localhost ports. It provides a beautiful real-time dashboard with CPU and memory usage for each service.

![DevDash Dashboard](https://via.placeholder.com/800x400?text=DevDash+Dashboard)

## Features

- **Auto-Discovery**: Automatically detects dev servers running on ports 3000-9000
- **Real-Time Monitoring**: Shows live CPU and memory usage for each service
- **Modern UI**: Built with TailwindCSS for a clean, responsive design
- **Process Detection**: Identifies Node.js, Python, Flask, FastAPI, Go, Java, Ruby, and PHP servers
- **Quick Actions**: Direct links to open each service in your browser
- **Auto-Refresh**: Updates every 5 seconds with tab visibility handling

## Installation

```bash
# Navigate to the project directory
cd /path/to/devdash

# Create virtual environment (optional but recommended)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# OR install without activating (using venv directly):
# ./venv/bin/pip install -r requirements.txt
```

## Usage

```bash
# Start the development server
python run.py

# OR run with the venv Python directly (no activation needed):
# ./venv/bin/python run.py
```

The dashboard will be available at http://127.0.0.1:7890

## Configuration

Edit `config.yaml` to customize:

- **Server host/port**: Change where DevDash binds
- **Discovery ports**: Add or remove ports to scan
- **Process blacklist**: Skip specific processes

```yaml
devdash:
  host: "127.0.0.1"
  port: 7890
  debug: false

discovery:
  scan_interval: 5
  ports:
    - 3000    # Node.js
    - 5173    # Vite
    - 5000    # Flask
    - 8000    # Django
    - 8080    # Go/Java
  process_blacklist:
    - chrome
    - firefox
```

## Common Ports

| Port | Framework/Server |
|------|-----------------|
| 3000 | Node.js (Express, etc.) |
| 5173 | Vite |
| 5000 | Flask |
| 5173 | Vite |
| 8000 | Django/FastAPI |
| 8080 | Go/Java |
| 8888 | Jupyter |

## API Endpoints

- `GET /api/services` - List all discovered services
- `GET /api/services/<id>` - Get service details
- `GET /api/ports` - List ports in use
- `GET /api/system` - System-wide statistics

## Development

```bash
# Run in development mode with auto-reload
FLASK_DEBUG=true python run.py

# Or use flask run
flask --app devdash.app run
```

## Tech Stack

- **Backend**: Flask 3.x
- **Process Monitoring**: psutil
- **Frontend**: TailwindCSS (via CDN)
- **Real-time**: WebSocket ready (Flask-SocketIO installed)

## License

MIT License - feel free to use for your local development needs.