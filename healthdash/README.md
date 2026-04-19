# HealthDash

Self-Hosted Service Health Dashboard - Monitor HTTP endpoints for uptime, response time, and status history.

## Features

- Monitor HTTP endpoints with configurable intervals
- Track response times and uptime percentage
- Dark-themed web UI
- REST API for automation
- Background health checks with APScheduler

## Requirements

- Python 3.10+
- SQLite (included)

## Installation

### 1. Clone and create virtual environment

```bash
git clone <your-repo>
cd healthdash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate   # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

Edit `.env` and set a secure SECRET_KEY:

```
SECRET_KEY=your-secure-random-key-here
```

### 4. Initialize database (optional - runs automatically)

```bash
python3 -c "from healthdash import create_app; from healthdash.models import db; app = create_app(); app.app_context().push(); db.create_all()"
```

## Running

### Development

```bash
python3 run.py
```

Access at http://localhost:5000

### Production

```bash
gunicorn -c gunicorn_config.py "healthdash:create_app('production')"
```

## Usage

### Web UI

1. Click "Add Service" to add a new endpoint to monitor
2. Configure the URL, check interval, and expected status
3. View dashboards and details on the main page

### REST API

```bash
# List services
curl http://localhost:5000/api/v1/services

# Add service
curl -X POST http://localhost:5000/api/v1/services \
  -H "Content-Type: application/json" \
  -d '{"name": "My API", "url": "https://api.example.com/health"}'

# Get service stats
curl http://localhost:5000/api/v1/services/1/stats

# Trigger check
curl -X POST http://localhost:5000/api/v1/services/1/check
```

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/services | List all services |
| POST | /api/v1/services | Create new service |
| GET | /api/v1/services/<id> | Get service details |
| PUT | /api/v1/services/<id> | Update service |
| DELETE | /api/v1/services/<id> | Delete service |
| GET | /api/v1/services/<id>/checks | Get check history |
| GET | /api/v1/services/<id>/stats | Get uptime stats |
| POST | /api/v1/services/<id>/check | Trigger check |
| GET | /api/v1/health | API health check |

## Testing

```bash
pip install -r requirements-dev.txt
pytest
```

## License

MIT