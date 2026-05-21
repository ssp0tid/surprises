# Git Activity Dashboard

A Flask web application that analyzes local git repositories to visualize commit history, contributor statistics, file change trends, activity heatmaps, commit message patterns, and branch information.

## Features

- **Repository Overview** - Summary stats, recent activity
- **Commit History** - Paginated commit list with filters
- **Contributor Statistics** - Leaderboard, activity charts
- **Activity Heatmap** - Visualize commits by day/hour
- **File Changes** - Most frequently changed files, trends
- **Branch Information** - Branch list, age, status
- **Commit Messages** - Word cloud, categories

## Requirements

- Python 3.11+
- Git

## Installation

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure (Optional)

Edit `config.yaml` to customize settings:

```yaml
app:
  host: "0.0.0.0"
  port: 5000
  debug: false

repositories:
  allowed_paths:
    - "/home/user/repos"
    - "/var/git"
  default_path: "/home/user/repos"

analysis:
  default_page_size: 50
  max_page_size: 200
  timeout_seconds: 30

cache:
  enabled: true
  ttl_minutes: 5
```

## Running

### Development

```bash
python run.py
```

The app will be available at `http://localhost:5000`

### Production

```bash
pip install gunicorn
gunicorn -c gunicorn_config.py "app:create_app()"
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/repos` | List available local repositories |
| GET | `/api/repo/<path>/info` | Repository overview stats |
| GET | `/api/repo/<path>/commits` | Paginated commit history |
| GET | `/api/repo/<path>/contributors` | Contributor statistics |
| GET | `/api/repo/<path>/activity` | Hourly/daily activity data |
| GET | `/api/repo/<path>/files` | File change statistics |
| GET | `/api/repo/<path>/branches` | Branch information |
| GET | `/api/repo/<path>/messages` | Commit message analysis |

Note: Repository paths should be URL-encoded when used in API calls.

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | Bad Request - Invalid path or parameters |
| 404 | Not Found - Repository doesn't exist |
| 422 | Unprocessable - Invalid repository (not a git repo) |
| 500 | Server Error - Internal error |

## Project Structure

```
git-activity-dashboard/
├── app/
│   ├── __init__.py          # Flask factory
│   ├── config.py            # Configuration
│   ├── routes/             # API and pages
│   ├── services/           # Git analysis logic
│   ├── models/            # Data models
│   ├── utils/              # Cache and validators
│   └── templates/          # Jinja2 templates
├── static/                # CSS and JS
├── tests/                 # Tests (placeholder)
├── repos/                 # Demo repositories (optional)
├── requirements.txt        # Python dependencies
├── config.yaml            # App configuration
├── run.py               # Development entry
└── gunicorn_config.py    # Production config
```

## License

MIT