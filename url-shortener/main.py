#!/usr/bin/env python3
"""
Self-hosted micro URL Shortener
Single file, zero setup, production ready
"""
import os
import re
import sqlite3
import time
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, validator

app = FastAPI(title="Micro URL Shortener", version="1.0.0")
DB_PATH = "urls.db"

# -----------------------------------------------------------------------------
# Database Setup
# -----------------------------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS urls (
            slug TEXT PRIMARY KEY,
            original_url TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            expires_at INTEGER,
            clicks INTEGER DEFAULT 0
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_expires_at ON urls(expires_at)')
    conn.commit()
    conn.close()

init_db()

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def generate_slug(url: str, length: int = 6) -> str:
    salt = str(time.time()).encode()
    h = hashlib.sha256(url.encode() + salt).hexdigest()
    return h[:length]

def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme in ('http', 'https'), result.netloc])
    except:
        return False

def slug_available(slug: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT 1 FROM urls WHERE slug = ?', (slug,))
    exists = c.fetchone() is not None
    conn.close()
    return not exists

SLUG_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,32}$')

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------
class ShortenRequest(BaseModel):
    url: str
    custom_slug: Optional[str] = None
    expire_hours: Optional[int] = None

    @validator('url')
    def validate_url(cls, v):
        if not is_valid_url(v):
            raise ValueError('Please enter a valid HTTP/HTTPS URL')
        return v

    @validator('custom_slug')
    def validate_slug(cls, v):
        if v is not None and not SLUG_PATTERN.match(v):
            raise ValueError('Custom slug must be 3-32 chars: letters, numbers, -, _')
        return v

    @validator('expire_hours')
    def validate_expire(cls, v):
        if v is not None and (v < 1 or v > 8760):
            raise ValueError('Expiration must be between 1 hour and 1 year')
        return v

