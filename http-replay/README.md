# HTTP Replay Server

A local CLI tool that records HTTP requests to SQLite, provides a web UI to view/search, and allows replay with variable substitution.

## Features

- **HTTP Proxy Server**: Run as a transparent proxy to record all HTTP traffic
- **SQLite Storage**: All requests and responses stored in local SQLite database
- **Web UI**: Browse, search, and filter recorded requests with a modern web interface
- **Replay with Variables**: Replay requests with variable substitution using `{{variableName}}` syntax
- **Header Modification**: Modify headers during replay
- **Delay Injection**: Add configurable delays to test timing-sensitive scenarios
- **Full Request/Response Details**: View headers, body, status codes, and timing

## Installation

```bash
# Clone or navigate to the project directory
cd http-replay

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Start Both Proxy and Web UI

```bash
python app.py run --port 8080 --web-port 5000
```

This starts:
- Proxy server on `http://127.0.0.1:8080`
- Web UI on `http://127.0.0.1:5000`

### Run Proxy Only (for recording)

```bash
python app.py proxy --port 8080 --target-host example.com --target-port 80
```

### Run Web UI Only

```bash
python app.py web --port 5000
```

### CLI Commands

```bash
# List all recordings
python app.py list

# Search recordings
python app.py list --search /api/users

# Filter by method
python app.py list --method POST

# Show recording details
python app.py show <uuid>

# Replay a recording with variables
python app.py replay <uuid> --variables '{"userId": 123, "apiKey": "new-key"}'

# Replay with header modifications
python app.py replay <uuid> --headers '{"Authorization": "Bearer new-token"}'

# Replay with delay
python app.py replay <uuid> --delay 1000

# Show statistics
python app.py stats

# Delete a recording
python app.py delete <uuid>
```

## Variable Substitution

Use `{{variableName}}` syntax in URLs or request bodies to substitute values during replay:

```bash
# Record a request with placeholder
# Original URL: /api/users/{{userId}}/posts

# Replay with substitution
python app.py replay <uuid> --variables '{"userId": 42}'
```

## Web UI

The web UI provides:

- **Dashboard**: View recording statistics
- **Search**: Search by URL, path, or notes
- **Filter**: Filter by HTTP method
- **View Details**: See full request/response with headers and body
- **Edit**: Add notes and tags to recordings
- **Replay**: Execute replay with variable substitution
- **Delete**: Remove unwanted recordings

## Database

The SQLite database (`recordings.db` by default) contains:

- `recordings`: All HTTP request/response pairs
- `replay_configs`: Saved replay configurations

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `--port` | 8080 | Proxy server port |
| `--web-port` | 5000 | Web UI port |
| `--target-host` | localhost | Default target for proxy |
| `--target-port` | 80 | Default target port |
| `--db-path` | recordings.db | SQLite database path |

## Examples

### Recording API Calls

```bash
# Start proxy
python app.py proxy --port 8080 --target-host api.example.com --target-port 443

# Configure your app to use proxy http://127.0.0.1:8080
# Make API calls - they will be recorded

# View recordings via web UI
python app.py web
```

### Testing with Replay

```bash
# Replay a recorded login request with different credentials
python app.py replay <login-uuid> --variables '{"username": "testuser", "password": "testpass"}'

# Load test: replay with delays
for i in {1..10}; do python app.py replay <uuid> --delay 100; done
```

### Analyzing Traffic

```bash
# View recent POST requests
python app.py list --method POST --limit 50

# Show full details
python app.py show <uuid>
```

## License

MIT License