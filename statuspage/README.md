# StatusPage

A self-hosted status page application for monitoring your services and communicating uptime to users.

## Features

- **Public Status Page**: Display real-time status of your services
- **Component Monitoring**: Track individual service components
- **Incident Management**: Create and manage status incidents
- **Uptime Tracking**: Historical uptime data (24h, 7d, 30d)
- **Custom Branding**: Logo, colors, and custom CSS
- **Organization Management**: Multi-tenant support

## Quick Start

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python run.py
```

### Configuration

The application can be configured using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `development` | Environment (development/production) |
| `SECRET_KEY` | auto-generated | Secret key for sessions |
| `DATABASE_URL` | SQLite | Database connection string |
| `PORT` | 5000 | Port to run the server on |

### First Run

1. Run `python run.py`
2. Open http://localhost:5000
3. Register your organization
4. Add components to monitor
5. Your public status page will be at `/status/<org-slug>`

## Project Structure

```
statuspage/
├── app/
│   ├── __init__.py      # Flask app factory
│   ├── auth.py          # Authentication routes
│   ├── config.py        # Configuration
│   ├── forms.py         # WTForms
│   ├── models.py        # SQLAlchemy models
│   ├── routes/
│   │   ├── admin.py     # Admin dashboard
│   │   ├── api.py       # REST API
│   │   └── status.py    # Public status pages
│   ├── services/
│   │   ├── health_checker.py
│   │   └── scheduler.py
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   ├── templates/
│   │   ├── admin/       # Admin templates
│   │   ├── auth/        # Auth templates
│   │   └── status/      # Public status templates
│   └── utils/
│       └── helpers.py
├── run.py               # Entry point
└── requirements.txt
```

## Usage

### Admin Dashboard

Access the admin dashboard at `/admin` after logging in.

- **Components**: Add and manage services to monitor
- **Groups**: Organize components into groups
- **Incidents**: Create and manage status incidents
- **Settings**: Configure organization branding

### Public Status Page

Public pages are available at:
- `/status/<org-slug>` - Main status page
- `/status/<org-slug>/history` - Historical uptime data
- `/status/<org-slug>/incident/<id>` - Incident details

## Development

```bash
# Run in development mode
python run.py

# Run tests (if available)
pytest
```

## License

MIT
