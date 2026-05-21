# Git Activity Dashboard - Implementation Plan

## 1. Project Overview

**Project Name:** Git Activity Dashboard  
**Type:** Flask Web Application  
**Core Functionality:** Analyzes local git repositories to visualize commit history, contributor statistics, file change trends, activity heatmaps, commit message patterns, and branch information.  
**Target Users:** Developers, team leads, and project managers who want insights into repository activity.

---

## 2. Technology Stack

| Layer | Technology |
|-------|------------|
| Backend | Flask 3.x with Python 3.11+ |
| Git Operations | GitPython |
| Data Processing | Pandas |
| Frontend | Bootstrap 5 + Chart.js |
| Templating | Jinja2 (built into Flask) |
| Testing | pytest |
| Deployment | Gunicorn (production) |

### Core Dependencies

```txt
Flask>=3.0.0
GitPython>=3.1.40
Pandas>=2.0.0
Gunicorn>=21.0.0
python-dateutil>=2.8.0
```

---

## 3. File Structure

```
git-activity-dashboard/
├── app/
│   ├── __init__.py              # Flask factory
│   ├── config.py                # Configuration
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── main.py              # Home, repository selection
│   │   ├── api.py               # REST API endpoints
│   │   └── errors.py            # Error handlers
│   ├── services/
│   │   ├── __init__.py
│   │   ├── git_analyzer.py      # Core git analysis logic
│   │   ├── commit_analyzer.py   # Commit-specific analysis
│   │   ├── contributor_analyzer.py
│   │   └── file_analyzer.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── repository.py        # Data models
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── cache.py             # Result caching
│   │   └── validators.py        # Input validation
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── dashboard.html
│       └── partials/
│           ├── commits.html
│           ├── contributors.html
│           ├── heatmap.html
│           ├── branches.html
│           └── messages.html
├── tests/
│   ├── __init__.py
│   ├── test_routes/
│   ├── test_services/
│   └── fixtures/
├── static/
│   ├── css/
│   │   └── custom.css
│   └── js/
│       ├── charts.js
│       ├── heatmap.js
│       └── utils.js
├── repos/                       # Demo repositories (optional)
├── .gitignore
├── requirements.txt
├── config.yaml                  # App configuration
├── run.py                       # Development entry
└── gunicorn_config.py           # Production entry
```

---

## 4. Data Models

### Repository Info
```python
@dataclass
class Repository:
    path: str
    name: str
    is_valid: bool
    branch_count: int
    total_commits: int
    contributors: List[Contributor]
    first_commit_date: datetime
    last_commit_date: datetime
```

### Commit Data
```python
@dataclass
class CommitInfo:
    sha: str
    short_sha: str
    author: Contributor
    committer: Contributor
    message: str
    message_first_line: str
    date: datetime
    changed_files: int
    insertions: int
    deletions: int
    branches: List[str]  # Which branches contain this commit
```

### Contributor Stats
```python
@dataclass
class Contributor:
    name: str
    email: str
    commit_count: int
    first_commit: datetime
    last_commit: datetime
    insertions: int
    deletions: int
```

### Activity Data (for heatmaps)
```python
@dataclass
class ActivityHour:
    hour: int          # 0-23
    day: int           # 0-6 (Mon-Sun)
    commit_count: int
```

---

## 5. API Design

### REST Endpoints

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

### Request/Response Formats

#### GET /api/repos
```json
{
  "repos": [
    {"path": "/path/to/repo1", "name": "repo1", "valid": true},
    {"path": "/path/to/repo2", "name": "repo2", "valid": false, "error": "Not a git repo"}
  ]
}
```

#### GET /api/repo/{path}/commits
```json
{
  "commits": [...],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 1000,
    "pages": 20
  }
}
```

---

## 6. Core Features Implementation

### 6.1 Repository Validation
- Check if directory exists
- Verify `.git` folder exists
- Test `git rev-parse --git-dir`

### 6.2 Commit History Analysis
- Use `repo.iter_commits()` with `max_count` for pagination
- Extract: sha, author, date, message, stats
- Support date range filtering

### 6.3 Contributor Statistics
- Group commits by author email
- Calculate: commit count, lines added/removed, activity span
- Sort by commit count (descending)

### 6.4 Activity Heatmap
- Build 7x24 matrix (day x hour)
- Aggregate commit counts per time slot
- Return as JSON for frontend visualization

### 6.5 File Change Trends
- Track file modifications over time
- Identify most frequently changed files
- Calculate: total changes, additions, deletions per file

### 6.6 Branch Statistics
- List all branches (local and remote)
- Get last commit for each branch
- Calculate branch age and commit distance from main

