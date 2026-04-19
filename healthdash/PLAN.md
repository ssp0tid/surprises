# HealthDash — Implementation Plan

## 1. Project Overview

**Project Name:** HealthDash  
**Type:** Self-Hosted Service Health Dashboard  
**Technology Stack:** Python 3.10+ / Flask / SQLite  
**Core Functionality:** Monitor HTTP endpoints/services for uptime, response time, and status history with a clean dark-themed UI and REST API.

---

## 2. Tech Stack & Dependencies

### Core Dependencies
```txt
Flask>=3.0.0          # Web framework
Flask-SQLAlchemy>=3.1.0  # ORM
APScheduler>=3.10.0   # Background scheduler for health checks
Requests>=2.31.0      # HTTP client for health checks
gunicorn>=21.2.0      # Production WSGI server
python-dotenv>=1.0.0  # Environment variable management
```

### Development Dependencies
```txt
pytest>=7.4.0         # Testing framework
pytest-flask>=1.3.0  # Flask testing utilities
```

### Project Structure
```
healthdash/
├── healthdash/
│   ├── __init__.py           # Flask app factory
│   ├── config.py             # Configuration
│   ├── models.py             # SQLAlchemy models
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py         # REST API endpoints
│   │   └── validators.py    # Request validation
│   ├── services/
│   │   ├── __init__.py
│   │   ├── checker.py       # Health check logic
│   │   └── scheduler.py    # Background scheduler
│   ├── web/
│   │   ├── __init__.py
│   │   ├── routes.py        # Web UI routes
│   │   └── templates/       # HTML templates
│   │       ├── base.html
│   │       ├── index.html
│   │       ├── add_service.html
│   │       ├── edit_service.html
│   │       └── service_detail.html
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css   # Dark theme styles
│   │   └── js/
│   │       └── main.js     # Frontend interactivity
│   └── utils/
│       ├── __init__.py
│       └── helpers.py       # Utility functions
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_services.py
│   └── test_models.py
├── .env                     # Environment variables
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
├── run.py                   # Development entry point
├── gunicorn_config.py       # Production config
└── PLAN.md                  # This file
```

---

## 3. Database Schema

### Models

```python
# models.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Service(db.Model):
    """Service endpoint to monitor"""
    __tablename__ = 'services'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(2048), nullable=False)
    method = db.Column(db.String(10), default='GET')  # GET, POST, HEAD
    expected_status = db.Column(db.Integer, default=200)
    check_interval = db.Column(db.Integer, default=60)  # seconds
    timeout = db.Column(db.Integer, default=10)  # seconds
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    checks = db.relationship('HealthCheck', backref='service', lazy='dynamic',
                           cascade='all, delete-orphan', order_by='HealthCheck.timestamp.desc()')

    def __repr__(self):
        return f'<Service {self.name}>'

    @property
    def uptime_percentage(self):
        """Calculate uptime percentage from last 100 checks"""
        recent_checks = self.checks.limit(100).all()
        if not recent_checks:
            return None
        successful = sum(1 for c in recent_checks if c.is_up)
        return round((successful / len(recent_checks)) * 100, 2)

    @property
    def avg_response_time(self):
        """Average response time from last 100 checks (ms)"""
        recent_checks = self.checks.limit(100).all()
        times = [c.response_time for c in recent_checks if c.response_time is not None]
        return round(sum(times) / len(times), 2) if times else None


class HealthCheck(db.Model):
    """Individual health check result"""
    __tablename__ = 'health_checks'

    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_up = db.Column(db.Boolean, nullable=False)
    response_time = db.Column(db.Float, nullable=True)  # milliseconds
    status_code = db.Column(db.Integer, nullable=True)
    error_message = db.Column(db.String(500), nullable=True)

    def __repr__(self):
        return f'<HealthCheck {self.service_id} {self.timestamp}>'
```

---

## 4. REST API Design