# -----------------------------------------------------------------------------
# Web UI
# -----------------------------------------------------------------------------
UI_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Micro URL Shortener</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: system-ui, -apple-system, sans-serif; background: #f8fafc; color: #1e293b; line-height: 1.5; }
        .container { max-width: 600px; margin: 0 auto; padding: 2rem 1rem; min-height: 100vh; }
        header { text-align: center; margin-bottom: 2rem; }
        h1 { font-size: 1.8rem; font-weight: 700; color: #0f172a; margin-bottom: 0.5rem; }
        .card { background: white; border-radius: 12px; padding: 1.5rem; box-shadow: 0 1px 3px 0 rgba(0,0,0,0.1); margin-bottom: 1.5rem; }
        form { display: flex; flex-direction: column; gap: 1rem; }
        input, button { width: 100%; padding: 0.875rem 1rem; border-radius: 8px; font-size: 1rem; border: 2px solid #e2e8f0; }
        input:focus { outline: none; border-color: #3b82f6; }
        button { background: #3b82f6; color: white; border: none; font-weight: 600; cursor: pointer; transition: background 0.15s; }
        button:hover { background: #2563eb; }
        .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
        @media (max-width: 480px) { .form-row { grid-template-columns: 1fr; } }
        .result { display: none; margin-top: 1rem; padding: 1rem; background: #f0fdf4; border-radius: 8px; border-left: 4px solid #22c55e; }
        .result.show { display: block; }
        .short-url { font-family: monospace; font-size: 1.1rem; word-break: break-all; font-weight: 600; margin-bottom: 0.5rem; }
        .info { color: #64748b; font-size: 0.875rem; text-align: center; margin-top: 1.5rem; }
        .error { display: none; background: #fef2f2; color: #dc2626; padding: 1rem; border-radius: 8px; margin-top: 1rem; }
        .error.show { display: block; }
        label { display: block; font-weight: 500; margin-bottom: 0.375rem; color: #334155; font-size: 0.875rem; }
        .stats { color: #64748b; font-size: 0.875rem; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔗 Micro Shortener</h1>
            <p style="color: #64748b;">Self-hosted, zero setup URL shortener</p>
        </header>

        <div class="card">
            <form id="shortenForm">
                <div>
                    <label for="url">URL to shorten</label>
                    <input type="url" id="url" placeholder="https://example.com" required autofocus>
                </div>

                <div class="form-row">
                    <div>
                        <label for="custom_slug">Custom slug</label>
                        <input type="text" id="custom_slug" placeholder="my-link">
                    </div>
                    <div>
                        <label for="expire_hours">Expire after (hours)</label>
                        <input type="number" id="expire_hours" min="1" max="8760" placeholder="optional">
                    </div>
                </div>

                <button type="submit">Shorten URL</button>
            </form>

            <div id="error" class="error"></div>

            <div id="result" class="result">
                <div>Your short URL:</div>
                <div class="short-url" id="shortUrl"></div>
                <div class="stats" id="stats"></div>
                <button onclick="copyUrl()" style="margin-top: 0.75rem;">Copy to clipboard</button>
            </div>
        </div>

        <div class="info">
            <p>No tracking. No accounts. Just works.</p>
            <p style="margin-top: 0.5rem; font-size: 0.75rem;">Append + to any short URL to view stats</p>
        </div>
    </div>

    <script>
        const form = document.getElementById('shortenForm');
        const result = document.getElementById('result');
        const error = document.getElementById('error');
        const shortUrlEl = document.getElementById('shortUrl');
        const statsEl = document.getElementById('stats');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            result.classList.remove('show');
            error.classList.remove('show');

            const body = {
                url: document.getElementById('url').value,
                custom_slug: document.getElementById('custom_slug').value || null,
                expire_hours: parseInt(document.getElementById('expire_hours').value) || null
            };

            try {
                const res = await fetch('/api/shorten', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });

                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail || 'Failed to shorten URL');
                }

                const data = await res.json();
                shortUrlEl.textContent = window.location.origin + '/' + data.slug;
                statsEl.textContent = `Clicks: ${data.clicks} | Created: ${new Date(data.created_at * 1000).toLocaleString()}`;
                result.classList.add('show');
            } catch (err) {
                error.textContent = err.message;
                error.classList.add('show');
            }
        });

        function copyUrl() {
            navigator.clipboard.writeText(shortUrlEl.textContent);
            alert('Copied to clipboard!');
        }
    </script>
</body>
</html>
"""

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def root():
    return UI_HTML

@app.post("/api/shorten")
async def shorten_url(req: ShortenRequest):
    now = int(time.time())

    if req.custom_slug:
        if not slug_available(req.custom_slug):
            raise HTTPException(status_code=400, detail="This custom slug is already taken")
        slug = req.custom_slug
    else:
        # Generate unique slug
        while True:
            slug = generate_slug(req.url)
            if slug_available(slug):
                break

    expires_at = None
    if req.expire_hours:
        expires_at = now + (req.expire_hours * 3600)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO urls (slug, original_url, created_at, expires_at, clicks)
        VALUES (?, ?, ?, ?, 0)
    ''', (slug, req.url, now, expires_at))
    conn.commit()
    conn.close()

    return {
        "slug": slug,
        "original_url": req.url,
        "created_at": now,
        "expires_at": expires_at,
        "clicks": 0
    }

@app.get("/{slug}")
async def redirect_to_url(slug: str):
    now = int(time.time())

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Clean up expired first
    c.execute('DELETE FROM urls WHERE expires_at IS NOT NULL AND expires_at < ?', (now,))
    conn.commit()

    c.execute('SELECT original_url FROM urls WHERE slug = ?', (slug,))
    row = c.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="URL not found or expired")

    original_url = row[0]

    # Increment click count
    c.execute('UPDATE urls SET clicks = clicks + 1 WHERE slug = ?', (slug,))
    conn.commit()
    conn.close()

    return RedirectResponse(url=original_url, status_code=302)

@app.get("/{slug}+")
async def get_url_stats(slug: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute('SELECT * FROM urls WHERE slug = ?', (slug,))
    row = c.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="URL not found")

    return {
        "slug": row['slug'],
        "original_url": row['original_url'],
        "created_at": row['created_at'],
        "expires_at": row['expires_at'],
        "clicks": row['clicks']
    }

@app.on_event("startup")
async def startup_event():
    print("\n✅ Micro URL Shortener running!")
    print("   Visit: http://localhost:8000")
    print("   Database: urls.db\n")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )
