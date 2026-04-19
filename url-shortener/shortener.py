#!/usr/bin/env python3
"""
Zero setup URL Shortener with analytics
Single file, no dependencies, no database. Just run it.
"""
import json
import time
import random
import string
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

DATA_FILE = "links.json"
PORT = 8000

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"links": {}, "stats": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def generate_id(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

class RequestHandler(BaseHTTPRequestHandler):
    def _send_html(self, html, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.lstrip("/")

        # Redirect short links
        if len(path) == 6 and path in self.server.data["links"]:
            link = self.server.data["links"][path]
            link["clicks"] += 1
            link["click_log"].append({
                "time": int(time.time()),
                "referer": self.headers.get("Referer", ""),
                "user_agent": self.headers.get("User-Agent", "")
            })
            save_data(self.server.data)
            self.send_response(302)
            self.send_header("Location", link["url"])
            self.end_headers()
            return

        # Main UI
        if path == "" or path == "index":
            self._send_html(MAIN_UI)
            return

        # Stats page
        if path == "stats":
            stats = []
            for slug, link in self.server.data["links"].items():
                stats.append({
                    "slug": slug,
                    "url": link["url"],
                    "created": link["created"],
                    "clicks": link["clicks"]
                })
            self._send_json(stats)
            return

        self._send_html("<h1>404 Not Found</h1>", 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/create":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            params = parse_qs(body)

            url = params.get("url", [None])[0]
            if not url:
                self._send_json({"error": "No URL provided"}, 400)
                return

            parsed_url = urlparse(url)
            if not parsed_url.scheme:
                url = "https://" + url

            slug = generate_id()
            self.server.data["links"][slug] = {
                "url": url,
                "created": int(time.time()),
                "clicks": 0,
                "click_log": []
            }
            save_data(self.server.data)

            self._send_json({
                "slug": slug,
                "short_url": f"http://{self.headers['Host']}/{slug}",
                "url": url
            })
            return

        self._send_json({"error": "Not found"}, 404)


MAIN_UI = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>URL Shortener</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: system-ui, -apple-system, sans-serif; max-width: 600px; margin: 4rem auto; padding: 0 20px; background: #f8fafc; color: #1e293b; }
        h1 { font-weight: 700; font-size: 2rem; margin-bottom: 2rem; text-align: center; }
        .box { background: white; border-radius: 12px; padding: 2rem; box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1); }
        input { width: 100%; padding: 14px; border: 2px solid #e2e8f0; border-radius: 8px; font-size: 1rem; margin-bottom: 1rem; }
        button { width: 100%; padding: 14px; background: #2563eb; color: white; border: none; border-radius: 8px; font-weight: 600; font-size: 1rem; cursor: pointer; }
        button:hover { background: #1d4ed8; }
        #result { margin-top: 1rem; padding: 1rem; background: #f0fdf4; border-radius: 8px; display: none; }
        .link { font-weight: 600; color: #166534; }
        .stats { margin-top: 3rem; }
        .stat-row { display: flex; justify-content: space-between; padding: 12px; border-bottom: 1px solid #f1f5f9; }
    </style>
</head>
<body>
    <h1>🔗 Simple URL Shortener</h1>
    <div class="box">
        <input id="urlInput" type="text" placeholder="Paste your long URL here..." autocomplete="off">
        <button onclick="shortenUrl()">Shorten URL</button>
        <div id="result">
            Your short link: <span class="link" id="shortLink"></span>
        </div>
    </div>

    <div class="box stats" style="margin-top: 2rem;">
        <h3 style="margin-bottom: 1rem;">📊 Recent Links</h3>
        <div id="statsList"></div>
    </div>

    <script>
        async function shortenUrl() {
            const url = document.getElementById('urlInput').value.trim();
            const res = await fetch('/api/create', {
                method: 'POST',
                body: 'url=' + encodeURIComponent(url),
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
            });
            const data = await res.json();
            document.getElementById('shortLink').textContent = data.short_url;
            document.getElementById('result').style.display = 'block';
            loadStats();
        }

        async function loadStats() {
            const res = await fetch('/stats');
            const links = await res.json();
            let html = '';
            links.reverse().slice(0,10).forEach(link => {
                html += `<div class="stat-row">
                    <div><a href="/${link.slug}" target="_blank">/${link.slug}</a></div>
                    <div>${link.clicks} clicks</div>
                </div>`;
            });
            document.getElementById('statsList').innerHTML = html;
        }

        loadStats();
    </script>
</body>
</html>
"""

def run_server():
    server = HTTPServer(("", PORT), RequestHandler)
    server.data = load_data()
    print(f"✅ URL Shortener running on http://localhost:{PORT}")
    print(f"💾 Data stored in {DATA_FILE}")
    print("\nPress Ctrl+C to stop\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()

if __name__ == "__main__":
    run_server()