### 6.7 Commit Message Analysis
- Extract first line as "subject"
- Categorize: feature, fix, docs, refactor, etc.
- Word frequency analysis (exclude stop words)
- Message length distribution

---

## 7. Error Handling

### HTTP Error Codes
| Code | Meaning | Cause |
|------|---------|-------|
| 400 | Bad Request | Invalid path encoding, missing params |
| 404 | Not Found | Repository doesn't exist |
| 422 | Unprocessable | Invalid repository (not git) |
| 500 | Server Error | GitPython failures, internal errors |

### Error Response Format
```json
{
  "error": {
    "code": "REPO_NOT_FOUND",
    "message": "Repository path does not exist",
    "details": "/path/to/repo"
  }
}
```

### Exception Handling Strategy
```python
# In app/routes/api.py
@app.errorhandler(GitError)
def handle_git_error(e):
    return jsonify({"error": str(e)}), 422

@app.errorhandler(RepositoryNotFoundError)
def handle_not_found(e):
    return jsonify({"error": str(e)}), 404
```

---

## 8. Edge Cases

### Path Handling
- URL-encode repository paths in API calls
- Validate path traversal attempts (`../../`)
- Handle spaces and special characters in paths

### Large Repositories
- Implement pagination (default 50 commits per page)
- Cache expensive computations with TTL
- Limit date range queries
- Add timeout for git operations (30s default)

### Empty Repositories
- Return empty arrays, not errors
- Show appropriate "no data" messages

### Corrupted Repositories
- Catch `GitError` exceptions
- Provide meaningful error messages

### Non-ASCII Content
- Handle commit messages in any encoding
- Support UTF-8 file contents

### Detached HEAD / No Branches
- Handle `HEAD` in detached state
- Show current commit info even with no branches

### Merged / Deleted Branches
- Handle branches that no longer exist
- Track commit presence across branches

---

## 9. Frontend Design

### Pages

1. **Home (`/`)** - Repository selection
   - Input field for repository path
   - List of recently analyzed repos (localStorage)

2. **Dashboard (`/dashboard/<path>`)** - Main view
   - Repository info header
   - Tab navigation for different views

### Dashboard Tabs

| Tab | Content |
|-----|---------|
| Overview | Summary stats, recent activity |
| Commits | Paginated commit list with filters |
| Contributors | Leaderboard, activity charts |
| Activity | Heatmap visualization |
| Files | Changed files, trends |
| Branches | Branch list, age, status |
| Messages | Word cloud, categories |

### Chart Configurations (Chart.js)

- **Commit Timeline:** Line chart, commits over time
- **Contributor Stats:** Bar chart, top 10 contributors
- **Activity Heatmap:** Custom canvas rendering
- **File Changes:** Horizontal bar chart
- **Message Categories:** Doughnut chart

---

## 10. Caching Strategy

```python
# Cache TTLs
CACHE_TTL = {
    "repo_info": 300,       # 5 minutes
    "commits": 60,          # 1 minute
    "contributors": 300,    # 5 minutes
    "activity": 300,        # 5 minutes
    "files": 300,           # 5 minutes
}
```

- Use in-memory cache (Flask-Caching or simple dict)
- Key: `{repo_path}_{endpoint}_{params}`
- Invalidate on repository write (post-commit hook not needed for read-only)

---

## 11. Security Considerations

1. **Path Validation**
   - Prevent directory traversal
   - Restrict to allowed directories (configurable)
   
2. **Repository Access**
   - Read-only operations only
   - No code execution from repo contents

3. **API Rate Limiting** (future)
   - Limit requests per minute
   - Cache responses aggressively

---

## 12. Testing Strategy

### Unit Tests
- Service layer functions
- Data transformation logic
- Validation functions

### Integration Tests
- API endpoints with mock git repos
- Response format validation

### Fixtures
- Sample git repositories with known history
- Pre-generated commit data

### Test Commands
```bash
pytest tests/ -v
pytest --cov=app tests/
```

---

## 13. Configuration (config.yaml)

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

---

## 14. Development & Deployment

### Development
```bash
# Create venv
python -m venv venv
source venv/bin/activate

# Install
pip install -r requirements.txt

# Run
python run.py
```

### Production
```bash
# Install production deps
pip install gunicorn

# Run with gunicorn
gunicorn -c gunicorn_config.py "app:create_app()"
```

---

## 15. Acceptance Criteria

- [ ] User can enter a local repository path
- [ ] Dashboard displays repository overview
- [ ] Commit history shows with pagination
- [ ] Contributor statistics calculated and displayed
- [ ] Activity heatmap renders correctly
- [ ] File change statistics available
- [ ] Branch information displayed
- [ ] Commit message analysis works
- [ ] Invalid repos show appropriate errors
- [ ] Large repos don't timeout
- [ ] Responsive design works on mobile