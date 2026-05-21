#!/usr/bin/env python3
"""
HTTP Replay Server - A local CLI tool that records HTTP requests to SQLite,
provides web UI to view/search, and allows replay with variable substitution.
"""

import os
import re
import sqlite3
import json
import time
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import socket
import uuid
from typing import Optional, Dict, Any, List

import click
from flask import Flask, render_template_string, request, jsonify, g


# =============================================================================
# Database Layer
# =============================================================================

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS recordings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid TEXT UNIQUE NOT NULL,
                    timestamp TEXT NOT NULL,
                    method TEXT NOT NULL,
                    url TEXT NOT NULL,
                    path TEXT NOT NULL,
                    query_string TEXT,
                    request_headers TEXT,
                    request_body BLOB,
                    response_status INTEGER,
                    response_headers TEXT,
                    response_body BLOB,
                    duration_ms REAL,
                    target_host TEXT,
                    target_port INTEGER,
                    notes TEXT,
                    tags TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS replay_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recording_uuid TEXT NOT NULL,
                    name TEXT NOT NULL,
                    variable_substitutions TEXT,
                    header_modifications TEXT,
                    delay_ms INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (recording_uuid) REFERENCES recordings(uuid)
                )
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_recordings_timestamp 
                ON recordings(timestamp)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_recordings_method 
                ON recordings(method)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_recordings_url 
                ON recordings(url)
            ''')
            conn.commit()
    
    def save_recording(self, data: Dict[str, Any]) -> str:
        recording_uuid = str(uuid.uuid4())
        with self._get_connection() as conn:
            conn.execute('''
                INSERT INTO recordings (
                    uuid, timestamp, method, url, path, query_string,
                    request_headers, request_body, response_status,
                    response_headers, response_body, duration_ms,
                    target_host, target_port, notes, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                recording_uuid,
                data.get('timestamp', datetime.now().isoformat()),
                data.get('method', 'GET'),
                data.get('url', ''),
                data.get('path', ''),
                data.get('query_string', ''),
                data.get('request_headers', '{}'),
                data.get('request_body'),
                data.get('response_status', 0),
                data.get('response_headers', '{}'),
                data.get('response_body'),
                data.get('duration_ms', 0),
                data.get('target_host', ''),
                data.get('target_port', 80),
                data.get('notes', ''),
                data.get('tags', '')
            ))
            conn.commit()
        return recording_uuid
    
    def get_recordings(self, search: Optional[str] = None, 
                      method: Optional[str] = None,
                      limit: int = 100) -> List[Dict]:
        query = 'SELECT * FROM recordings'
        conditions = []
        params = []
        
        if search:
            conditions.append('(url LIKE ? OR path LIKE ? OR notes LIKE ?)')
            search_pattern = f'%{search}%'
            params.extend([search_pattern, search_pattern, search_pattern])
        
        if method:
            conditions.append('method = ?')
            params.append(method)
        
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_recording(self, uuid: str) -> Optional[Dict]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                'SELECT * FROM recordings WHERE uuid = ?', (uuid,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def delete_recording(self, uuid: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute(
                'DELETE FROM recordings WHERE uuid = ?', (uuid,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def update_recording(self, uuid: str, data: Dict[str, Any]) -> bool:
        fields = []
        params = []
        for key in ['notes', 'tags']:
            if key in data:
                fields.append(f'{key} = ?')
                params.append(data[key])
        
        if not fields:
            return False
        
        params.append(uuid)
        query = f'UPDATE recordings SET {", ".join(fields)} WHERE uuid = ?'
        
        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0
    
    def save_replay_config(self, data: Dict[str, Any]) -> int:
        with self._get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO replay_configs (
                    recording_uuid, name, variable_substitutions,
                    header_modifications, delay_ms, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['recording_uuid'],
                data['name'],
                json.dumps(data.get('variable_substitutions', {})),
                json.dumps(data.get('header_modifications', {})),
                data.get('delay_ms', 0),
                datetime.now().isoformat()
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_replay_configs(self, recording_uuid: str) -> List[Dict]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                'SELECT * FROM replay_configs WHERE recording_uuid = ? '
                'ORDER BY created_at DESC',
                (recording_uuid,)
            )
            rows = cursor.fetchall()
            result = []
            for row in rows:
                r = dict(row)
                r['variable_substitutions'] = json.loads(
                    r['variable_substitutions'] or '{}'
                )
                r['header_modifications'] = json.loads(
                    r['header_modifications'] or '{}'
                )
                result.append(r)
            return result
    
    def get_stats(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT 
                    COUNT(*) as total,
                    COUNT(DISTINCT method) as methods,
                    MIN(timestamp) as earliest,
                    MAX(timestamp) as latest,
                    AVG(duration_ms) as avg_duration
                FROM recordings
            ''')
            row = cursor.fetchone()
            cursor2 = conn.execute('''
                SELECT method, COUNT(*) as count 
                GROUP BY method ORDER BY count DESC
            ''')
            method_counts = dict(cursor2.fetchall())
            return {
                'total': row['total'] or 0,
                'methods': row['methods'] or 0,
                'earliest': row['earliest'],
                'latest': row['latest'],
                'avg_duration': row['avg_duration'] or 0,
                'method_counts': method_counts
            }


# =============================================================================
# Proxy Server
# =============================================================================

class ProxyHandler(BaseHTTPRequestHandler):
    """HTTP proxy handler that records requests and responses."""
    
    protocol_version = 'HTTP/1.1'
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass
    
    def do_REQUEST(self):
        """Handle GET, POST, PUT, DELETE, etc."""
        self._handle_request(self.command)
    
    def do_GET(self):
        self._handle_request('GET')
    
    def do_POST(self):
        self._handle_request('POST')
    
    def do_PUT(self):
        self._handle_request('PUT')
    
    def do_DELETE(self):
        self._handle_request('DELETE')
    
    def do_PATCH(self):
        self._handle_request('PATCH')
    
    def do_HEAD(self):
        self._handle_request('HEAD')
    
    def do_OPTIONS(self):
        self._handle_request('OPTIONS')
    
    def _handle_request(self, method: str):
        server = self.server
        db = server.db
        
        # Parse target from headers or path
        target_host = self.headers.get('X-Target-Host', server.target_host)
        target_port = int(self.headers.get('X-Target-Port', server.target_port))
        
        # Build request
        path = self.path
        if path.startswith('http://'):
            # Full URL proxy mode
            from urllib.parse import urlparse
            parsed = urlparse(path)
            target_host = parsed.hostname
            target_port = parsed.port or 80
            path = parsed.path
            if parsed.query:
                path += '?' + parsed.query
        
        query_string = ''
        if '?' in path:
            path, query_string = path.split('?', 1)
        
        # Get request body
        content_length = int(self.headers.get('Content-Length', 0))
        request_body = self.rfile.read(content_length) if content_length > 0 else None
        
        # Build headers dict
        headers = {}
        for key, value in self.headers.items():
            if key.lower() not in ['host', 'connection', 'proxy-connection']:
                headers[key] = value
        
        start_time = time.time()
        
        # Connect to target
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(60)
            sock.connect((target_host, target_port))
            
            # Forward request
            request_line = f'{method} {path} HTTP/1.1\r\n'
            if query_string:
                request_line = f'{method} {path}?{query_string} HTTP/1.1\r\n'
            
            sock.send(request_line.encode())
            
            # Send headers
            headers['Host'] = target_host
            for key, value in headers.items():
                sock.send(f'{key}: {value}\r\n'.encode())
            sock.send(b'\r\n')
            
            # Send body
            if request_body:
                sock.send(request_body)
            
            # Read response
            response = self._read_response(sock)
            sock.close()
            
        except Exception as e:
            self.send_error(502, f"Proxy error: {str(e)}")
            return
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Parse response
        response_parts = response.split(b'\r\n\r\n', 1)
        response_headers_raw = response_parts[0].decode('latin-1')
        response_body = response_parts[1] if len(response_parts) > 1 else b''
        
        # Parse status line
        status_line = response_headers_raw.split('\r\n')[0]
        match = re.search(r'HTTP/[\d.]+ (\d+)', status_line)
        status = int(match.group(1)) if match else 502
        
        # Parse response headers
        response_headers = {}
        for line in response_headers_raw.split('\r\n')[1:]:
            if ':' in line:
                key, value = line.split(':', 1)
                response_headers[key.strip()] = value.strip()
        
        # Save recording
        recording_data = {
            'timestamp': datetime.now().isoformat(),
            'method': method,
            'url': f'http://{target_host}:{target_port}{path}',
            'path': path,
            'query_string': query_string,
            'request_headers': json.dumps(headers),
            'request_body': request_body,
            'response_status': status,
            'response_headers': json.dumps(response_headers),
            'response_body': response_body,
            'duration_ms': duration_ms,
            'target_host': target_host,
            'target_port': target_port,
        }
        
        try:
            db.save_recording(recording_data)
        except Exception as e:
            server.logger.warning(f"Failed to save recording: {e}")
        
        # Send response to client
        self.send_response(status)
        for key, value in response_headers.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(response_body)
    
    def _read_response(self, sock: socket.socket) -> bytes:
        """Read complete HTTP response."""
        response = b''
        while True:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
                # Check for end of headers
                if b'\r\n\r\n' in response:
                    # Check if chunked encoding
                    if b'Chunked' in response:
                        # For chunked, read until 0\r\n\r\n
                        if b'0\r\n\r\n' in response:
                            break
                    else:
                        # Content-Length
                        match = re.search(
                            b'Content-Length: (\\d+)', response, re.IGNORECASE
                        )
                        if match:
                            content_length = int(match.group(1))
                            header_end = response.index(b'\r\n\r\n')
                            body_received = len(response) - header_end - 4
                            if body_received >= content_length:
                                break
                        else:
                            # No content length, read until close
                            pass
            except socket.timeout:
                break
        
        return response


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Threaded HTTP server for handling concurrent requests."""
    
    def __init__(self, server_address, request_handlerClass, 
                 target_host: str, target_port: int, db: Database,
                 logger):
        super().__init__(server_address, request_handlerClass)
        self.target_host = target_host
        self.target_port = target_port
        self.db = db
        self.logger = logger


# =============================================================================
# Flask Web UI
# =============================================================================

app = Flask(__name__)
DATABASE: Optional[Database] = None


@app.before_request
def before_request():
    g.db = DATABASE


HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>HTTP Replay Server</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0; padding: 20px; 
            background: #f5f5f5; 
            color: #333;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { 
            color: #2c3e50; 
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        .toolbar {
            display: flex; gap: 10px; margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .search-box {
            flex: 1; min-width: 200px;
            padding: 10px; border: 1px solid #ddd;
            border-radius: 4px; font-size: 14px;
        }
        .btn {
            padding: 10px 20px; border: none; border-radius: 4px;
            cursor: pointer; font-size: 14px; font-weight: 500;
        }
        .btn-primary { background: #3498db; color: white; }
        .btn-primary:hover { background: #2980b9; }
        .btn-danger { background: #e74c3c; color: white; }
        .btn-danger:hover { background: #c0392b; }
        .btn-success { background: #27ae60; color: white; }
        .btn-success:hover { background: #229954; }
        .btn-secondary { background: #95a5a6; color: white; }
        .btn-secondary:hover { background: #7f8c8d; }
        
        table { 
            width: 100%; border-collapse: collapse;
            background: white; border-radius: 4px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #34495e; color: white; font-weight: 500; }
        tr:hover { background: #f8f9fa; }
        .method { 
            font-weight: bold; padding: 4px 8px; border-radius: 3px;
            font-size: 12px;
        }
        .method-GET { background: #3498db; color: white; }
        .method-POST { background: #27ae60; color: white; }
        .method-PUT { background: #f39c12; color: white; }
        .method-DELETE { background: #e74c3c; color: white; }
        .method-PATCH { background: #9b59b6; color: white; }
        
        .status-2xx { color: #27ae60; }
        .status-4xx { color: #f39c12; }
        .status-5xx { color: #e74c3c; }
        
        .actions { display: flex; gap: 5px; }
        .actions .btn { padding: 6px 12px; font-size: 12px; }
        
        .modal {
            display: none; position: fixed; top: 0; left: 0;
            width: 100%; height: 100%; background: rgba(0,0,0,0.5);
            z-index: 1000;
        }
        .modal.active { display: flex; align-items: center; justify-content: center; }
        .modal-content {
            background: white; padding: 20px; border-radius: 8px;
            max-width: 600px; width: 90%; max-height: 80vh;
            overflow-y: auto;
        }
        .modal-header {
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 20px;
        }
        .modal-header h2 { margin: 0; }
        .close { 
            background: none; border: none; font-size: 24px;
            cursor: pointer; color: #999;
        }
        .close:hover { color: #333; }
        
        .form-group { margin-bottom: 15px; }
        .form-group label { 
            display: block; margin-bottom: 5px; font-weight: 500;
        }
        .form-group input, .form-group textarea {
            width: 100%; padding: 8px; border: 1px solid #ddd;
            border-radius: 4px; font-size: 14px;
        }
        .form-group textarea { min-height: 100px; font-family: monospace; }
        
        .detail-row {
            display: flex; border-bottom: 1px solid #eee;
            padding: 10px 0;
        }
        .detail-label { 
            width: 150px; font-weight: 500; color: #7f8c8d;
            flex-shrink: 0;
        }
        .detail-value { flex: 1; word-break: break-all; }
        
        .code-block {
            background: #2c3e50; color: #ecf0f1; padding: 15px;
            border-radius: 4px; overflow-x: auto;
            font-family: 'Monaco', 'Menlo', monospace; font-size: 13px;
        }
        
        .tabs { display: flex; border-bottom: 2px solid #eee; margin-bottom: 20px; }
        .tab {
            padding: 10px 20px; cursor: pointer; border: none;
            background: none; font-size: 14px; color: #7f8c8d;
        }
        .tab.active { 
            color: #3498db; border-bottom: 2px solid #3498db; 
            margin-bottom: -2px;
        }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        
        .stats-bar {
            display: flex; gap: 20px; margin-bottom: 20px;
            background: white; padding: 15px; border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stat { text-align: center; }
        .stat-value { font-size: 24px; font-weight: bold; color: #3498db; }
        .stat-label { font-size: 12px; color: #7f8c8d; }
        
        textarea.json-input {
            font-family: monospace; min-height: 150px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>HTTP Replay Server</h1>
        
        <div class="stats-bar">
            <div class="stat">
                <div class="stat-value">{{ stats.total }}</div>
                <div class="stat-label">Total Recordings</div>
            </div>
            <div class="stat">
                <div class="stat-value">{{ stats.avg_duration|round(1) }}ms</div>
                <div class="stat-label">Avg Duration</div>
            </div>
            <div class="stat">
                <div class="stat-value">{{ stats.earliest or 'N/A' }}</div>
                <div class="stat-label">Earliest</div>
            </div>
            <div class="stat">
                <div class="stat-value">{{ stats.latest or 'N/A' }}</div>
                <div class="stat-label">Latest</div>
            </div>
        </div>
        
        <div class="toolbar">
            <input type="text" class="search-box" id="searchInput" 
                   placeholder="Search by URL, path, or notes..." value="{{ search }}">
            <select class="search-box" id="methodFilter" style="flex: 0; min-width: 120px;">
                <option value="">All Methods</option>
                <option value="GET">GET</option>
                <option value="POST">POST</option>
                <option value="PUT">PUT</option>
                <option value="DELETE">DELETE</option>
                <option value="PATCH">PATCH</option>
            </select>
            <button class="btn btn-primary" onclick="loadRecordings()">Search</button>
            <button class="btn btn-secondary" onclick="clearSearch()">Clear</button>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Method</th>
                    <th>URL</th>
                    <th>Status</th>
                    <th>Duration</th>
                    <th>Timestamp</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody id="recordingsTable">
                {% for recording in recordings %}
                <tr>
                    <td><span class="method method-{{ recording.method }}">{{ recording.method }}</span></td>
                    <td>{{ recording.path }}{% if recording.query_string %}?{{ recording.query_string }}{% endif %}</td>
                    <td>
                        {% if recording.response_status %}
                        <span class="status-{{ (recording.response_status // 100) }}xx">{{ recording.response_status }}</span>
                        {% else %}pending{% endif %}
                    </td>
                    <td>{{ recording.duration_ms|round(1) }}ms</td>
                    <td>{{ recording.timestamp }}</td>
                    <td class="actions">
                        <button class="btn btn-primary" onclick="viewDetail('{{ recording.uuid }}')">View</button>
                        <button class="btn btn-success" onclick="showReplayModal('{{ recording.uuid }}')">Replay</button>
                        <button class="btn btn-danger" onclick="deleteRecording('{{ recording.uuid }}')">Delete</button>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    <!-- Detail Modal -->
    <div class="modal" id="detailModal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>Request Details</h2>
                <button class="close" onclick="closeModal('detailModal')">&times;</button>
            </div>
            <div id="detailContent"></div>
        </div>
    </div>
    
    <!-- Replay Modal -->
    <div class="modal" id="replayModal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>Replay Request</h2>
                <button class="close" onclick="closeModal('replayModal')">&times;</button>
            </div>
            <form id="replayForm">
                <input type="hidden" id="replayUuid" name="uuid">
                <div class="form-group">
                    <label>Name</label>
                    <input type="text" name="name" required placeholder="My Replay Config">
                </div>
                <div class="form-group">
                    <label>Variable Substitutions (JSON)</label>
                    <textarea name="variables" class="json-input" placeholder='{"{{"{{"}}"userId{{"}}"}}": 123, "{{"{{"}}"apiKey{{"}}"}}": "new-key"}'></textarea>
                    <small style="color: #7f8c8d;">Use {{"{{"}}"variableName{{"}}"}} syntax in URLs/bodies</small>
                </div>
                <div class="form-group">
                    <label>Header Modifications (JSON)</label>
                    <textarea name="headers" class="json-input" placeholder='{"Authorization": "Bearer new-token", "X-Custom-Header": "value"}'></textarea>
                </div>
                <div class="form-group">
                    <label>Delay (ms)</label>
                    <input type="number" name="delay" value="0" min="0">
                </div>
                <button type="submit" class="btn btn-success">Replay Now</button>
            </form>
        </div>
    </div>
    
    <script>
        function loadRecordings() {
            const search = document.getElementById('searchInput').value;
            const method = document.getElementById('methodFilter').value;
            window.location.href = '/?search=' + encodeURIComponent(search) + '&method=' + method;
        }
        
        function clearSearch() {
            window.location.href = '/';
        }
        
        function viewDetail(uuid) {
            fetch('/api/recordings/' + uuid)
                .then(r => r.json())
                .then(data => {
                    let html = '';
                    
                    // Request section
                    html += '<div class="tabs">';
                    html += '<button class="tab active" onclick="switchTab(\'request\')">Request</button>';
                    html += '<button class="tab" onclick="switchTab(\'response\')">Response</button>';
                    html += '<button class="tab" onclick="switchTab(\'edit\')">Edit</button>';
                    html += '</div>';
                    
                    // Request tab
                    html += '<div class="tab-content active" id="tab-request">';
                    html += '<div class="detail-row"><div class="detail-label">Method</div><div class="detail-value">' + data.method + '</div></div>';
                    html += '<div class="detail-row"><div class="detail-label">URL</div><div class="detail-value">' + data.url + '</div></div>';
                    html += '<div class="detail-row"><div class="detail-label">Path</div><div class="detail-value">' + data.path + '</div></div>';
                    if (data.query_string) {
                        html += '<div class="detail-row"><div class="detail-label">Query</div><div class="detail-value">' + data.query_string + '</div></div>';
                    }
                    html += '<div class="detail-row"><div class="detail-label">Headers</div><div class="detail-value"><pre class="code-block">' + JSON.stringify(JSON.parse(data.request_headers || '{}'), null, 2) + '</pre></div></div>';
                    if (data.request_body) {
                        let body = data.request_body;
                        try { body = atob(body); } catch(e) {}
                        html += '<div class="detail-row"><div class="detail-label">Body</div><div class="detail-value"><pre class="code-block">' + escapeHtml(body) + '</pre></div></div>';
                    }
                    html += '</div>';
                    
                    // Response tab
                    html += '<div class="tab-content" id="tab-response">';
                    html += '<div class="detail-row"><div class="detail-label">Status</div><div class="detail-value">' + data.response_status + '</div></div>';
                    html += '<div class="detail-row"><div class="detail-label">Duration</div><div class="detail-value">' + data.duration_ms + 'ms</div></div>';
                    html += '<div class="detail-row"><div class="detail-label">Headers</div><div class="detail-value"><pre class="code-block">' + JSON.stringify(JSON.parse(data.response_headers || '{}'), null, 2) + '</pre></div></div>';
                    if (data.response_body) {
                        let body = data.response_body;
                        try { body = atob(body); } catch(e) {}
                        html += '<div class="detail-row"><div class="detail-label">Body</div><div class="detail-value"><pre class="code-block">' + escapeHtml(body.substring(0, 10000)) + '</pre></div></div>';
                    }
                    html += '</div>';
                    
                    // Edit tab
                    html += '<div class="tab-content" id="tab-edit">';
                    html += '<form id="editForm">';
                    html += '<div class="form-group"><label>Notes</label><textarea name="notes" class="json-input">' + escapeHtml(data.notes || '') + '</textarea></div>';
                    html += '<div class="form-group"><label>Tags (comma-separated)</label><input type="text" name="tags" value="' + escapeHtml(data.tags || '') + '"></div>';
                    html += '<button type="submit" class="btn btn-primary">Save</button>';
                    html += '</form>';
                    html += '</div>';
                    
                    document.getElementById('detailContent').innerHTML = html;
                    
                    // Form handler
                    document.getElementById('editForm').onsubmit = function(e) {
                        e.preventDefault();
                        const formData = new FormData(this);
                        fetch('/api/recordings/' + uuid, {
                            method: 'PATCH',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                notes: formData.get('notes'),
                                tags: formData.get('tags')
                            })
                        }).then(r => r.json()).then(data => {
                            alert('Saved!');
                            loadRecordings();
                        });
                    };
                    
                    document.getElementById('detailModal').classList.add('active');
                });
        }
        
        function switchTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById('tab-' + tab).classList.add('active');
        }
        
        function showReplayModal(uuid) {
            document.getElementById('replayUuid').value = uuid;
            document.getElementById('replayModal').classList.add('active');
        }
        
        document.getElementById('replayForm').onsubmit = function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const uuid = formData.get('uuid');
            
            let variables = {};
            try {
                variables = JSON.parse(formData.get('variables') || '{}');
            } catch(e) {
                alert('Invalid JSON in variable substitutions');
                return;
            }
            
            let headers = {};
            try {
                headers = JSON.parse(formData.get('headers') || '{}');
            } catch(e) {
                alert('Invalid JSON in header modifications');
                return;
            }
            
            fetch('/api/replay', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    uuid: uuid,
                    name: formData.get('name'),
                    variable_substitutions: variables,
                    header_modifications: headers,
                    delay_ms: parseInt(formData.get('delay')) || 0
                })
            }).then(r => r.json()).then(data => {
                if (data.success) {
                    alert('Replay completed! Status: ' + data.status);
                } else {
                    alert('Replay failed: ' + data.error);
                }
            });
        };
        
        function deleteRecording(uuid) {
            if (!confirm('Delete this recording?')) return;
            fetch('/api/recordings/' + uuid, {method: 'DELETE'})
                .then(r => r.json())
                .then(data => {
                    loadRecordings();
                });
        }
        
        function closeModal(id) {
            document.getElementById(id).classList.remove('active');
        }
        
        function escapeHtml(text) {
            if (!text) return '';
            return text.toString()
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#039;');
        }
        
        // Enter key搜索
        document.getElementById('searchInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') loadRecordings();
        });
    </script>
</body>
</html>
'''


# =============================================================================
# Flask Routes
# =============================================================================

@app.route('/')
def index():
    search = request.args.get('search', '')
    method = request.args.get('method', '')
    recordings = g.db.get_recordings(search=search, method=method)
    stats = g.db.get_stats()
    return render_template_string(
        HTML_TEMPLATE, 
        recordings=recordings, 
        stats=stats,
        search=search
    )


@app.route('/api/recordings/<uuid>')
def get_recording(uuid):
    recording = g.db.get_recording(uuid)
    if not recording:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(recording)


@app.route('/api/recordings/<uuid>', methods=['DELETE'])
def delete_recording(uuid):
    success = g.db.delete_recording(uuid)
    return jsonify({'success': success})


@app.route('/api/recordings/<uuid>', methods=['PATCH'])
def update_recording(uuid):
    data = request.json
    success = g.db.update_recording(uuid, data)
    return jsonify({'success': success})


@app.route('/api/replay', methods=['POST'])
def replay_request():
    """Execute a replay with variable substitution."""
    data = request.json
    uuid = data.get('uuid')
    
    # Get original recording
    recording = g.db.get_recording(uuid)
    if not recording:
        return jsonify({'success': False, 'error': 'Recording not found'})
    
    # Apply delay if specified
    delay_ms = data.get('delay_ms', 0)
    if delay_ms > 0:
        time.sleep(delay_ms / 1000)
    
    # Apply variable substitutions
    path = recording['path']
    query_string = recording['query_string'] or ''
    request_body = recording['request_body']
    
    variables = data.get('variable_substitutions', {})
    for var_name, var_value in variables.items():
        placeholder = '{{' + var_name + '}}'
        path = path.replace(placeholder, str(var_value))
        query_string = query_string.replace(placeholder, str(var_value))
        if request_body:
            request_body = request_body.replace(placeholder, str(var_value))
    
    # Apply header modifications
    request_headers = json.loads(recording['request_headers'] or '{}')
    header_mods = data.get('header_modifications', {})
    for header_name, header_value in header_mods.items():
        request_headers[header_name] = header_value
    
    # Build target URL
    target_host = recording['target_host']
    target_port = recording['target_port']
    url = f"http://{target_host}:{target_port}{path}"
    if query_string:
        url += '?' + query_string
    
    # Execute replay
    import urllib.request
    import urllib.error
    
    req = urllib.request.Request(
        url,
        data=request_body.encode() if request_body else None,
        headers=request_headers,
        method=recording['method']
    )
    
    try:
        response = urllib.request.urlopen(req, timeout=30)
        status = response.getcode()
        return jsonify({
            'success': True,
            'status': status,
            'message': 'Request replayed successfully'
        })
    except urllib.error.HTTPError as e:
        return jsonify({
            'success': False,
            'error': f'HTTP {e.code}: {e.reason}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


# =============================================================================
# CLI Commands
# =============================================================================

@click.group()
@click.pass_context
def cli(ctx):
    """HTTP Replay Server - Record, view, and replay HTTP requests."""
    pass


@cli.command()
@click.option('--host', default='127.0.0.1', help='Proxy server host')
@click.option('--port', default=8080, type=int, help='Proxy server port')
@click.option('--target-host', default='localhost', help='Default target host to proxy to')
@click.option('--target-port', default=80, type=int, help='Default target port')
@click.option('--db-path', default='recordings.db', help='SQLite database path')
def proxy(host: str, port: int, target_host: str, target_port: int, db_path: str):
    """Run the HTTP proxy server."""
    global DATABASE
    DATABASE = Database(db_path)
    
    # Save DATABASE reference for proxy
    app.config['DATABASE'] = DATABASE
    
    server = ThreadedHTTPServer(
        (host, port),
        ProxyHandler,
        target_host,
        target_port,
        DATABASE,
        click.echo
    )
    
    click.echo(f"Starting proxy server on {host}:{port}")
    click.echo(f"Default target: {target_host}:{target_port}")
    click.echo(f"Database: {db_path}")
    click.echo("Press Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        click.echo("\nShutting down...")


@cli.command()
@click.option('--db-path', default='recordings.db', help='SQLite database path')
@click.option('--host', default='127.0.0.1', help='Web server host')
@click.option('--port', default=5000, type=int, help='Web server port')
def web(db_path: str, host: str, port: int):
    """Run the web UI server."""
    global DATABASE
    DATABASE = Database(db_path)
    app.config['DATABASE'] = DATABASE
    
    click.echo(f"Starting web UI on http://{host}:{port}")
    app.run(host=host, port=port, debug=False)


@cli.command()
@click.option('--port', default=8080, type=int, help='Proxy server port')
@click.option('--web-port', default=5000, type=int, help='Web UI port')
@click.option('--target-host', default='localhost', help='Default target host')
@click.option('--target-port', default=80, type=int, help='Default target port')
@click.option('--db-path', default='recordings.db', help='SQLite database path')
def run(port: int, web_port: int, target_host: str, target_port: int, db_path: str):
    """Run both proxy and web server."""
    global DATABASE
    DATABASE = Database(db_path)
    app.config['DATABASE'] = DATABASE
    
    # Start proxy server
    proxy_server = ThreadedHTTPServer(
        ('127.0.0.1', port),
        ProxyHandler,
        target_host,
        target_port,
        DATABASE,
        click.echo
    )
    
    proxy_thread = threading.Thread(target=proxy_server.serve_forever)
    proxy_thread.daemon = True
    proxy_thread.start()
    
    click.echo(f"Proxy server: http://127.0.0.1:{port}")
    click.echo(f"Web UI: http://127.0.0.1:{web_port}")
    click.echo(f"Database: {db_path}")
    click.echo("Press Ctrl+C to stop")
    
    # Run web server (blocking)
    from werkzeug.serving import make_server
    server = make_server('127.0.0.1', web_port, app)
    server.serve_forever()


@cli.command('list')
@click.option('--db-path', default='recordings.db', help='SQLite database path')
@click.option('--search', help='Search pattern')
@click.option('--method', help='Filter by HTTP method')
@click.option('--limit', default=100, type=int, help='Limit results')
def list_recordings(db_path: str, search: str, method: str, limit: int):
    """List recorded requests."""
    db = Database(db_path)
    recordings = db.get_recordings(search=search, method=method, limit=limit)
    
    if not recordings:
        click.echo("No recordings found.")
        return
    
    for r in recordings:
        status = r['response_status'] or 'pending'
        method = r['method']
        path = r['path']
        duration = r['duration_ms']
        ts = r['timestamp']
        click.echo(f"{method}: {status} - {path} ({duration}ms) [{ts}]")


@cli.command('show')
@click.argument('uuid')
@click.option('--db-path', default='recordings.db', help='SQLite database path')
def show_recording(uuid: str, db_path: str):
    """Show a recorded request in detail."""
    db = Database(db_path)
    recording = db.get_recording(uuid)
    
    if not recording:
        click.echo("Recording not found.")
        return
    
    click.echo(f"UUID: {recording['uuid']}")
    click.echo(f"Method: {recording['method']}")
    click.echo(f"URL: {recording['url']}")
    click.echo(f"Status: {recording['response_status']}")
    click.echo(f"Duration: {recording['duration_ms']}ms")
    click.echo(f"Timestamp: {recording['timestamp']}")
    click.echo(f"\nRequest Headers:")
    click.echo(json.dumps(json.loads(recording['request_headers'] or '{}'), indent=2))
    click.echo(f"\nResponse Headers:")
    click.echo(json.dumps(json.loads(recording['response_headers'] or '{}'), indent=2))


@cli.command('replay')
@click.argument('uuid')
@click.option('--db-path', default='recordings.db', help='SQLite database path')
@click.option('--variables', help='Variable substitutions as JSON')
@click.option('--headers', help='Header modifications as JSON')
@click.option('--delay', type=int, default=0, help='Delay in milliseconds')
def replay(uuid: str, db_path: str, variables: str, headers: str, delay: int):
    """Replay a recorded request."""
    db = Database(db_path)
    recording = db.get_recording(uuid)
    
    if not recording:
        click.echo("Recording not found.")
        return
    
    # Parse inputs
    var_subs = json.loads(variables) if variables else {}
    header_mods = json.loads(headers) if headers else {}
    
    # Apply substitutions
    path = recording['path']
    request_body = recording['request_body']
    
    for var_name, var_value in var_subs.items():
        placeholder = '{{' + var_name + '}}'
        path = path.replace(placeholder, str(var_value))
        if request_body:
            request_body = request_body.replace(placeholder, str(var_value))
    
    # Build request
    request_headers = json.loads(recording['request_headers'] or '{}')
    request_headers.update(header_mods)
    
    # Apply delay
    if delay > 0:
        click.echo(f"Waiting {delay}ms...")
        time.sleep(delay / 1000)
    
    # Execute request
    import urllib.request
    import urllib.error
    
    url = f"http://{recording['target_host']}:{recording['target_port']}{path}"
    
    try:
        req = urllib.request.Request(
            url,
            data=request_body.encode() if request_body else None,
            headers=request_headers,
            method=recording['method']
        )
        response = urllib.request.urlopen(req)
        click.echo(f"Success! Status: {response.getcode()}")
    except urllib.error.HTTPError as e:
        click.echo(f"Error: HTTP {e.code} - {e.reason}")
    except Exception as e:
        click.echo(f"Error: {e}")


@cli.command('stats')
@click.option('--db-path', default='recordings.db', help='SQLite database path')
def show_stats(db_path: str):
    """Show recording statistics."""
    db = Database(db_path)
    stats = db.get_stats()
    
    click.echo(f"Total Recordings: {stats['total']}")
    click.echo(f"Average Duration: {stats['avg_duration']:.1f}ms")
    click.echo(f"Methods Used: {stats['methods']}")
    if stats['earliest']:
        click.echo(f"Date Range: {stats['earliest']} to {stats['latest']}")
    if stats['method_counts']:
        click.echo("\nBy Method:")
        for method, count in stats['method_counts'].items():
            click.echo(f"  {method}: {count}")


@cli.command('delete')
@click.argument('uuid')
@click.option('--db-path', default='recordings.db', help='SQLite database path')
def delete(uuid: str, db_path: str):
    """Delete a recording."""
    db = Database(db_path)
    success = db.delete_recording(uuid)
    if success:
        click.echo("Recording deleted.")
    else:
        click.echo("Recording not found.")


@cli.command('init')
@click.option('--db-path', default='recordings.db', help='SQLite database path')
def init(db_path: str):
    """Initialize the database."""
    db = Database(db_path)
    click.echo(f"Database initialized: {db_path}")


if __name__ == '__main__':
    cli()