#!/usr/bin/env python3
"""
Self-hosted expiring URL shortener
Single file, no database, flat file storage
"""
import os
import json
import time
import hashlib
import secrets
from datetime import datetime, timedelta
from urllib.parse import urlparse
from flask import Flask, render_template_string, request, redirect, jsonify, abort

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)

# Configuration
STORAGE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'links.json')
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
MAX_HOURS = 720  # 30 days
MAX_CLICKS = 1000
SHORT_CODE_LENGTH = 6

# Load storage
def load_links():
    if not os.path.exists(STORAGE_FILE):
        return {}
    try:
        with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_links(links):
    with open(STORAGE_FILE, 'w', encoding='utf-8') as f:
        json.dump(links, f, indent=2)

def cleanup_expired():
    links = load_links()
    now = time.time()
    cleaned = {k: v for k, v in links.items() 
               if v['expires_at'] > now and v['remaining_clicks'] > 0}
    if len(cleaned) != len(links):
        save_links(cleaned)
    return cleaned

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def generate_short_code():
    return secrets.token_urlsafe(SHORT_CODE_LENGTH)[:SHORT_CODE_LENGTH]

# HTML Template
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Expiring Link Shortener</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8fafc;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            color: #1e293b;
        }
        .container {
            background: white;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.08);
            padding: 40px;
            max-width: 520px;
            width: 100%;
        }
        h1 {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
            text-align: center;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .subtitle {
            text-align: center;
            color: #64748b;
            margin-bottom: 32px;
            font-size: 14px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 6px;
            font-weight: 500;
            font-size: 14px;
            color: #475569;
        }
        input, select {
            width: 100%;
            padding: 14px 16px;
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            font-size: 15px;
            transition: all 0.2s;
            outline: none;
        }
        input:focus, select:focus {
            border-color: #6366f1;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }
        .row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
            border: none;
            border-radius: 10px;
            font-weight: 600;
            font-size: 15px;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover {
            transform: translateY(-1px);
            box-shadow: 0 8px 20px rgba(99, 102, 241, 0.3);
        }
        button:active {
            transform: translateY(0);
        }
        .result {
            margin-top: 24px;
            padding: 20px;
            background: #f1f5f9;
            border-radius: 10px;
            display: none;
        }
        .result.show {
            display: block;
            animation: fadeIn 0.3s ease;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .short-url {
            font-family: monospace;
            font-size: 16px;
            padding: 12px;
            background: white;
            border-radius: 8px;
            margin-bottom: 12px;
            word-break: break-all;
        }
        .copy-btn {
            background: #475569;
            padding: 10px 16px;
            width: auto;
            font-size: 13px;
        }
        .copy-btn:hover {
            background: #334155;
            box-shadow: none;
        }
        .status {
            margin-top: 12px;
            font-size: 13px;
            color: #64748b;
        }
        .error {
            margin-top: 16px;
            padding: 12px;
            background: #fef2f2;
            border: 1px solid #fecaca;
            border-radius: 8px;
            color: #dc2626;
            font-size: 14px;
            display: none;
        }
        .error.show { display: block; }
        .footer {
            margin-top: 32px;
            text-align: center;
            font-size: 12px;
            color: #94a3b8;
        }
        @media (max-width: 480px) {
            .container { padding: 24px; }
            .row { grid-template-columns: 1fr; }
            h1 { font-size: 24px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⟡ Link Shortener</h1>
        <p class="subtitle">Create temporary links that expire automatically</p>
        
        <form id="shortenForm">
            <div class="form-group">
                <label for="url">Destination URL</label>
                <input type="url" id="url" placeholder="https://example.com" required autocomplete="off">
            </div>
            
            <div class="row">
                <div class="form-group">
                    <label for="expire_hours">Expire after</label>
                    <select id="expire_hours">
                        <option value="1">1 hour</option>
                        <option value="6">6 hours</option>
                        <option value="24" selected>24 hours</option>
                        <option value="72">3 days</option>
                        <option value="168">1 week</option>
                        <option value="720">30 days</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="max_clicks">Maximum clicks</label>
                    <select id="max_clicks">
                        <option value="1">1 click</option>
                        <option value="5">5 clicks</option>
                        <option value="10" selected>10 clicks</option>
                        <option value="50">50 clicks</option>
                        <option value="100">100 clicks</option>
                        <option value="0">Unlimited</option>
                    </select>
                </div>
            </div>
            
            <button type="submit">Create Short Link</button>
        </form>
        
        <div class="error" id="error"></div>
        
        <div class="result" id="result">
            <div>Your short link:</div>
            <div class="short-url" id="shortUrl"></div>
            <button class="copy-btn" id="copyBtn">Copy to clipboard</button>
            <div class="status" id="status"></div>
        </div>
        
        <div class="footer">
            No tracking. No login. Self hosted.
        </div>
    </div>

    <script>
        const form = document.getElementById('shortenForm');
        const result = document.getElementById('result');
        const error = document.getElementById('error');
        const shortUrl = document.getElementById('shortUrl');
        const status = document.getElementById('status');
        const copyBtn = document.getElementById('copyBtn');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            result.classList.remove('show');
            error.classList.remove('show');
            
            const body = JSON.stringify({
                url: document.getElementById('url').value,
                expire_hours: parseInt(document.getElementById('expire_hours').value),
                max_clicks: parseInt(document.getElementById('max_clicks').value)
            });

            try {
                const res = await fetch('/api/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body
                });
                
                const data = await res.json();
                
                if (res.ok) {
                    shortUrl.textContent = data.short_url;
                    status.textContent = `Expires: ${data.expires} • Remaining clicks: ${data.remaining_clicks}`;
                    result.classList.add('show');
                } else {
                    error.textContent = data.error;
                    error.classList.add('show');
                }
            } catch (err) {
                error.textContent = 'Failed to create link';
                error.classList.add('show');
            }
        });

        copyBtn.addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(shortUrl.textContent);
                copyBtn.textContent = '✓ Copied!';
                setTimeout(() => copyBtn.textContent = 'Copy to clipboard', 2000);
            } catch {
                alert('Copy failed');
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/create', methods=['POST'])
def create_link():
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'URL is required'}), 400
        
        url = data['url'].strip()
        if not is_valid_url(url):
            return jsonify({'error': 'Please enter a valid URL'}), 400
        
        expire_hours = min(int(data.get('expire_hours', 24)), MAX_HOURS)
        max_clicks = min(int(data.get('max_clicks', 10)), MAX_CLICKS)
        
        if expire_hours < 1:
            expire_hours = 1
        
        links = cleanup_expired()
        
        code = generate_short_code()
        while code in links:
            code = generate_short_code()
        
        expires_at = time.time() + (expire_hours * 3600)
        remaining = max_clicks if max_clicks > 0 else 999999
        
        links[code] = {
            'url': url,
            'expires_at': expires_at,
            'remaining_clicks': remaining,
            'created_at': time.time()
        }
        
        save_links(links)
        
        expire_dt = datetime.fromtimestamp(expires_at)
        expires_str = expire_dt.strftime('%b %d, %H:%M')
        
        return jsonify({
            'short_url': f"{BASE_URL}/{code}",
            'expires': expires_str,
            'remaining_clicks': max_clicks if max_clicks > 0 else 'Unlimited'
        })
        
    except Exception as e:
        app.logger.error(f"Error creating link: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/<code>')
def redirect_link(code):
    links = load_links()
    
    if code not in links:
        abort(404)
    
    link = links[code]
    now = time.time()
    
    if link['expires_at'] <= now or link['remaining_clicks'] <= 0:
        cleanup_expired()
        abort(404)
    
    link['remaining_clicks'] -= 1
    save_links(links)
    
    return redirect(link['url'], code=302)

@app.errorhandler(404)
def not_found(e):
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Link Expired</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: system-ui; text-align: center; padding-top: 100px; background: #f8fafc; }
            h1 { color: #64748b; font-size: 32px; }
            p { color: #94a3b8; margin-top: 8px; }
            a { color: #6366f1; margin-top: 24px; display: inline-block; text-decoration: none; }
        </style>
    </head>
    <body>
        <h1>Link expired or not found</h1>
        <p>This link has reached its click limit or has expired</p>
        <a href="/">Create a new link</a>
    </body>
    </html>
    """, 404

if __name__ == '__main__':
    import sys
    host = sys.argv[1] if len(sys.argv) > 1 else '0.0.0.0'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
    print(f"🚀 Expiring Link Shortener running on http://{host}:{port}")
    print(f"📁 Storage file: {STORAGE_FILE}")
    app.run(host=host, port=port, debug=False)
