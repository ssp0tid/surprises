# Micro URL Shortener

✅ Single file, self-hosted, zero setup URL shortener service.
No external databases, no config files, no accounts. Just works.

## Features
✅ Shorten any URL with optional custom slug
✅ Click tracking for every short link
✅ Optional expiration time (1 hour to 1 year)
✅ Clean responsive mobile-friendly UI
✅ Proper 302 redirects
✅ Auto-expired links cleanup
✅ REST API
✅ Zero configuration
✅ Built with FastAPI + SQLite

## Run it
```bash
# Clone or just download main.py
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn pydantic

python main.py
```

Then visit: http://localhost:8000

## Usage
1. Paste any URL
2. Optional: enter custom slug
3. Optional: set expiration time
4. Click shorten
5. Done!

Append `+` to any short URL to view statistics:
`http://localhost:8000/abc123+`

## API
```
POST /api/shorten
{
  "url": "https://example.com",
  "custom_slug": "mylink",
  "expire_hours": 24
}
```

## Production
Works great behind any reverse proxy (nginx, caddy). Can handle thousands of links easily.
All data is stored in `urls.db` SQLite file.

---
Made with ❤️ as a single file utility.
