# Habitbeat - Implementation Plan

## 1. Project Overview

**Habitbeat** is a self-hosted habit tracking web application with the following features:

- **Streak Analytics**: Track current/longest streaks, completion rates
- **Daily Check-ins**: One-click habit completion
- **Progress Charts**: Weekly/monthly visualization
- **Habit Categories**: Organize habits by category
- **Reminders API**: External reminder integration
- **RESTful API**: Full programmatic access

**Tech Stack**: Flask + SQLite

---

## 2. File Structure

```
habitbeat/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Configuration
│   ├── models.py           # SQLAlchemy models
│   ├── api/
│   │   ├── __init__.py
│   │   ├── habits.py       # Habit CRUD endpoints
│   │   ├── checkins.py     # Check-in endpoints
│   │   ├── categories.py   # Category endpoints
│   │   ├── analytics.py    # Streak/progress endpoints
│   │   └── reminders.py    # Reminders API
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── web.py          # HTML routes
│   │   └── auth.py         # Auth routes
│   ├── services/
│   │   ├── __init__.py
│   │   ├── streak.py       # Streak calculation logic
│   │   ├── notifications.py # Reminder scheduling
│   │   └── analytics.py    # Chart data aggregation
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── errors.py        # Custom exceptions
│   │   └── validators.py   # Input validation
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── habits.html
│       ├── habit_detail.html
│       ├── analytics.html
│       └── settings.html
├── static/
│   ├── css/
│   │   ├── style.css
│   │   └── charts.css
│   └── js/
│       ├── main.js
│       ├── charts.js
│       └── api-client.js
├── tests/
│   ├── __init__.py
│   ├── test_habits.py
│   ├── test_analytics.py
│   └── test_api.py
├── migrations/
│   └── (Alembic/Flask-Migrate files)
├── .env                    # Environment variables
├── .env.example
├── requirements.txt
├── requirements-dev.txt
├── config.yaml            # Application configuration
├── app.db                 # SQLite database (auto-generated)
├── run.py                 # Entry point
└── PLAN.md               # This file
```

---

## 3. Dependencies

### Core Dependencies (requirements.txt)

```txt
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.5
Flask-CORS==4.0.0
SQLAlchemy==2.0.23
AlchemyUtils==0.1.5
python-dotenv==1.0.0
marshmallow==3.20.1
marshmallow-sqlalchemy==0.29.0
APScheduler==3.10.4
gunicorn==21.2.0
```

### Development Dependencies (requirements-dev.txt)

```txt
-r requirements.txt
pytest==7.4.3
pytest-flask==1.3.0
pytest-cov==4.1.0
flake8==6.1.0
black==23.12.1
isort==5.12.0
```

### Optional Production Dependencies

```txt
# For enhanced scheduler
pytz==2023.3
bleach==6.1.0
email-validator==2.1.0
```

---

## 4. Database Schema

### Entity Relationship

```
┌─────────────────┐       ┌─────────────────┐
│    users        │       │   categories     │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │◄──┐   │ id (PK)         │
│ email           │   │   │ name           │
│ password_hash  │   │   │ color          │
│ created_at     │   │   │ icon           │
│ updated_at     │   └───│ user_id (FK)   │
└─────────────────┘       │ created_at     │
                          └─────────────────┘
                                 │
                                 │ 1:N
                                 ▼
┌─────────────────┐       ┌─────────────────┐
│    habits        │       │  checkins        │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │◄──────│ id (PK)         │
│ name           │       │ habit_id (FK)   │
│ description    │       │ user_id (FK)    │
│ frequency      │       │ completed_at    │
│ target_count   │       │ note            │
│ category_id(FK) │       │ created_at      │
│ user_id (FK)   │       └─────────────────┘
│ is_active      │
│ reminder_time  │
│ created_at     │
│ updated_at     │
└─────────────────┘
                │
                │ 1:N
                ▼
        ┌─────────────────┐
        │   reminders     │
        ├─────────────────┤
        │ id (PK)         │
        │ habit_id (FK)   │
        │ user_id (FK)    │
        │ scheduled_at    │
        │ sent_at         │
        │ status          │
        │ external_url   │
        └─────────────────┘
```

