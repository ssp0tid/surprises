#!/usr/bin/env python3
"""
URL Shortener - Single File Flask Application
Self-hosted URL shortener with click analytics. No database required.
Stores data as JSON files in the filesystem.
"""

import os
import json
import random
import re
import threading
import time
from datetime import datetime, timezone
from functools import wraps
from urllib.parse import urlparse

from flask import Flask, request, jsonify, redirect, render_template_string, abort

# =============================================================================
# Configuration
# =============================================================================

DATA_DIR = os.environ.get("DATA_DIR", "./data")
LINKS_DIR = os.path.join(DATA_DIR, "links")
INDEX_FILE = os.path.join(LINKS_DIR, "index.json")
BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000")
SHORT_CODE_LENGTH = int(os.environ.get("SHORT_CODE_LENGTH", "6"))
RATE_LIMIT = int(os.environ.get("RATE_LIMIT", "30"))  # requests per minute
RATE_WINDOW = 60  # seconds

# =============================================================================
# Flask App
# =============================================================================

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

# Thread lock for file operations
file_lock = threading.Lock()

# Rate limiting storage: {ip: [(timestamp, count), ...]}
rate_limit_store = {}
rate_limit_lock = threading.Lock()

# =============================================================================
# HTML Templates
# =============================================================================