### Base URL: `/api/v1`

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/services` | List all services |
| POST | `/services` | Create new service |
| GET | `/services/<id>` | Get service details |
| PUT | `/services/<id>` | Update service |
| DELETE | `/services/<id>` | Delete service |
| GET | `/services/<id>/checks` | Get check history |
| GET | `/services/<id>/stats` | Get uptime/stats |
| POST | `/services/<id>/check` | Trigger immediate check |
| GET | `/health` | API health check |

### Request/Response Formats

#### POST /services
**Request:**
```json
{
  "name": "My API",
  "url": "https://api.example.com/health",
  "method": "GET",
  "expected_status": 200,
  "check_interval": 60,
  "timeout": 10
}
```

**Response (201):**
```json
{
  "id": 1,
  "name": "My API",
  "url": "https://api.example.com/health",
  "method": "GET",
  "expected_status": 200,
  "check_interval": 60,
  "timeout": 10,
  "is_active": true,
  "created_at": "2026-04-18T10:00:00Z",
  "updated_at": "2026-04-18T10:00:00Z"
}
```

#### GET /services/1/stats
**Response (200):**
```json
{
  "service_id": 1,
  "service_name": "My API",
  "uptime_percentage": 99.5,
  "avg_response_time_ms": 145.2,
  "total_checks": 1500,
  "last_check": "2026-04-18T10:05:00Z",
  "last_status": "up"
}
```

#### GET /services/1/checks
**Query Params:** `?limit=100&offset=0`

**Response (200):**
```json
{
  "service_id": 1,
  "checks": [
    {
      "id": 1500,
      "timestamp": "2026-04-18T10:05:00Z",
      "is_up": true,
      "response_time": 145.2,
      "status_code": 200,
      "error_message": null
    }
  ],
  "total": 1500,
  "limit": 100,
  "offset": 0
}
```

### API Error Responses

**400 - Validation Error:**
```json
{
  "error": "validation_error",
  "message": "Invalid request data",
  "fields": {
    "url": "URL is required",
    "check_interval": "Must be between 10 and 3600"
  }
}
```

**404 - Not Found:**
```json
{
  "error": "not_found",
  "message": "Service not found"
}
```

**500 - Server Error:**
```json
{
  "error": "server_error",
  "message": "An internal error occurred"
}
```

---

## 5. Background Scheduler

### Implementation

```python
# services/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from healthdash.services.checker import perform_health_check

scheduler = BackgroundScheduler()

def schedule_service_checks(app):
    """Initialize scheduler with all active services"""
    with app.app_context():
        from healthdash.models import Service, db
        services = Service.query.filter_by(is_active=True).all()
        
        for service in services:
            add_job(service)
        
        if not scheduler.running:
            scheduler.start()

def add_job(service):
    """Add or update a scheduled job for a service"""
    job_id = f"check_{service.id}"
    
    # Remove existing job if present
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    
    # Add new job
    scheduler.add_job(
        func=perform_health_check,
        trigger=IntervalTrigger(seconds=service.check_interval),
        args=[service.id],
        id=job_id,
        replace_existing=True
    )

def remove_job(service_id):
    """Remove scheduled job for a service"""
    job_id = f"check_{service_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

