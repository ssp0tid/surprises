# Self-Hosted Status Page Generator - Implementation Plan

## Project Overview

**Project Name:** StatusPage
**Type:** Web Application (Self-Hosted)
**Tech Stack:** Flask, SQLite, Chart.js
**Core Functionality:** Monitor services/endpoints, display uptime history, log incidents, generate shareable public status pages

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Flask Application                        │
├─────────────────────────────────────────────────────────────┤
│  Admin Panel          │    Public Status Page               │
│  (/admin/*)           │    (/status/*)                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Routes     │  │   Models     │  │  Scheduler   │      │
│  │  (Views)     │  │  (SQLAlchemy)│  │  (APScheduler)│     │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Services    │  │   Forms      │  │   Helpers    │      │
│  │ (HTTP Check) │  │  (WTForms)   │  │  (Utils)     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                      SQLite Database                         │
│   - organizations    - components     - incidents          │
│   - component_groups - incident_timeline                   │
│   - checks           - check_results                        │
│   - settings         - users                                 │
└─────────────────────────────────────────────────────────────┘
```

### Database Schema

```sql
-- Organizations (multi-tenant support)
organizations (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    custom_branding JSON,
    created_at DATETIME
)

-- Users (admin access)
users (
    id INTEGER PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'admin',
    created_at DATETIME
)

-- Component Groups
component_groups (
    id INTEGER PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id),
    name TEXT NOT NULL,
    description TEXT,
    display_order INTEGER DEFAULT 0,
    created_at DATETIME
)

-- Components (Services/Endpoints)
components (
    id INTEGER PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id),
    group_id INTEGER REFERENCES component_groups(id),
    name TEXT NOT NULL,
    description TEXT,
    type TEXT DEFAULT 'http', -- http, tcp, ping
    check_url TEXT,
    check_method TEXT DEFAULT 'GET',
    check_timeout INTEGER DEFAULT 30,
    check_interval INTEGER DEFAULT 60, -- seconds
    check_expected_status INTEGER DEFAULT 200,
    is_enabled BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,
    created_at DATETIME
)

-- Check Results
check_results (
    id INTEGER PRIMARY KEY,
    component_id INTEGER REFERENCES components(id),
    status TEXT, -- operational, degraded, down
    response_time_ms INTEGER,
    status_code INTEGER,
    error_message TEXT,
    checked_at DATETIME
)

-- Incidents
incidents (
    id INTEGER PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id),
    title TEXT NOT NULL,
    description TEXT,
    severity TEXT, -- critical, major, minor
    status TEXT, -- investigating, identified, monitoring, resolved
    created_at DATETIME,
    resolved_at DATETIME
)

-- Incident Timeline
incident_timeline (
    id INTEGER PRIMARY KEY,
    incident_id INTEGER REFERENCES incidents(id),
    status TEXT,
    message TEXT,
    created_at DATETIME
)

-- Settings
settings (
    id INTEGER PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id),
    key TEXT NOT NULL,
    value TEXT,
    UNIQUE(organization_id, key)
)
```

---

## Feature Implementation Plan

### Phase 1: Core Infrastructure

#### 1.1 Project Setup
- Initialize Flask project structure
- Configure SQLite database with SQLAlchemy
- Set up Flask-Login for authentication
- Configure Flask-WTF for forms
- Set up logging

**Files to create:**
- `app/__init__.py` - Application factory
- `app/config.py` - Configuration
- `app/models.py` - Database models
- `requirements.txt` - Dependencies

#### 1.2 Authentication System
- User registration (first user = owner)
- Login/logout
- Password hashing with bcrypt
- Session management

**Files to create:**
- `app/auth.py` - Authentication routes
- `app/forms.py` - WTForms definitions

---

### Phase 2: Component Management

#### 2.1 Component CRUD
- Create components with type (HTTP, TCP, Ping)
- Configure check parameters (URL, interval, timeout, expected status)
- Edit/delete components
- Toggle component monitoring on/off
- Organize into groups

**Routes:**
- `GET/POST /admin/components` - List components
- `GET/POST /admin/components/new` - Create component
- `GET/POST /admin/components/<id>/edit` - Edit component
- `POST /admin/components/<id>/delete` - Delete component

#### 2.2 Component Groups
- Create/edit/delete groups
- Drag-drop reordering
- Assign components to groups

**Routes:**
- `GET/POST /admin/groups` - List groups
- `GET/POST /admin/groups/new` - Create group
- `GET/POST /admin/groups/<id>/edit` - Edit group

---

### Phase 3: Monitoring Engine

#### 3.1 Health Check Service
- HTTP endpoint checking with configurable method/headers
- TCP port checking
- ICMP ping checking (optional, requires root)
- Timeout handling
- SSL certificate expiry checking

**Files to create:**
- `app/services/health_checker.py`

#### 3.2 Scheduler Integration
- APScheduler for periodic checks
- Per-component interval configuration
- Check result storage
- Status determination logic:
  - `operational`: 2xx status, response time < threshold
  - `degraded`: 2xx but slow response OR 3xx redirect
  - `down`: Connection error, timeout, 4xx/5xx

#### 3.3 Uptime Calculation
- Calculate uptime percentage for:
  - Last 24 hours
  - Last 7 days
  - Last 30 days
  - Last 90 days
- Store aggregated data for performance

---

### Phase 4: Incident Management

#### 4.1 Incident Creation
- Create incidents manually or auto-triggered
- Severity levels: critical, major, minor
- Status workflow: investigating → identified → monitoring → resolved
- Assign affected components

#### 4.2 Incident Timeline
- Add timeline updates
- Timestamp each update
- Public visibility on status page

#### 4.3 Auto-Incident Creation
- Automatically create incidents when component goes down
- Auto-resolve when component recovers (optional)

---

### Phase 5: Public Status Page

#### 5.1 Status Page Design
- Clean, minimal design
- Current status banner (operational/degraded/down)
- Component status list with uptime percentages
- Uptime charts (Chart.js)
- Incident history
- Incident timeline during active incidents

**Routes:**
- `GET /status/<org_slug>` - Public status page
- `GET /status/<org_slug>/history` - Historical view

#### 5.2 Branding Customization
- Logo upload
- Primary color customization
- Custom CSS
- Custom domain support (optional)

**Routes:**
- `GET/POST /admin/settings` - Branding settings

#### 5.3 Uptime Charts
- 24-hour sparkline per component
- 7-day trend chart
- 30-day historical chart
- Component group aggregation

---

### Phase 6: API & Extras

#### 6.1 REST API
- Read-only API for status checks
- JSON output
- CORS support

**Routes:**
- `GET /api/status/<org_slug>` - JSON status
- `GET /api/components` - Component list

#### 6.2 Status Badges
- SVG badges for markdown embedding
- Various styles (flat, plastic)
- Status: operational, degraded, down

---

## File Structure

```
statuspage/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   ├── forms.py
│   ├── auth.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── status.py
│   │   └── api.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── health_checker.py
│   │   └── scheduler.py
│   ├── templates/
│   │   ├── admin/
│   │   │   ├── base.html
│   │   │   ├── dashboard.html
│   │   │   ├── components.html
│   │   │   ├── component_form.html
│   │   │   ├── groups.html
│   │   │   ├── group_form.html
│   │   │   ├── incidents.html
│   │   │   ├── incident_form.html
│   │   │   └── settings.html
│   │   ├── status/
│   │   │   ├── page.html
│   │   │   └── history.html
│   │   ├── auth/
│   │   │   ├── login.html
│   │   │   └── register.html
│   │   └── base.html
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       ├── charts.js
│   │       └── main.js
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── migrations/
├── instance/
│   └── statuspage.db
├── requirements.txt
├── run.py
└── PLAN.md
```

---

## Implementation Order

### Week 1: Foundation
1. Project setup & database models
2. Authentication system
3. Admin layout & navigation

### Week 2: Component Management
4. Component CRUD operations
5. Component groups
6. Basic settings

### Week 3: Monitoring
7. Health check service
8. Scheduler integration
9. Uptime calculation

### Week 4: Public Interface
10. Public status page
11. Uptime charts (Chart.js)
12. Incident management
13. Timeline updates

### Week 5: Polish
14. Custom branding
15. Status badges
16. API endpoints
17. Testing & bug fixes

---

## Dependencies

```python
Flask>=2.3
Flask-SQLAlchemy>=3.0
Flask-Login>=0.6
Flask-WTF>=1.1
SQLAlchemy>=2.0
APScheduler>=3.10
requests>=2.31
Werkzeug>=2.3
python-dotenv>=1.0
gunicorn>=21.0  # Production
```

---

## Security Considerations

- Passwords hashed with bcrypt
- CSRF protection via Flask-WTF
- SQL injection prevention via SQLAlchemy ORM
- XSS prevention via Jinja2 autoescaping
- Rate limiting on login (optional)
- HTTPS required for production

---

## Performance Optimizations

- Database indexes on frequently queried columns
- Cached uptime calculations (refresh hourly)
- Lazy loading for historical data
- Pagination for incident lists
- Background job for checks (not blocking requests)

---

## Deployment

### Development
```bash
pip install -r requirements.txt
python run.py
```

### Production
```bash
pip install -r requirements.txt
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

### Docker (Optional)
- Alpine-based Python image
- SQLite mounted volume
- Nginx reverse proxy

---

## Acceptance Criteria

- [ ] Users can register/login
- [ ] Admins can create/edit/delete components
- [ ] Components can be organized into groups
- [ ] Health checks run at configured intervals
- [ ] Uptime percentages calculate correctly
- [ ] Incidents can be created and updated
- [ ] Public status page displays current status
- [ ] Uptime charts render with Chart.js
- [ ] Custom branding can be applied
- [ ] Status page is responsive on mobile

---

## Future Enhancements (Out of Scope)

- Multi-user collaboration
- Email/Slack notifications
- HTTP webhook alerts
- Prometheus metrics export
- Custom check types (DNS, SSL)
- Two-factor authentication
- Audit logging