INDEX_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>URL Shortener</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 500px;
        }
        h1 { color: #333; margin-bottom: 8px; font-size: 28px; }
        .subtitle { color: #666; margin-bottom: 30px; font-size: 14px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; color: #444; font-weight: 500; }
        input[type="url"], input[type="text"] {
            width: 100%;
            padding: 14px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.2s;
        }
        input:focus { outline: none; border-color: #007bff; }
        input[readonly] { background: #f8f9fa; cursor: not-allowed; }
        .btn {
            width: 100%;
            padding: 14px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }
        .btn:hover { background: #0056b3; }
        .btn:disabled { background: #ccc; cursor: not-allowed; }
        .result {
            margin-top: 20px;
            padding: 16px;
            background: #e8f5e9;
            border-radius: 8px;
            display: none;
        }
        .result.show { display: block; }
        .result-label { color: #2e7d32; font-size: 12px; font-weight: 600; text-transform: uppercase; margin-bottom: 8px; }
        .result-url {
            color: #1b5e20;
            font-size: 18px;
            font-weight: 600;
            word-break: break-all;
        }
        .result-url a { color: #1b5e20; text-decoration: none; }
        .result-url a:hover { text-decoration: underline; }
        .copy-btn {
            margin-top: 12px;
            padding: 10px 20px;
            background: #4caf50;
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            cursor: pointer;
        }
        .copy-btn:hover { background: #388e3c; }
        .error {
            margin-top: 20px;
            padding: 16px;
            background: #ffebee;
            border-radius: 8px;
            color: #c62828;
            display: none;
        }
        .error.show { display: block; }
        .links-section { margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px; }
        .links-title { color: #666; font-size: 14px; margin-bottom: 15px; }
        .link-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 6px;
            margin-bottom: 8px;
        }
        .link-short { font-weight: 600; color: #007bff; }
        .link-count { color: #666; font-size: 14px; }
        .link-stats { font-size: 12px; color: #999; }
        .rate-limit-notice {
            margin-top: 15px;
            font-size: 12px;
            color: #999;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>URL Shortener</h1>
        <p class="subtitle">Create short links with click analytics</p>

        <form id="shorten-form">
            <div class="form-group">
                <label for="url">Long URL</label>
                <input type="url" id="url" name="url" placeholder="https://example.com/very/long/url" required>
            </div>
            <div class="form-group">
                <label for="custom-code">Custom Code (optional)</label>
                <input type="text" id="custom-code" name="custom_code" placeholder="my-link" maxlength="32" pattern="[a-zA-Z0-9_-]+">
            </div>
            <button type="submit" class="btn" id="submit-btn">Create Short Link</button>
        </form>

        <div id="result" class="result">
            <div class="result-label">Your Short Link</div>
            <div class="result-url"><a href="" id="short-url"></a></div>
            <button class="copy-btn" id="copy-btn">Copy to Clipboard</button>
        </div>

        <div id="error" class="error"></div>

        <p class="rate-limit-notice">Rate limit: 30 requests per minute</p>
    </div>

    <script>
        const form = document.getElementById('shorten-form');
        const result = document.getElementById('result');
        const shortUrlEl = document.getElementById('short-url');
        const copyBtn = document.getElementById('copy-btn');
        const errorEl = document.getElementById('error');
        const submitBtn = document.getElementById('submit-btn');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            errorEl.classList.remove('show');
            result.classList.remove('show');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Creating...';

            const url = document.getElementById('url').value;
            const customCode = document.getElementById('custom-code').value;

            try {
                const response = await fetch('/api/shorten', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url, custom_code: customCode || null })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || 'Failed to create short link');
                }

                shortUrlEl.href = data.short_url;
                shortUrlEl.textContent = data.short_url;
                result.classList.add('show');
            } catch (err) {
                errorEl.textContent = err.message;
                errorEl.classList.add('show');
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Create Short Link';
            }
        });

        copyBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(shortUrlEl.textContent);
            copyBtn.textContent = 'Copied!';
            setTimeout(() => { copyBtn.textContent = 'Copy to Clipboard'; }, 2000);
        });
    </script>
</body>
</html>
"""

STATS_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stats - {{ short_code }}</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
            max-width: 900px;
            margin: 0 auto;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 30px;
            flex-wrap: wrap;
            gap: 20px;
        }
        h1 { color: #333; font-size: 24px; }
        .back-link { color: #007bff; text-decoration: none; }
        .back-link:hover { text-decoration: underline; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-value { font-size: 32px; font-weight: 700; color: #007bff; }
        .stat-label { color: #666; font-size: 14px; margin-top: 5px; }
        .url-display {
            background: #e3f2fd;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 30px;
            word-break: break-all;
        }
        .url-label { font-size: 12px; color: #666; text-transform: uppercase; margin-bottom: 8px; }
        .url-value { color: #1976d2; font-size: 16px; }
        h2 { color: #333; margin-bottom: 20px; font-size: 18px; }
        .clicks-table {
            width: 100%;
            border-collapse: collapse;
        }
        .clicks-table th, .clicks-table td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #eee;
        }
        .clicks-table th { color: #666; font-weight: 600; font-size: 12px; text-transform: uppercase; }
        .clicks-table tr:hover { background: #f8f9fa; }
        .empty-state { text-align: center; color: #999; padding: 40px; }
        .no-scrolls { color: #999; font-style: italic; }
        @media (max-width: 600px) {
            .clicks-table { font-size: 14px; }
            .clicks-table th, .clicks-table td { padding: 8px; }
            .stat-value { font-size: 24px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>Stats: {{ short_code }}</h1>
                <a href="/" class="back-link">← Create new link</a>
            </div>
            <a href="/{{ short_code }}" class="back-link">Open short link →</a>
        </div>

        <div class="url-display">
            <div class="url-label">Original URL</div>
            <div class="url-value">{{ original_url }}</div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{{ total_clicks }}</div>
                <div class="stat-label">Total Clicks</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ created_date }}</div>
                <div class="stat-label">Created</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ unique_referrers }}</div>
                <div class="stat-label">Unique Referrers</div>
            </div>
        </div>

        <h2>Click History</h2>
        {% if clicks %}
        <table class="clicks-table">
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Referrer</th>
                    <th>User Agent</th>
                </tr>
            </thead>
            <tbody>
                {% for click in clicks %}
                <tr>
                    <td>{{ click.timestamp }}</td>
                    <td>{{ click.referrer }}</td>
                    <td>{{ click.user_agent }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="empty-state">
            <p class="no-scrolls">No clicks recorded yet</p>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

ERROR_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error {{ code }}</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            text-align: center;
            padding: 40px;
        }
        .code { font-size: 72px; font-weight: 700; color: #e0e0e0; }
        .message { font-size: 24px; color: #666; margin: 20px 0; }
        a { color: #007bff; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <div class="code">{{ code }}</div>
        <div class="message">{{ message }}</div>
        <a href="/">← Go to homepage</a>
    </div>
</body>
</html>
"""

# =============================================================================
# Utility Functions
# =============================================================================


def generate_short_code(length: int = SHORT_CODE_LENGTH) -> str:
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "".join(random.choice(chars) for _ in range(length))


def validate_url(url: str) -> bool:
    """Validate URL format."""
    if not url or not isinstance(url, str):
        return False
    try:
        result = urlparse(url)
        return bool(result.scheme in ("http", "https") and result.netloc)
    except Exception:
        return False


def validate_short_code(code: str) -> bool:
    """Validate short code format (alphanumeric + hyphen/underscore)."""
    if not code or not isinstance(code, str):
        return False
    return bool(re.match(r"^[a-zA-Z0-9_-]+$", code) and len(code) <= 32)


def ensure_data_dir():
    """Ensure data directory exists."""
    os.makedirs(LINKS_DIR, exist_ok=True)
    if not os.path.exists(INDEX_FILE):
        save_index([])


def load_index() -> list:
    """Load short code index."""
    try:
        with open(INDEX_FILE, "r") as f:
            data = json.load(f)
            return data.get("short_codes", [])
    except Exception:
        return []


def save_index(codes: list):
    """Save short code index."""
    with open(INDEX_FILE, "w") as f:
        json.dump({"version": 1, "short_codes": codes}, f, indent=2)


def load_link(short_code: str) -> dict | None:
    """Load link data from JSON file."""
    link_file = os.path.join(LINKS_DIR, f"{short_code}.json")
    try:
        with open(link_file, "r") as f:
            return json.load(f)
    except Exception:
        return None


def save_link(link_data: dict):
    """Save link data to JSON file."""
    short_code = link_data["short_code"]
    link_file = os.path.join(LINKS_DIR, f"{short_code}.json")
    with open(link_file, "w") as f:
        json.dump(link_data, f, indent=2, default=str)


def add_click(short_code: str, click_data: dict):
    """Add a click to link data."""
    with file_lock:
        link = load_link(short_code)
        if link:
            link["click_count"] = link.get("click_count", 0) + 1
            link["clicks"] = link.get("clicks", [])
            link["clicks"].insert(0, click_data)  # Most recent first
            # Keep only last 1000 clicks to prevent file bloat
            link["clicks"] = link["clicks"][:1000]
            save_link(link)


# =============================================================================
# Rate Limiting
# =============================================================================


def check_rate_limit(ip: str) -> tuple[bool, int]:
    """
    Check if IP is within rate limit.
    Returns (allowed, remaining_requests).
    """
    now = time.time()
    window_start = now - RATE_WINDOW

    with rate_limit_lock:
        # Clean old entries
        if ip in rate_limit_store:
            rate_limit_store[ip] = [
                (ts, count) for ts, count in rate_limit_store[ip] if ts > window_start
            ]
        else:
            rate_limit_store[ip] = []

        # Count requests in window
        total_requests = sum(count for ts, count in rate_limit_store[ip])

        if total_requests >= RATE_LIMIT:
            return False, 0

        # Add current request
        rate_limit_store[ip].append((now, 1))
        return True, RATE_LIMIT - total_requests - 1


def rate_limit(func):
    """Decorator for rate limiting endpoints."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        ip = request.remote_addr or "127.0.0.1"
        allowed, remaining = check_rate_limit(ip)

        if not allowed:
            response = jsonify(
                {
                    "error": "Rate limit exceeded. Please wait before trying again.",
                    "retry_after": RATE_WINDOW,
                }
            )
            response.status_code = 429
            response.headers["Retry-After"] = str(RATE_WINDOW)
            response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT)
            response.headers["X-RateLimit-Remaining"] = "0"
            return response

        response = func(*args, **kwargs)
        if hasattr(response, "headers"):
            response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response

    return wrapper


# =============================================================================
# Routes - Web Pages
# =============================================================================


@app.route("/")
def index():
    """Landing page with link creation form."""
    return render_template_string(INDEX_TEMPLATE)


@app.route("/<short_code>")
def redirect_to_url(short_code: str):
    """Redirect to the original URL and track the click."""
    with file_lock:
        link = load_link(short_code)

    if not link:
        abort(404)

    # Track click
    click_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "referrer": request.referrer or "direct",
        "user_agent": request.user_agent.string[:512]
        if request.user_agent.string
        else "unknown",
        "ip": request.remote_addr or "127.0.0.1",
    }

    # Add click in background (non-blocking for redirect speed)
    try:
        add_click(short_code, click_data)
    except Exception:
        pass  # Don't fail redirect if click tracking fails

    return redirect(link["original_url"], code=302)


@app.route("/<short_code>/stats")
def show_stats(short_code: str):
    """Show click statistics for a short link."""
    with file_lock:
        link = load_link(short_code)

    if not link:
        abort(404)

    # Format data for template
    created_date = link.get("created_at", "Unknown")
    if created_date != "Unknown":
        try:
            dt = datetime.fromisoformat(created_date.replace("Z", "+00:00"))
            created_date = dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    # Get unique referrers
    clicks = link.get("clicks", [])
    unique_referrers = len(set(c.get("referrer", "direct") for c in clicks))

    return render_template_string(
        STATS_TEMPLATE,
        short_code=short_code,
        original_url=link["original_url"],
        total_clicks=link.get("click_count", 0),
        created_date=created_date,
        unique_referrers=unique_referrers,
        clicks=clicks[:100],  # Show last 100 clicks
    )


@app.errorhandler(404)
def not_found(e):
    """404 error page."""
    return render_template_string(
        ERROR_TEMPLATE, code=404, message="Link not found"
    ), 404


@app.errorhandler(500)
def server_error(e):
    """500 error page."""
    return render_template_string(ERROR_TEMPLATE, code=500, message="Server error"), 500


# =============================================================================
# Routes - API
# =============================================================================


@app.route("/api/shorten", methods=["POST"])
@rate_limit
def api_shorten():
    """API endpoint to create a short link."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON body required"}), 400

        url = data.get("url", "").strip()
        custom_code = data.get("custom_code", "").strip() or None

        # Validate URL
        if not validate_url(url):
            return jsonify(
                {"error": "Invalid URL format. Must start with http:// or https://"}
            ), 400

        # Determine short code
        short_code = None
        with file_lock:
            index = load_index()

            if custom_code:
                # Validate custom code
                if not validate_short_code(custom_code):
                    return jsonify(
                        {
                            "error": "Invalid custom code. Use only letters, numbers, hyphens, and underscores."
                        }
                    ), 400

                # Check if custom code already exists
                if custom_code in index:
                    return jsonify(
                        {"error": f'Custom code "{custom_code}" is already taken'}
                    ), 409

                short_code = custom_code
            else:
                # Generate unique short code
                for _ in range(10):  # Max 10 attempts
                    code = generate_short_code()
                    if code not in index:
                        short_code = code
                        break

                if not short_code:
                    return jsonify(
                        {"error": "Failed to generate unique code. Please try again."}
                    ), 500

            # Create link data
            link_data = {
                "short_code": short_code,
                "original_url": url,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "click_count": 0,
                "clicks": [],
            }

            # Save link and update index
            save_link(link_data)
            index.append(short_code)
            save_index(index)

        return jsonify(
            {
                "short_code": short_code,
                "short_url": f"{BASE_URL}/{short_code}",
                "original_url": url,
            }
        ), 201

    except Exception as e:
        app.logger.error(f"Error creating short link: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/links", methods=["GET"])
def api_list_links():
    """API endpoint to list all links with stats."""
    with file_lock:
        index = load_index()
        links = []

        for short_code in index:
            link = load_link(short_code)
            if link:
                links.append(
                    {
                        "short_code": short_code,
                        "short_url": f"{BASE_URL}/{short_code}",
                        "original_url": link["original_url"],
                        "created_at": link.get("created_at"),
                        "click_count": link.get("click_count", 0),
                    }
                )

    return jsonify({"links": links})


@app.route("/api/links/<short_code>", methods=["GET"])
def api_get_link(short_code: str):
    """API endpoint to get a specific link with full click data."""
    with file_lock:
        link = load_link(short_code)

    if not link:
        return jsonify({"error": "Link not found"}), 404

    return jsonify(link)


@app.route("/api/links/<short_code>", methods=["DELETE"])
def api_delete_link(short_code: str):
    """API endpoint to delete a link."""
    with file_lock:
        index = load_index()

        if short_code not in index:
            return jsonify({"error": "Link not found"}), 404

        # Remove from index
        index.remove(short_code)
        save_index(index)

        # Delete link file
        link_file = os.path.join(LINKS_DIR, f"{short_code}.json")
        if os.path.exists(link_file):
            os.remove(link_file)

    return jsonify({"message": f'Link "{short_code}" deleted'})


# =============================================================================
# Health Check
# =============================================================================


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "version": "1.0.0"})


# =============================================================================
# Initialize
# =============================================================================

with app.app_context():
    ensure_data_dir()

# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"

    print(f"Starting URL Shortener on http://{host}:{port}")
    print(f"Data directory: {DATA_DIR}")
    print(f"Rate limit: {RATE_LIMIT} requests/minute")
    app.run(host=host, port=port, debug=debug)