### Schema Details

#### users

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique user ID |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User email |
| password_hash | VARCHAR(255) | NOT NULL | Bcrypt hash |
| created_at | DATETIME | NOT NULL, DEFAULT=now | Creation timestamp |
| updated_at | DATETIME | NOT NULL, DEFAULT=now | Last update |

#### categories

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique category ID |
| user_id | INTEGER | FOREIGN KEY → users.id | Owner |
| name | VARCHAR(100) | NOT NULL | Category name |
| color | VARCHAR(7) | DEFAULT='#6366f1' | Hex color |
| icon | VARCHAR(50) | DEFAULT='star' | Icon name |
| created_at | DATETIME | NOT NULL, DEFAULT=now | Creation timestamp |

#### habits

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique habit ID |
| user_id | INTEGER | FOREIGN KEY → users.id | Owner |
| category_id | INTEGER | FOREIGN KEY → categories.id, NULLABLE | Category |
| name | VARCHAR(255) | NOT NULL | Habit name |
| description | TEXT | NULLABLE | Description |
| frequency | VARCHAR(20) | NOT NULL, DEFAULT='daily' | daily/weekly/monthly |
| target_count | INTEGER | DEFAULT=1 | Target per period |
| is_active | BOOLEAN | DEFAULT=TRUE | Soft delete |
| reminder_time | TIME | NULLABLE | Daily reminder time |
| created_at | DATETIME | NOT NULL, DEFAULT=now | Creation timestamp |
| updated_at | DATETIME | NOT NULL, DEFAULT=now | Last update |

#### checkins

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique check-in ID |
| habit_id | INTEGER | FOREIGN KEY → habits.id | Related habit |
| user_id | INTEGER | FOREIGN KEY → users.id | Owner |
| completed_at | DATETIME | NOT NULL | Completion timestamp |
| note | TEXT | NULLABLE | Optional note |
| created_at | DATETIME | NOT NULL, DEFAULT=now | Creation timestamp |

**UNIQUE CONSTRAINT**: (habit_id, completed_at date) - One check-in per habit per day

#### reminders

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique reminder ID |
| habit_id | INTEGER | FOREIGN KEY → habits.id | Related habit |
| user_id | INTEGER | FOREIGN KEY → users.id | Owner |
| scheduled_at | DATETIME | NOT NULL | When to send |
| sent_at | DATETIME | NULLABLE | When actually sent |
| status | VARCHAR(20) | DEFAULT='pending' | pending/sent/failed |
| external_url | VARCHAR(500) | NULLABLE | Webhook URL |
| created_at | DATETIME | NOT NULL, DEFAULT=now | Creation timestamp |

---

## 5. API Design

### 5.1 Authentication

All API endpoints (except registration/login) require authentication via Bearer token.

```
Authorization: Bearer <jwt_token>
```

**Token Claims**:
- `sub`: user_id
- `email`: user email
- `exp`: expiration timestamp (24h default)

### 5.2 API Endpoints

#### Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | /api/auth/register | Register new user | No |
| POST | /api/auth/login | Login, get token | No |
| POST | /api/auth/refresh | Refresh token | Yes |
| DELETE | /api/auth/logout | Invalidate token | Yes |

#### Habits

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | /api/habits | List all habits | Yes |
| POST | /api/habits | Create habit | Yes |
| GET | /api/habits/{id} | Get habit detail | Yes |
| PUT | /api/habits/{id} | Update habit | Yes |
| DELETE | /api/habits/{id} | Soft delete habit | Yes |

#### Categories

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | /api/categories | List categories | Yes |
| POST | /api/categories | Create category | Yes |
| PUT | /api/categories/{id} | Update category | Yes |
| DELETE | /api/categories/{id} | Delete category | Yes |

