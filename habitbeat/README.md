# Habitbeat

A self-hosted habit tracking web application with streak analytics, daily check-ins, progress charts, and RESTful API.

## Features

- Track habits with daily/weekly/monthly frequency
- One-click daily check-ins
- Streak analytics (current/longest streaks, completion rates)
- Progress charts (weekly/monthly visualization)
- Habit categories with custom colors
- Reminders API with webhook integration
- Full RESTful API for programmatic access

## Tech Stack

- Flask 3.0
- SQLAlchemy 2.0
- SQLite (default)
- JWT Authentication

## Quick Start

### 1. Clone and Install

```bash
cd habitbeat
pip install -r requirements.txt
```

### 2. Configure

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
SECRET_KEY=your-secure-random-key
JWT_SECRET_KEY=your-jwt-secret-key
```

### 3. Run

Development:

```bash
python run.py
```

Production with Gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

The app runs at `http://localhost:5000`.

## API Usage

### Register

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securePassword123"}'
```

Response:
```json
{
  "message": "Registration successful",
  "user": {"id": 1, "email": "user@example.com", "created_at": "..."},
  "access_token": "eyJ0..."
}
```

### Login

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securePassword123"}'
```

### Create Habit

```bash
curl -X POST http://localhost:5000/api/habits \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Morning Exercise", "frequency": "daily"}'
```

### Check In

```bash
curl -X POST http://localhost:5000/api/habits/1/checkins \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/register | Register new user |
| POST | /api/auth/login | Get access token |
| GET | /api/habits | List habits |
| POST | /api/habits | Create habit |
| GET | /api/habits/{id} | Get habit detail |
| PUT | /api/habits/{id} | Update habit |
| DELETE | /api/habits/{id} | Delete habit |
| POST | /api/habits/{id}/checkins | Record check-in |
| GET | /api/habits/{id}/streak | Get streak info |
| GET | /api/habits/{id}/analytics | Get progress data |
| GET | /api/analytics/summary | Dashboard summary |
| GET | /api/categories | List categories |
| POST | /api/categories | Create category |

## Development

### Run Tests

```bash
pip install -r requirements-dev.txt
pytest
```

### Code Style

```bash
black app/ tests/
isort app/ tests/
flake8 app/ tests/
```

## Configuration

Environment variables in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| FLASK_ENV | development | Environment |
| SECRET_KEY | - | Flask secret key |
| JWT_SECRET_KEY | - | JWT signing key |
| JWT_ACCESS_TOKEN_EXPIRES | 86400 | Token expiry (seconds) |
| DATABASE_URL | sqlite:///app.db | Database URI |
| HOST | 0.0.0.0 | Server host |
| PORT | 5000 | Server port |

## License

MIT