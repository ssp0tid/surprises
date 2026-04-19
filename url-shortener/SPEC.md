# URL Shortener - Single File Flask Application

## Overview
Self-hosted URL shortener with click analytics. Single `app.py` file using Flask. Data stored as JSON files in filesystem. No database required.

## Features

### Core Functionality
- [x] Create short links from full URLs
- [x] Automatic short code generation (6-char alphanumeric)
- [x] Redirect short URLs to original destinations
- [x] Custom short codes (optional)

### Analytics Tracking
- [x] Total click count per short link
- [x] Per-click data storage:
  - Timestamp (ISO 8601)
  - Referrer URL (or "direct" if none)
  - User Agent string
  - IP address (for geo approximation)

### Storage
- [x] JSON file per short link: `data/links/{short_code}.json`
- [x] Index file for quick lookup: `data/links/index.json`
- [x] Analytics stored in link's JSON file

### Web UI
- [x] Clean, minimal design (no frameworks, pure HTML/CSS)
- [x] Single page for creating links
- [x] Stats page per short code
- [x] Mobile responsive
- [x] No JavaScript required (progressive enhancement optional)

### Production Features
- [x] Rate limiting (in-memory, configurable)
- [x] Input validation and sanitization
- [x] Error handling with proper HTTP status codes
- [x] Graceful handling of corrupted data files
- [x] Thread-safe file operations

## API Endpoints

### Web Pages
| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Landing page with link creation form |
| `/<short_code>` | GET | Redirect to original URL |
| `/<short_code>/stats` | GET | View click analytics for link |

### API (JSON responses)
| Route | Method | Description |
|-------|--------|-------------|
| `/api/shorten` | POST | Create short link (JSON body: `{url, custom_code?}`) |
| `/api/links` | GET | List all short links with stats |

## Data Schema

### Link JSON (`data/links/{short_code}.json`)
```json
{
  "short_code": "abc123",
  "original_url": "https://example.com/long/url",
  "created_at": "2024-01-15T10:30:00Z",
  "click_count": 42,
  "clicks": [
    {
      "timestamp": "2024-01-15T11:00:00Z",
      "referrer": "https://twitter.com/...",
      "user_agent": "Mozilla/5.0...",
      "ip": "192.168.1.1"
    }
  ]
}
```

### Index JSON (`data/links/index.json`)
```json
{
  "version": 1,
  "short_codes": ["abc123", "xyz789"]
}
```

## Configuration (Environment Variables)
| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_HOST` | `0.0.0.0` | Host to bind |
| `FLASK_PORT` | `5000` | Port to bind |
| `FLASK_DEBUG` | `False` | Debug mode |
| `DATA_DIR` | `./data` | Data directory path |
| `BASE_URL` | `http://localhost:5000` | Base URL for short links |
| `RATE_LIMIT` | `30` | Max requests per minute per IP |
| `SHORT_CODE_LENGTH` | `6` | Length of auto-generated codes |

## Rate Limiting
- In-memory sliding window rate limiting
- Default: 30 requests per minute per IP
- Returns 429 Too Many Requests when exceeded
- Applies to `/api/shorten` endpoint

## Error Handling
- Invalid URL format: 400 Bad Request
- Short code not found: 404 Not Found
- Rate limit exceeded: 429 Too Many Requests
- Server error: 500 Internal Server Error
- All errors return JSON with `error` field

## File Structure
```
url-shortener/
├── app.py          # Single-file Flask application
├── data/           # Data directory (created automatically)
│   └── links/      # JSON files for each link
├── requirements.txt
├── run.sh
└── README.md
```

## Usage

### Quick Start
```bash
pip install -r requirements.txt
python app.py
```

### Run Script
```bash
chmod +x run.sh
./run.sh
```

### Docker (optional)
```dockerfile
FROM python:3.11-slim
COPY app.py requirements.txt ./
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["python", "app.py"]
```

## Security Considerations
- URL validation prevents open redirect vulnerabilities
- Short codes use URL-safe base62 characters only
- No user authentication (intentional for simplicity)
- Rate limiting prevents abuse
- Input sanitization for XSS prevention in stats display

## License
Public domain / Unlicense