#### Check-ins

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | /api/habits/{id}/checkins | List check-ins | Yes |
| POST | /api/habits/{id}/checkins | Create check-in | Yes |
| DELETE | /api/checkins/{id} | Delete check-in | Yes |

#### Analytics

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | /api/habits/{id}/streak | Get streak info | Yes |
| GET | /api/habits/{id}/analytics | Get progress data | Yes |
| GET | /api/analytics/summary | Dashboard data | Yes |

#### Reminders

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | /api/reminders | List reminders | Yes |
| POST | /api/reminders | Create reminder | Yes |
| PUT | /api/reminders/{id} | Update reminder | Yes |
| DELETE | /api/reminders/{id} | Delete reminder | Yes |

---

## 6. Request/Response Formats

### 6.1 Authentication

#### POST /api/auth/register

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response (201):**
```json
{
  "message": "Registration successful",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "created_at": "2024-01-15T10:30:00Z"
  },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### POST /api/auth/login

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer",
  "expires_in": 86400
}
```

### 6.2 Habits

#### GET /api/habits

**Response (200):**
```json
{
  "habits": [
    {
      "id": 1,
      "name": "Morning Exercise",
      "description": "30 min workout",
      "category": {
        "id": 1,
        "name": "Health",
        "color": "#22c55e"
      },
      "frequency": "daily",
      "target_count": 1,
      "current_streak": 5,
      "longest_streak": 12,
      "completion_rate": 0.85,
      "is_active": true,
      "reminder_time": "07:00:00",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 10,
  "active": 8
}
```

#### POST /api/habits

**Request:**
```json
{
  "name": "Morning Exercise",
  "description": "30 min workout",
  "category_id": 1,
  "frequency": "daily",
  "target_count": 1,
  "reminder_time": "07:00:00"
}
```

**Response (201):**
```json
{
  "id": 1,
  "name": "Morning Exercise",
  "message": "Habit created successfully"
}
```

### 6.3 Check-ins

#### POST /api/habits/{id}/checkins

**Request:**
```json
{
  "completed_at": "2024-01-15T08:00:00Z",
  "note": "Felt great!"
}
```

**Response (201):**
```json
{
  "id": 1,
  "habit_id": 1,
  "completed_at": "2024-01-15T08:00:00Z",
  "message": "Check-in recorded"
}
```

### 6.4 Analytics

#### GET /api/habits/{id}/streak

**Response (200):**
```json
{
  "current_streak": 5,
  "longest_streak": 12,
  "streak_start_date": "2024-01-10",
  "streak_end_date": "2024-01-15",
  "last_completed_date": "2024-01-15",
  "completion_rate_30d": 0.87,
  "completion_rate_90d": 0.75,
  "total_completions": 45
}
```

#### GET /api/habits/{id}/analytics

**Query Parameters:**
- `period`: weekly | monthly (default: weekly)
- `start_date`: ISO date (default: 30 days ago)
- `end_date`: ISO date (default: today)

**Response (200):**
```json
{
  "habit_id": 1,
  "period": "weekly",
  "data": [
    {"date": "2024-01-08", "completed": 1, "target": 1},
    {"date": "2024-01-09", "completed": 1, "target": 1},
    {"date": "2024-01-10", "completed": 0, "target": 1},
    {"date": "2024-01-11", "completed": 1, "target": 1},
    {"date": "2024-01-12", "completed": 1, "target": 1},
    {"date": "2024-01-13", "completed": 1, "target": 1},
    {"date": "2024-01-14", "completed": 1, "target": 1}
  ],
  "summary": {
    "total_completed": 6,
    "total_target": 7,
    "completion_rate": 0.86
  }
}
```

#### GET /api/analytics/summary

**Response (200):**
```json
{
  "total_habits": 10,
  "active_habits": 8,
  "overall_completion_rate": 0.72,
  "best_streak": 15,
  "total_checkins_today": 5,
  "habits_due_today": 8,
  "by_category": [
    {
      "category": "Health",
      "habits": 3,
      "completion_rate": 0.85
    }
  ]
}
```