def shutdown_scheduler():
    """Gracefully shutdown scheduler"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
```

---

## 6. Health Check Logic

```python
# services/checker.py

import requests
from healthdash.models import HealthCheck, Service, db

def perform_health_check(service_id):
    """Execute health check for a service"""
    service = Service.query.get(service_id)
    if not service or not service.is_active:
        return
    
    start_time = None
    error_message = None
    status_code = None
    is_up = False
    response_time = None
    
    try:
        start_time = datetime.utcnow()
        
        response = requests.request(
            method=service.method,
            url=service.url,
            timeout=service.timeout,
            allow_redirects=True
        )
        
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        status_code = response.status_code
        is_up = (status_code == service.expected_status)
        
    except requests.Timeout:
        error_message = "Request timeout"
        response_time = service.timeout * 1000
    except requests.ConnectionError as e:
        error_message = f"Connection error: {str(e)[:200]}"
    except requests.RequestException as e:
        error_message = f"Request error: {str(e)[:200]}"
    except Exception as e:
        error_message = f"Unexpected error: {str(e)[:200]}"
    
    # Save check result
    check = HealthCheck(
        service_id=service.id,
        is_up=is_up,
        response_time=response_time,
        status_code=status_code,
        error_message=error_message
    )
    
    db.session.add(check)
    db.session.commit()
    
    return check
```

---

## 7. Web UI Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Dashboard with all services |
| GET | `/add` | Add service form |
| POST | `/add` | Create service |
| GET | `/service/<id>` | Service detail with history |
| GET | `/service/<id>/edit` | Edit service form |
| POST | `/service/<id>/edit` | Update service |
| POST | `/service/<id>/delete` | Delete service (redirect) |
| POST | `/service/<id>/toggle` | Toggle active status |
| POST | `/service/<id>/check` | Trigger immediate check |

---

## 8. Error Handling

### Global Error Handlers

```python
# api/routes.py or __init__.py

from flask import jsonify

@app.errorhandler(400)
def bad_request(e):
    return jsonify({
        "error": "bad_request",
        "message": str(e.description)
    }), 400

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "error": "not_found",
        "message": "Resource not found"
    }), 404

@app.errorhandler(500)
def server_error(e):
    db.session.rollback()
    return jsonify({
        "error": "server_error",
        "message": "An internal error occurred"
    }), 500

# CSRF protection for web forms
from flask_wtf.csrf import CSRFError

@app.errorhandler(CSRFError)
def csrf_error(e):
    return jsonify({
        "error": "csrf_error",
        "message": "CSRF token validation failed"
    }), 400
```

### API Validation Errors

```python
# api/validators.py

from flask import request, jsonify
from functools import wraps

def validate_service_data(required_fields=None):
    """Validate incoming service data"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json()
            
            if not data:
                return jsonify({
                    "error": "validation_error",
                    "message": "Request body required"
                }), 400
            
            if required_fields:
                missing = [f for f in required_fields if f not in data]
                if missing:
                    return jsonify({
                        "error": "validation_error",
                        "message": f"Missing required fields: {', '.join(missing)}"
                    }), 400
            
            # URL validation
            if 'url' in data:
                if not data['url'].startswith(('http://', 'https://')):
                    return jsonify({
                        "error": "validation_error",
                        "message": "URL must start with http:// or https://"
                    }), 400
            
            # Interval validation
            if 'check_interval' in data:
                interval = data['check_interval']
                if not isinstance(interval, int) or interval < 10 or interval > 3600:
                    return jsonify({
                        "error": "validation_error",
                        "message": "check_interval must be between 10 and 3600 seconds"
                    }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

---

## 9. UI/UX Design

### Color Palette (Dark Theme)
```css
:root {
    --bg-primary: #0d1117;
    --bg-secondary: #161b22;
    --bg-tertiary: #21262d;
    --border-color: #30363d;
    --text-primary: #e6edf3;
    --text-secondary: #8b949e;
    --text-muted: #6e7681;
    --accent-green: #3fb950;
    --accent-red: #f85149;
    --accent-yellow: #d29922;
    --accent-blue: #58a6ff;
    --accent-purple: #a371f7;
}
```

### Status Indicators
- **UP:** Green badge with checkmark icon
- **DOWN:** Red badge with X icon
- **DEGRADED:** Yellow badge (high response time > 1000ms)
- **PENDING:** Gray spinner during check

### Layout
- **Header:** Logo + "Add Service" button
- **Main Grid:** Service cards in responsive grid
- **Service Card:** Name, URL, status badge, uptime %, avg response time
- **Detail Page:** Full history graph, recent checks table, stats

---

## 10. Implementation Order

### Phase 1: Foundation
1. Create project structure and dependencies
2. Set up Flask app factory with config
3. Create database models
4. Set up SQLite database

### Phase 2: Core API
5. Implement service CRUD API endpoints
6. Add request validation
7. Implement error handlers
8. Write API tests

### Phase 3: Health Checking
9. Implement health check logic
10. Set up APScheduler
11. Create scheduler service
12. Test background checks

### Phase 4: Web UI
13. Create HTML templates
14. Implement CSS dark theme
15. Add JavaScript interactivity
16. Create web routes

### Phase 5: Polish
17. Add service statistics (uptime %, avg response)
18. Implement status history pagination
19. Add immediate check trigger
20. Production deployment config

---

## 11. Configuration

```python
# config.py

import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///healthdash.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Scheduler
    SCHEDULER_API_ENABLED = False
    
    # Health check defaults
    DEFAULT_TIMEOUT = 10
    DEFAULT_INTERVAL = 60
    MAX_HISTORY_PER_SERVICE = 1000  # Keep last 1000 checks

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
```

---

## 12. Environment Variables

```bash
# .env

FLASK_APP=healthdash
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///healthdash.db
```

---

## 13. Acceptance Criteria

- [ ] Can add a new service via UI and API
- [ ] Can edit existing service
- [ ] Can delete service
- [ ] Services are checked at configured intervals
- [ ] Response time is recorded for each check
- [ ] Uptime percentage calculates correctly
- [ ] Status history displays with pagination
- [ ] Dark theme renders correctly
- [ ] API returns proper error responses
- [ ] Scheduler runs on application startup
- [ ] Data persists in SQLite

---

## 14. Future Enhancements (Out of Scope)

- User authentication / multi-tenant
- Email/Slack/PagerDuty notifications
- Multiple check locations
- SSL certificate expiration monitoring
- Custom headers for health checks
- Prometheus metrics export
- Docker containerization
