# MockFlow - HTTP Mock Designer

A visual web-based HTTP mock API designer for creating, managing, and testing mock API endpoints.

## Features

- Create and manage mock API endpoints (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS)
- Path parameters support (e.g., `/users/:id`)
- Multiple response variants per endpoint with conditional logic
- Dynamic variables: `{{uuid}}`, `{{timestamp}}`, `{{random.number}}`, `{{random.string}}`
- Request matching by headers, query params, and body content
- Response latency simulation
- Request logging and inspection
- Import from OpenAPI/Swagger and Postman collections
- Start/stop mock server per project

## Setup

### Prerequisites

- Python 3.9+

### Installation

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python run.py
```

The app will be available at http://localhost:5000

### Using Gunicorn (Production)

```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|----------|-------------|
| `PORT` | 5000 | Flask server port |
| `FLASK_DEBUG` | true | Enable debug mode |
| `DATABASE_URL` | sqlite:///mockflow.db | Database connection |
| `SECRET_KEY` | dev-secret-key | Flask secret key |
| `LOG_RETENTION_DAYS` | 7 | Log retention days |

## API Endpoints

### Projects

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/projects` | List all projects |
| GET | `/api/projects/{id}` | Get project |
| POST | `/api/projects` | Create project |
| PUT | `/api/projects/{id}` | Update project |
| DELETE | `/api/projects/{id}` | Delete project |

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/projects/{id}/endpoints` | List endpoints |
| GET | `/api/endpoints/{id}` | Get endpoint |
| POST | `/api/projects/{id}/endpoints` | Create endpoint |
| PUT | `/api/endpoints/{id}` | Update endpoint |
| DELETE | `/api/endpoints/{id}` | Delete endpoint |

### Responses

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/endpoints/{id}/responses` | List responses |
| POST | `/api/endpoints/{id}/responses` | Create response |
| PUT | `/api/responses/{id}` | Update response |
| DELETE | `/api/responses/{id}` | Delete response |

### Server Control

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/projects/{id}/server` | Get server status |
| POST | `/api/projects/{id}/server/start` | Start mock server |
| POST | `/api/projects/{id}/server/stop` | Stop mock server |

### Logs

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/projects/{id}/logs` | Get request logs |
| DELETE | `/api/projects/{id}/logs` | Clear logs |

## Dynamic Variables

Response body supports variables:

| Variable | Description |
|----------|-------------|
| `{{uuid}}` | Random UUID |
| `{{timestamp}}` | ISO timestamp |
| `{{timestamp.unix}}` | Unix timestamp |
| `{{random.number}}` | Random number (1-100) |
| `{{random.string}}` | Random string (8 chars) |
| `{{request.body.field}}` | From request body |
| `{{request.query.param}}` | From query params |

## Example

1. Create a project named "My API"
2. Add endpoint: `GET /api/users/:id`
3. Response body:
```json
{
  "id": "{{request.params.id}}",
  "name": "User {{random.string}}",
  "created_at": "{{timestamp}}"
}
```
4. Start server and test:
```bash
curl http://localhost:8080/api/users/123
```

## License

MIT