### 6.5 Reminders

#### GET /api/reminders

**Response (200):**
```json
{
  "reminders": [
    {
      "id": 1,
      "habit": {
        "id": 1,
        "name": "Morning Exercise"
      },
      "scheduled_at": "2024-01-15T07:00:00Z",
      "sent_at": null,
      "status": "pending",
      "external_url": "https://webhook.site/abc123"
    }
  ]
}
```

---

## 7. Configuration

### 7.1 Environment Variables (.env)

```bash
# Flask
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here-change-in-production

# Database
DATABASE_URL=sqlite:///app.db
SQLALCHEMY_DATABASE_URI=sqlite:///app.db

# JWT
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_ACCESS_TOKEN_EXPIRES=86400

# Reminders API
REMINDER_BACKEND=webhook
DEFAULT_WEBHOOK_URL=
REMINDER_CHECK_INTERVAL=300

# Server
HOST=0.0.0.0
PORT=5000
```

### 7.2 config.yaml

```yaml
app:
  name: Habitbeat
  version: 1.0.0
  debug: true

database:
  uri: "sqlite:///app.db"
  echo: false
  pool_size: 5
  pool_recycle: 3600

auth:
  jwt_algorithm: HS256
  jwt_expiration: 86400
  password_min_length: 8

scheduler:
  enabled: true
  check_interval: 300
  max_retries: 3

api:
  rate_limit: 100
  rate_limit_period: 3600

reminders:
  enabled: true
  default_time: "09:00:00"
  webhook_timeout: 10

charts:
  default_period_days: 30
  max_period_days: 365
```

---

## 8. Error Handling

### 8.1 HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Success |
| 201 | Created - Resource created |
| 204 | No Content - Success, no response body |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid/missing token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - Duplicate resource |
| 422 | Unprocessable Entity - Validation failed |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

### 8.2 Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": [
      {"field": "email", "message": "Invalid email format"}
    ]
  }
}
```

### 8.3 Custom Error Codes

| Code | HTTP Status | Description |
|------|------------|-------------|
| VALIDATION_ERROR | 400 | Input validation failed |
| AUTHENTICATION_REQUIRED | 401 | No/invalid token |
| PERMISSION_DENIED | 403 | Not resource owner |
| RESOURCE_NOT_FOUND | 404 | Resource doesn't exist |
| DUPLICATE_RESOURCE | 409 | Resource already exists |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests |

### 8.4 Implementation

```python
# utils/errors.py

class HabitbeatError(Exception):
    status_code = 500
    error_code = "INTERNAL_ERROR"

    def __init__(self, message=None, details=None):
        super().__init__(message)
        self.message = message or self.__class__.__name__
        self.details = details or []

class ValidationError(HabitbeatError):
    status_code = 400
    error_code = "VALIDATION_ERROR"

class NotFoundError(HabitbeatError):
    status_code = 404
    error_code = "RESOURCE_NOT_FOUND"

class AuthenticationError(HabitbeatError):
    status_code = 401
    error_code = "AUTHENTICATION_REQUIRED"

class PermissionError(HabitbeatError):
    status_code = 403
    error_code = "PERMISSION_DENIED"

class DuplicateError(HabitbeatError):
    status_code = 409
    error_code = "DUPLICATE_RESOURCE"

# API error handler
@app.errorhandler(HabitbeatError)
def handle_habitbeat_error(error):
    return jsonify({
        "error": {
            "code": error.error_code,
            "message": error.message,
            "details": error.details
        }
    }), error.status_code
