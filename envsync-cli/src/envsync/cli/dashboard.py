"""Web dashboard for envsync."""

import json
from http.server import HTTPServer, SimpleHTTPRequestHandler

from jinja2 import Template

DASHBOARD_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>envsync Dashboard</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #1a1a2e; color: #fff; min-height: 100vh; }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 1px solid #333; }
        h1 { font-size: 1.5rem; color: #00d4ff; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }
        .card { background: #16213e; border-radius: 8px; padding: 1.5rem; border: 1px solid #0f3460; }
        .card h2 { font-size: 1.1rem; margin-bottom: 1rem; color: #e94560; }
        .stat { font-size: 2rem; font-weight: bold; color: #00d4ff; }
        .stat-label { font-size: 0.875rem; color: #888; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 0.75rem; text-align: left; border-bottom: 1px solid #0f3460; }
        th { color: #e94560; font-weight: 600; }
        tr:hover { background: #1f2b4d; }
        .btn { background: #e94560; color: #fff; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer; }
        .btn:hover { background: #ff6b6b; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>envsync Dashboard</h1>
        </header>
        <div class="grid">
            <div class="card">
                <h2>Projects</h2>
                <div class="stat">{{ projects|length }}</div>
                <div class="stat-label">Total projects</div>
            </div>
            <div class="card">
                <h2>Groups</h2>
                <div class="stat">{{ groups|length }}</div>
                <div class="stat-label">Total groups</div>
            </div>
            <div class="card">
                <h2>Variables</h2>
                <div class="stat">{{ variables|length }}</div>
                <div class="stat-label">Global variables</div>
            </div>
        </div>
        <div class="card" style="margin-top: 1.5rem;">
            <h2>Global Variables</h2>
            <table>
                <thead><tr><th>Key</th><th>Value</th></tr></thead>
                <tbody>
                    {% for key, value in variables.items() %}
                    <tr><td>{{ key }}</td><td>{{ value }}</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>"""


def run_dashboard(port: int = 3000) -> None:
    template = Template(DASHBOARD_HTML)

    class DashboardHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/api/data":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                data = {"projects": [], "groups": [], "variables": {}}
                self.wfile.write(json.dumps(data).encode())
            else:
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                html = template.render(projects=[], groups=[], variables={})
                self.wfile.write(html.encode())

    server = HTTPServer(("localhost", port), DashboardHandler)
    print(f"Dashboard running at http://localhost:{port}")
    server.serve_forever()