```

---

## 9. Edge Cases

### 9.1 Check-in Edge Cases

| Scenario | Expected Behavior |
|----------|-----------------|
| Duplicate check-in same day | Return existing, update note if provided |
| Check-in for deleted habit | Return 404 |
| Check-in for inactive habit | Allow (historical tracking) |
| Future date check-in | Allow for pre-tracking |
| Check-in date before habit created | Return validation error |
| Bulk check-in (multiple same day) | Keep latest, aggregate notes |

### 9.2 Streak Calculation Edge Cases

| Scenario | Expected Behavior |
|----------|-----------------|
| No check-ins yet | Streak = 0, completion_rate = 0 |
| Missed one day, completed rest | current_streak resets to 0 |
| Multiple check-ins per day | Count as 1 for streak |
| Habit frequency changes | Recalculate from change date |
| Timezone handling | Use UTC, store timezone separately |
| Leap year | Handle Feb 29 correctly |

### 9.3 Category Edge Cases

| Scenario | Expected Behavior |
|----------|-----------------|
| Delete category with habits | Set habit.category_id to NULL |
| Delete last category | Allow (habits become uncategorized) |
| Category name duplicate | Return validation error |
| Category with many habits | Return count in response |

### 9.4 Reminder Edge Cases

| Scenario | Expected Behavior |
|----------|-----------------|
| Webhook timeout | Mark as failed, retry up to 3 times |
| Invalid webhook URL | Return validation error |
| Past scheduled time | Mark as missed |
| Habit deleted | Cancel pending reminders |
| Network failure | Retry with exponential backoff |

### 9.5 Data Integrity Edge Cases

| Scenario | Expected Behavior |
|----------|-----------------|
| Database locked | Retry with timeout |
| Concurrent check-ins | Use transaction/lock |
| Large data export | Paginate responses |
| Orphaned check-ins | Clean with periodic job |

---

## 10. Implementation Phases

### Phase 1: Foundation (Week 1)

- [ ] Project setup (Flask, SQLAlchemy, configuration)
- [ ] Database models and migrations
- [ ] User authentication (register, login, JWT)
- [ ] Basic error handling
- [ ] SQLite configuration

### Phase 2: Core Features (Week 2)

- [ ] Habit CRUD operations
- [ ] Category management
- [ ] Daily check-ins
- [ ] Streak calculation service

### Phase 3: Analytics (Week 3)

- [ ] Progress charts data endpoints
- [ ] Analytics aggregation
- [ ] Dashboard summary API
- [ ] Date range filtering

### Phase 4: Reminders (Week 4)

- [ ] Reminder model and API
- [ ] APScheduler integration
- [ ] Webhook delivery
- [ ] Retry logic

### Phase 5: Frontend (Week 5)

- [ ] HTML templates
- [ ] CSS styling
- [ ] JavaScript interactions
- [ ] Chart.js integration
- [ ] API client

### Phase 6: Testing & Polish (Week 6)

- [ ] Unit tests
- [ ] API integration tests
- [ ] Error case handling
- [ ] Documentation
- [ ] Performance optimization

---

## 11. Acceptance Criteria

### Authentication
- [ ] User can register with email/password
- [ ] User can login and receive JWT token
- [ ] Protected endpoints reject invalid tokens

### Habits
- [ ] User can create, read, update, delete habits
- [ ] Habits support daily/weekly/monthly frequencies
- [ ] Inactive habits are hidden from list

### Check-ins
- [ ] User can record daily check-in
- [ ] Duplicate check-ins handled gracefully
- [ ] Check-ins support optional notes

### Analytics
- [ ] Streak calculation is accurate
- [ ] Weekly/monthly charts return correct data
- [ ] Dashboard shows correct summary

### Categories
- [ ] Categories can be created/managed
- [ ] Habits can be assigned to categories
- [ ] Deleting category retains habits

### Reminders
- [ ] Reminders can be scheduled
- [ ] Webhook delivery works
- [ ] Failed reminders are retried

### API Documentation
- [ ] All endpoints documented
- [ ] Request/response examples provided
- [ ] Error codes documented

---

## 12. Future Enhancements (Out of Scope)

- Social features (sharing habits)
- Gamification (badges, points)
- Multi-user habits (accountability partners)
- Mobile push notifications
- Email reminders
- Data export (CSV, JSON)
- Recurring check-in patterns
- Habit templates library
- Dark mode UI
- PWA support