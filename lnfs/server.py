#!/usr/bin/env python3
"""
LNFS - Local Network File Sharing Server
A beautiful, feature-rich file sharing server with a modern dark UI.
"""

import os
import sys
import io
import re
import json
import mimetypes
import argparse
import socket
import zipfile
import hashlib
from pathlib import Path
from functools import wraps

from flask import (
    Flask,
    request,
    send_file,
    render_template_string,
    jsonify,
    abort,
    redirect,
    url_for,
)
from werkzeug.utils import secure_filename

try:
    import qrcode

    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False


# ============================================================================
# Configuration
# ============================================================================

APP_NAME = "LNFS"
DEFAULT_PORT = 8888
BUFFER_SIZE = 8192
MAX_FILE_PREVIEW_SIZE = 1024 * 1024  # 1MB for text preview
IMAGE_PREVIEW_SIZE = 1920  # Max dimension for image previews

# Allowed file extensions for preview
TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".py",
    ".js",
    ".json",
    ".html",
    ".css",
    ".xml",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".sh",
    ".bash",
    ".zsh",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".java",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".sql",
    ".log",
    ".csv",
}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".ico", ".svg"}
ARCHIVE_EXTENSIONS = {
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".7z",
    ".rar",
    ".tar.gz",
    ".tgz",
}

# ============================================================================
# Flask Application
# ============================================================================

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024 * 1024  # 16GB max upload
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

# Global state
serve_dir = os.getcwd()
password_hash = None


def get_local_ip():
    """Detect the local IP address on the network."""
    try:
        # Create a socket to determine the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        # Fallback to localhost if we can't determine the IP
        return "127.0.0.1"


def hash_password(password):
    """Create a SHA256 hash of the password."""
    return hashlib.sha256(password.encode()).hexdigest()


def check_auth(auth_header):
    """Check if the provided auth header matches the password."""
    if not password_hash:
        return True
    if not auth_header:
        return False
    try:
        scheme, token = auth_header.split(" ", 1)
        if scheme.lower() == "bearer":
            return hashlib.sha256(token.encode()).hexdigest() == password_hash
    except (ValueError, AttributeError):
        pass
    return False


def authenticate():
    """Send a 401 response that enables basic auth."""
    return (
        jsonify({"error": "Authentication required"}),
        401,
    )
    {"WWW-Authenticate": 'Bearer realm="LNFS"'}


def requires_auth(f):
    """Decorator to require authentication for a route."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if not check_auth(request.headers.get("Authorization", "")):
            return authenticate()
        return f(*args, **kwargs)

    return decorated


def get_file_icon(filename, is_dir=False):
    """Return an emoji icon based on file type."""
    if is_dir:
        return "📁"

    ext = Path(filename).suffix.lower()

    # Images
    if ext in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".ico"}:
        return "🖼️"
    # Videos
    elif ext in {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"}:
        return "🎬"
    # Audio
    elif ext in {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"}:
        return "🎵"
    # Documents
    elif ext in {".pdf"}:
        return "📕"
    elif ext in {".doc", ".docx", ".odt", ".rtf"}:
        return "📄"
    elif ext in {".xls", ".xlsx", ".csv", ".ods"}:
        return "📊"
    elif ext in {".ppt", ".pptx", ".odp"}:
        return "📽️"
    # Code
    elif ext in {
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".java",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".go",
        ".rs",
        ".rb",
        ".php",
        ".swift",
        ".kt",
    }:
        return "💻"
    # Web
    elif ext in {".html", ".htm", ".css", ".scss", ".sass", ".less"}:
        return "🌐"
    # Archives
    elif ext in ARCHIVE_EXTENSIONS:
        return "📦"
    # Text
    elif ext in TEXT_EXTENSIONS:
        return "📝"
    # Config
    elif ext in {
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".cfg",
        ".conf",
        ".env",
        ".properties",
    }:
        return "⚙️"
    # Executables
    elif ext in {".exe", ".msi", ".dmg", ".app", ".deb", ".rpm", ".apk"}:
        return "⚡"
    # Fonts
    elif ext in {".ttf", ".otf", ".woff", ".woff2", ".eot"}:
        return "🔤"
    # 3D models
    elif ext in {".obj", ".fbx", ".stl", ".3ds", ".blend", ".dae"}:
        return "🎲"
    else:
        return "📎"


def format_size(size):
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def format_path(rel_path):
    """Format a relative path for display."""
    if rel_path == ".":
        return "Root"
    parts = Path(rel_path).parts
    return " / ".join(parts) if parts else "Root"


# ============================================================================
# HTML Template
# ============================================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LNFS - Local Network File Sharing</title>
    <style>
        :root {
            --bg-primary: #1a1a2e;
            --bg-secondary: #16213e;
            --bg-tertiary: #0f3460;
            --accent: #e94560;
            --accent-hover: #ff6b6b;
            --text-primary: #eaeaea;
            --text-secondary: #a0a0a0;
            --border: #2a2a4a;
            --success: #00d26a;
            --warning: #ffb830;
            --error: #ff4757;
            --shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
            --radius: 12px;
            --transition: all 0.3s ease;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            line-height: 1.6;
        }

        /* Header */
        .header {
            background: var(--bg-secondary);
            padding: 1rem 2rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .logo-icon {
            font-size: 2rem;
        }

        .logo-text {
            font-size: 1.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent), var(--accent-hover));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .header-actions {
            display: flex;
            gap: 0.75rem;
            align-items: center;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.75rem 1.25rem;
            border: none;
            border-radius: var(--radius);
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
            transition: var(--transition);
        }

        .btn-primary {
            background: var(--accent);
            color: white;
        }

        .btn-primary:hover {
            background: var(--accent-hover);
            transform: translateY(-2px);
            box-shadow: var(--shadow);
        }

        .btn-secondary {
            background: var(--bg-tertiary);
            color: var(--text-primary);
        }

        .btn-secondary:hover {
            background: var(--border);
        }

        /* Main Container */
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }

        /* Breadcrumb */
        .breadcrumb {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 1rem 1.5rem;
            background: var(--bg-secondary);
            border-radius: var(--radius);
            margin-bottom: 1.5rem;
            overflow-x: auto;
            flex-wrap: wrap;
        }

        .breadcrumb-item {
            color: var(--text-secondary);
            text-decoration: none;
            padding: 0.25rem 0.75rem;
            border-radius: 6px;
            transition: var(--transition);
            white-space: nowrap;
            font-size: 0.9rem;
        }

        .breadcrumb-item:hover {
            background: var(--bg-tertiary);
            color: var(--text-primary);
        }

        .breadcrumb-separator {
            color: var(--text-secondary);
        }

        .breadcrumb-current {
            color: var(--accent);
            font-weight: 500;
        }

        /* Upload Zone */
        .upload-zone {
            border: 2px dashed var(--border);
            border-radius: var(--radius);
            padding: 3rem;
            text-align: center;
            margin-bottom: 2rem;
            transition: var(--transition);
            cursor: pointer;
            background: var(--bg-secondary);
        }

        .upload-zone:hover,
        .upload-zone.dragover {
            border-color: var(--accent);
            background: rgba(233, 69, 96, 0.1);
        }

        .upload-zone-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }

        .upload-zone-text {
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }

        .upload-zone-hint {
            font-size: 0.85rem;
            color: var(--text-secondary);
            opacity: 0.7;
        }

        #file-input {
            display: none;
        }

        /* Progress Bar */
        .progress-container {
            display: none;
            margin-bottom: 2rem;
            background: var(--bg-secondary);
            border-radius: var(--radius);
            padding: 1.5rem;
        }

        .progress-container.active {
            display: block;
        }

        .progress-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }

        .progress-title {
            font-weight: 500;
        }

        .progress-percent {
            color: var(--accent);
            font-weight: 700;
        }

        .progress-bar {
            height: 8px;
            background: var(--bg-tertiary);
            border-radius: 4px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--accent), var(--accent-hover));
            width: 0%;
            transition: width 0.3s ease;
            border-radius: 4px;
        }

        .progress-status {
            margin-top: 0.5rem;
            font-size: 0.85rem;
            color: var(--text-secondary);
        }

        /* File Grid */
        .file-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 1rem;
        }

        .file-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 1.25rem;
            cursor: pointer;
            transition: var(--transition);
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            gap: 0.75rem;
        }

        .file-card:hover {
            transform: translateY(-4px);
            box-shadow: var(--shadow);
            border-color: var(--accent);
        }

        .file-icon {
            font-size: 2.5rem;
        }

        .file-name {
            font-size: 0.9rem;
            word-break: break-word;
            max-width: 100%;
            color: var(--text-primary);
        }

        .file-size {
            font-size: 0.75rem;
            color: var(--text-secondary);
        }

        .file-actions {
            display: flex;
            gap: 0.5rem;
            margin-top: 0.5rem;
            opacity: 0;
            transition: var(--transition);
        }

        .file-card:hover .file-actions {
            opacity: 1;
        }

        .file-action-btn {
            padding: 0.4rem 0.6rem;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.75rem;
            transition: var(--transition);
        }

        .file-action-btn.download {
            background: var(--success);
            color: white;
        }

        .file-action-btn.delete {
            background: var(--error);
            color: white;
        }

        .file-action-btn:hover {
            transform: scale(1.1);
        }

        /* Empty State */
        .empty-state {
            text-align: center;
            padding: 4rem 2rem;
            color: var(--text-secondary);
        }

        .empty-state-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
        }

        .empty-state-text {
            font-size: 1.1rem;
        }

        /* Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 1000;
            justify-content: center;
            align-items: center;
            padding: 2rem;
        }

        .modal.active {
            display: flex;
        }

        .modal-content {
            background: var(--bg-secondary);
            border-radius: var(--radius);
            max-width: 900px;
            width: 100%;
            max-height: 90vh;
            overflow: auto;
            box-shadow: var(--shadow);
        }

        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1.25rem 1.5rem;
            border-bottom: 1px solid var(--border);
        }

        .modal-title {
            font-size: 1.1rem;
            font-weight: 600;
        }

        .modal-close {
            background: none;
            border: none;
            color: var(--text-secondary);
            font-size: 1.5rem;
            cursor: pointer;
            padding: 0.25rem 0.5rem;
            transition: var(--transition);
        }

        .modal-close:hover {
            color: var(--accent);
        }

        .modal-body {
            padding: 1.5rem;
        }

        /* Preview */
        .preview-content {
            background: var(--bg-primary);
            border-radius: 8px;
            padding: 1rem;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.85rem;
            overflow: auto;
            max-height: 60vh;
            white-space: pre-wrap;
            word-break: break-all;
        }

        .preview-image {
            max-width: 100%;
            max-height: 60vh;
            object-fit: contain;
            border-radius: 8px;
        }

        .preview-binary {
            text-align: center;
            padding: 3rem;
            color: var(--text-secondary);
        }

        /* New Folder Modal */
        .modal-input {
            width: 100%;
            padding: 0.75rem 1rem;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--bg-primary);
            color: var(--text-primary);
            font-size: 1rem;
            transition: var(--transition);
        }

        .modal-input:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(233, 69, 96, 0.2);
        }

        .modal-actions {
            display: flex;
            justify-content: flex-end;
            gap: 0.75rem;
            margin-top: 1.5rem;
        }

        /* Toast Notifications */
        .toast-container {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            z-index: 2000;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }

        .toast {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 1rem 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            box-shadow: var(--shadow);
            animation: slideIn 0.3s ease;
            min-width: 280px;
        }

        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        .toast.success {
            border-left: 4px solid var(--success);
        }

        .toast.error {
            border-left: 4px solid var(--error);
        }

        .toast.warning {
            border-left: 4px solid var(--warning);
        }

        .toast-icon {
            font-size: 1.25rem;
        }

        .toast-message {
            flex: 1;
            font-size: 0.9rem;
        }

        /* Auth Modal */
        .auth-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            z-index: 3000;
            justify-content: center;
            align-items: center;
        }

        .auth-modal.active {
            display: flex;
        }

        .auth-content {
            background: var(--bg-secondary);
            border-radius: var(--radius);
            padding: 2rem;
            width: 100%;
            max-width: 400px;
            box-shadow: var(--shadow);
        }

        .auth-title {
            font-size: 1.25rem;
            margin-bottom: 1.5rem;
            text-align: center;
        }

        .auth-form {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .auth-label {
            font-size: 0.9rem;
            color: var(--text-secondary);
            margin-bottom: 0.25rem;
        }

        .auth-submit {
            margin-top: 0.5rem;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .header {
                padding: 1rem;
            }
            
            .container {
                padding: 1rem;
            }
            
            .file-grid {
                grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
                gap: 0.75rem;
            }
            
            .file-card {
                padding: 1rem;
            }
            
            .upload-zone {
                padding: 2rem 1rem;
            }
            
            .toast-container {
                left: 1rem;
                right: 1rem;
                bottom: 1rem;
            }
            
            .toast {
                min-width: auto;
            }
        }

        /* Loading spinner */
        .spinner {
            display: inline-block;
            width: 1rem;
            height: 1rem;
            border: 2px solid var(--border);
            border-top-color: var(--accent);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Loading overlay */
        .loading-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            z-index: 2500;
            justify-content: center;
            align-items: center;
        }

        .loading-overlay.active {
            display: flex;
        }

        .loading-content {
            text-align: center;
        }

        .loading-spinner {
            font-size: 3rem;
            animation: spin 1s linear infinite;
        }

        .loading-text {
            margin-top: 1rem;
            color: var(--text-secondary);
        }
    </style>
</head>
<body>
    <!-- Auth Modal -->
    <div class="auth-modal" id="auth-modal">
        <div class="auth-content">
            <h2 class="auth-title">🔐 Enter Password</h2>
            <form class="auth-form" id="auth-form">
                <div>
                    <label class="auth-label">Password</label>
                    <input type="password" class="modal-input" id="auth-password" required>
                </div>
                <button type="submit" class="btn btn-primary auth-submit">Access</button>
            </form>
        </div>
    </div>

    <!-- Header -->
    <header class="header">
        <div class="logo">
            <span class="logo-icon">📡</span>
            <span class="logo-text">LNFS</span>
        </div>
        <div class="header-actions">
            <button class="btn btn-secondary" id="new-folder-btn" title="Create New Folder">
                📁 New Folder
            </button>
            <button class="btn btn-primary" id="upload-btn">
                ⬆️ Upload
            </button>
        </div>
    </header>

    <!-- Main Content -->
    <main class="container">
        <!-- Breadcrumb -->
        <nav class="breadcrumb" id="breadcrumb">
            <!-- Populated by JS -->
        </nav>

        <!-- Upload Zone -->
        <div class="upload-zone" id="upload-zone">
            <div class="upload-zone-icon">☁️</div>
            <div class="upload-zone-text">Drag & Drop files here or click to upload</div>
            <div class="upload-zone-hint">Supports multiple files • Max 16GB per file</div>
            <input type="file" id="file-input" multiple>
        </div>

        <!-- Progress Bar -->
        <div class="progress-container" id="progress-container">
            <div class="progress-header">
                <span class="progress-title" id="progress-title">Uploading...</span>
                <span class="progress-percent" id="progress-percent">0%</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" id="progress-fill"></div>
            </div>
            <div class="progress-status" id="progress-status"></div>
        </div>

        <!-- File Grid -->
        <div class="file-grid" id="file-grid">
            <!-- Populated by JS -->
        </div>

        <!-- Empty State -->
        <div class="empty-state" id="empty-state" style="display: none;">
            <div class="empty-state-icon">📂</div>
            <div class="empty-state-text">This folder is empty</div>
        </div>
    </main>

    <!-- Preview Modal -->
    <div class="modal" id="preview-modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3 class="modal-title" id="preview-title">File Preview</h3>
                <button class="modal-close" id="preview-close">×</button>
            </div>
            <div class="modal-body" id="preview-body">
                <!-- Content populated by JS -->
            </div>
        </div>
    </div>

    <!-- New Folder Modal -->
    <div class="modal" id="folder-modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3 class="modal-title">Create New Folder</h3>
                <button class="modal-close" id="folder-close">×</button>
            </div>
            <div class="modal-body">
                <form id="folder-form">
                    <input type="text" class="modal-input" id="folder-name" 
                           placeholder="Folder name" required>
                    <div class="modal-actions">
                        <button type="button" class="btn btn-secondary" id="folder-cancel">Cancel</button>
                        <button type="submit" class="btn btn-primary">Create</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <!-- Loading Overlay -->
    <div class="loading-overlay" id="loading-overlay">
        <div class="loading-content">
            <div class="loading-spinner">⏳</div>
            <div class="loading-text" id="loading-text">Preparing download...</div>
        </div>
    </div>

    <!-- Toast Container -->
    <div class="toast-container" id="toast-container"></div>

    <script>
        // State
        const state = {
            currentPath: '',
            isAuthenticated: {{ 'false' if not password_hash else 'true' }},
            authToken: null
        };

        // DOM Elements
        const elements = {
            breadcrumb: document.getElementById('breadcrumb'),
            fileGrid: document.getElementById('file-grid'),
            emptyState: document.getElementById('empty-state'),
            uploadZone: document.getElementById('upload-zone'),
            fileInput: document.getElementById('file-input'),
            uploadBtn: document.getElementById('upload-btn'),
            newFolderBtn: document.getElementById('new-folder-btn'),
            previewModal: document.getElementById('preview-modal'),
            previewTitle: document.getElementById('preview-title'),
            previewBody: document.getElementById('preview-body'),
            previewClose: document.getElementById('preview-close'),
            folderModal: document.getElementById('folder-modal'),
            folderForm: document.getElementById('folder-form'),
            folderName: document.getElementById('folder-name'),
            folderClose: document.getElementById('folder-close'),
            folderCancel: document.getElementById('folder-cancel'),
            progressContainer: document.getElementById('progress-container'),
            progressFill: document.getElementById('progress-fill'),
            progressPercent: document.getElementById('progress-percent'),
            progressTitle: document.getElementById('progress-title'),
            progressStatus: document.getElementById('progress-status'),
            toastContainer: document.getElementById('toast-container'),
            loadingOverlay: document.getElementById('loading-overlay'),
            loadingText: document.getElementById('loading-text'),
            authModal: document.getElementById('auth-modal'),
            authForm: document.getElementById('auth-form'),
            authPassword: document.getElementById('auth-password')
        };

        // Helper Functions
        function getAuthHeaders() {
            const headers = { 'X-Path': state.currentPath };
            if (state.authToken) {
                headers['Authorization'] = 'Bearer ' + state.authToken;
            }
            return headers;
        }

        function showToast(message, type = 'success') {
            const icons = {
                success: '✓',
                error: '✗',
                warning: '⚠'
            };
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.innerHTML = `
                <span class="toast-icon">${icons[type]}</span>
                <span class="toast-message">${message}</span>
            `;
            elements.toastContainer.appendChild(toast);
            setTimeout(() => {
                toast.style.animation = 'slideIn 0.3s ease reverse';
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        }

        function formatSize(size) {
            for (const unit of ['B', 'KB', 'MB', 'GB']) {
                if (size < 1024) return size.toFixed(1) + ' ' + unit;
                size /= 1024;
            }
            return size.toFixed(1) + ' TB';
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function showLoading(text = 'Loading...') {
            elements.loadingText.textContent = text;
            elements.loadingOverlay.classList.add('active');
        }

        function hideLoading() {
            elements.loadingOverlay.classList.remove('active');
        }

        // Render Functions
        function renderBreadcrumb() {
            const parts = state.currentPath ? state.currentPath.split('/').filter(Boolean) : [];
            let html = `<a href="#" class="breadcrumb-item" data-path="">🏠 Root</a>`;
            
            let currentPathAccum = '';
            parts.forEach((part, index) => {
                currentPathAccum += (index > 0 ? '/' : '') + part;
                html += `<span class="breadcrumb-separator">›</span>`;
                if (index === parts.length - 1) {
                    html += `<span class="breadcrumb-item breadcrumb-current">${escapeHtml(part)}</span>`;
                } else {
                    html += `<a href="#" class="breadcrumb-item" data-path="${escapeHtml(currentPathAccum)}">${escapeHtml(part)}</a>`;
                }
            });
            
            elements.breadcrumb.innerHTML = html;
            
            // Add click handlers
            elements.breadcrumb.querySelectorAll('.breadcrumb-item[data-path]').forEach(item => {
                item.addEventListener('click', (e) => {
                    e.preventDefault();
                    navigateTo(item.dataset.path);
                });
            });
        }

        function renderFileList(files) {
            if (files.length === 0) {
                elements.fileGrid.innerHTML = '';
                elements.emptyState.style.display = 'block';
                return;
            }
            
            elements.emptyState.style.display = 'none';
            elements.fileGrid.innerHTML = files.map(file => `
                <div class="file-card" data-path="${escapeHtml(file.path)}" data-type="${file.type}">
                    <span class="file-icon">${file.icon}</span>
                    <span class="file-name">${escapeHtml(file.name)}</span>
                    <span class="file-size">${file.type === 'dir' ? 'Folder' : formatSize(file.size)}</span>
                    <div class="file-actions">
                        ${file.type === 'dir' ? 
                            `<button class="file-action-btn download" data-action="open" title="Open">📂</button>` :
                            `<button class="file-action-btn download" data-action="download" title="Download">⬇️</button>`
                        }
                        <button class="file-action-btn delete" data-action="delete" title="Delete">🗑️</button>
                    </div>
                </div>
            `).join('');
            
            // Add click handlers
            elements.fileGrid.querySelectorAll('.file-card').forEach(card => {
                card.addEventListener('click', (e) => {
                    if (e.target.closest('.file-action-btn')) {
                        e.stopPropagation();
                        const action = e.target.closest('.file-action-btn').dataset.action;
                        handleFileAction(card.dataset.path, card.dataset.type, action);
                    } else {
                        handleFileClick(card.dataset.path, card.dataset.type);
                    }
                });
            });
        }

        // Navigation & Actions
        async function navigateTo(path) {
            state.currentPath = path;
            renderBreadcrumb();
            await loadFiles();
        }

        async function loadFiles() {
            try {
                const response = await fetch('/api/files?path=' + encodeURIComponent(state.currentPath), {
                    headers: getAuthHeaders()
                });
                
                if (response.status === 401) {
                    state.isAuthenticated = false;
                    elements.authModal.classList.add('active');
                    return;
                }
                
                if (!response.ok) throw new Error('Failed to load files');
                
                const data = await response.json();
                renderFileList(data.files);
            } catch (error) {
                showToast('Failed to load files: ' + error.message, 'error');
            }
        }

        function handleFileClick(path, type) {
            if (type === 'dir') {
                navigateTo(path);
            } else {
                previewFile(path);
            }
        }

        async function handleFileAction(path, type, action) {
            switch (action) {
                case 'open':
                    navigateTo(path);
                    break;
                case 'download':
                    downloadFile(path);
                    break;
                case 'delete':
                    if (confirm('Are you sure you want to delete this ' + (type === 'dir' ? 'folder' : 'file') + '?')) {
                        await deleteFile(path);
                    }
                    break;
            }
        }

        async function previewFile(path) {
            const filename = path.split('/').pop();
            elements.previewTitle.textContent = filename;
            elements.previewBody.innerHTML = '<div class="spinner"></div> Loading preview...';
            elements.previewModal.classList.add('active');
            
            try {
                const response = await fetch('/api/preview?path=' + encodeURIComponent(path), {
                    headers: getAuthHeaders()
                });
                
                if (response.status === 401) {
                    elements.previewModal.classList.remove('active');
                    state.isAuthenticated = false;
                    elements.authModal.classList.add('active');
                    return;
                }
                
                const data = await response.json();
                
                if (data.type === 'image') {
                    elements.previewBody.innerHTML = `<img src="${data.content}" class="preview-image" alt="${escapeHtml(filename)}">`;
                } else if (data.type === 'text') {
                    elements.previewBody.innerHTML = `<pre class="preview-content">${escapeHtml(data.content)}</pre>`;
                } else if (data.type === 'binary') {
                    elements.previewBody.innerHTML = `
                        <div class="preview-binary">
                            <div style="font-size: 3rem;">📄</div>
                            <p>Binary file - preview not available</p>
                            <button class="btn btn-primary" onclick="downloadFile('${escapeHtml(path)}')">Download to View</button>
                        </div>
                    `;
                } else {
                    elements.previewBody.innerHTML = `
                        <div class="preview-binary">
                            <div style="font-size: 3rem;">📄</div>
                            <p>File preview not available</p>
                        </div>
                    `;
                }
            } catch (error) {
                elements.previewBody.innerHTML = `<div class="preview-binary">Failed to load preview</div>`;
                showToast('Preview failed: ' + error.message, 'error');
            }
        }

        function downloadFile(path) {
            const filename = path.split('/').pop();
            window.location.href = '/api/download?path=' + encodeURIComponent(path) + '&token=' + (state.authToken || '');
        }

        async function deleteFile(path) {
            try {
                const response = await fetch('/api/delete', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...getAuthHeaders()
                    },
                    body: JSON.stringify({ path })
                });
                
                if (response.status === 401) {
                    state.isAuthenticated = false;
                    elements.authModal.classList.add('active');
                    return;
                }
                
                if (!response.ok) throw new Error('Failed to delete');
                
                showToast('Deleted successfully');
                await loadFiles();
            } catch (error) {
                showToast('Delete failed: ' + error.message, 'error');
            }
        }

        // Upload
        async function uploadFiles(files) {
            if (files.length === 0) return;
            
            elements.progressContainer.classList.add('active');
            
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                elements.progressTitle.textContent = `Uploading ${file.name} (${i + 1}/${files.length})`;
                
                try {
                    const formData = new FormData();
                    formData.append('file', file);
                    if (state.currentPath) {
                        formData.append('path', state.currentPath);
                    }
                    
                    const xhr = new XMLHttpRequest();
                    
                    await new Promise((resolve, reject) => {
                        xhr.upload.addEventListener('progress', (e) => {
                            if (e.lengthComputable) {
                                const percent = Math.round((e.loaded / e.total) * 100);
                                elements.progressFill.style.width = percent + '%';
                                elements.progressPercent.textContent = percent + '%';
                                elements.progressStatus.textContent = formatSize(e.loaded) + ' / ' + formatSize(e.total);
                            }
                        });
                        
                        xhr.addEventListener('load', () => {
                            if (xhr.status >= 200 && xhr.status < 300) {
                                showToast(`Uploaded ${file.name}`);
                                resolve();
                            } else {
                                reject(new Error(xhr.statusText));
                            }
                        });
                        
                        xhr.addEventListener('error', () => reject(new Error('Upload failed')));
                        
                        xhr.open('POST', '/api/upload');
                        if (state.authToken) {
                            xhr.setRequestHeader('Authorization', 'Bearer ' + state.authToken);
                        }
                        xhr.setRequestHeader('X-Path', state.currentPath);
                        xhr.send(formData);
                    });
                } catch (error) {
                    showToast(`Failed to upload ${file.name}: ${error.message}`, 'error');
                }
                
                elements.progressFill.style.width = '0%';
            }
            
            elements.progressContainer.classList.remove('active');
            await loadFiles();
        }

        // Event Listeners
        elements.uploadZone.addEventListener('click', () => elements.fileInput.click());
        
        elements.uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            elements.uploadZone.classList.add('dragover');
        });
        
        elements.uploadZone.addEventListener('dragleave', () => {
            elements.uploadZone.classList.remove('dragover');
        });
        
        elements.uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            elements.uploadZone.classList.remove('dragover');
            uploadFiles(e.dataTransfer.files);
        });
        
        elements.fileInput.addEventListener('change', () => {
            uploadFiles(elements.fileInput.files);
            elements.fileInput.value = '';
        });
        
        elements.uploadBtn.addEventListener('click', () => elements.fileInput.click());
        
        elements.newFolderBtn.addEventListener('click', () => {
            elements.folderName.value = '';
            elements.folderModal.classList.add('active');
            elements.folderName.focus();
        });
        
        elements.folderClose.addEventListener('click', () => {
            elements.folderModal.classList.remove('active');
        });
        
        elements.folderCancel.addEventListener('click', () => {
            elements.folderModal.classList.remove('active');
        });
        
        elements.folderForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = elements.folderName.value.trim();
            if (!name) return;
            
            try {
                const response = await fetch('/api/mkdir', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...getAuthHeaders()
                    },
                    body: JSON.stringify({ 
                        path: state.currentPath,
                        name 
                    })
                });
                
                if (response.status === 401) {
                    state.isAuthenticated = false;
                    elements.folderModal.classList.remove('active');
                    elements.authModal.classList.add('active');
                    return;
                }
                
                if (!response.ok) throw new Error('Failed to create folder');
                
                showToast('Folder created: ' + name);
                elements.folderModal.classList.remove('active');
                await loadFiles();
            } catch (error) {
                showToast('Failed to create folder: ' + error.message, 'error');
            }
        });
        
        elements.previewClose.addEventListener('click', () => {
            elements.previewModal.classList.remove('active');
        });
        
        elements.previewModal.addEventListener('click', (e) => {
            if (e.target === elements.previewModal) {
                elements.previewModal.classList.remove('active');
            }
        });
        
        elements.folderModal.addEventListener('click', (e) => {
            if (e.target === elements.folderModal) {
                elements.folderModal.classList.remove('active');
            }
        });
        
        // Auth
        elements.authForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const password = elements.authPassword.value;
            
            // Store token (in real app, this would be validated server-side)
            state.authToken = password;
            state.isAuthenticated = true;
            elements.authModal.classList.remove('active');
            elements.authPassword.value = '';
            
            await loadFiles();
        });
        
        // Close modals on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                elements.previewModal.classList.remove('active');
                elements.folderModal.classList.remove('active');
            }
        });
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            renderBreadcrumb();
            loadFiles();
        });
    </script>
</body>
</html>
"""


# ============================================================================
# API Routes
# ============================================================================


@app.route("/")
def index():
    """Serve the main page."""
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/files")
def list_files():
    """List files in a directory."""
    if not check_auth(request.headers.get("Authorization", "")):
        return jsonify({"error": "Unauthorized"}), 401

    path = request.args.get("path", "")
    target_dir = os.path.join(serve_dir, path) if path else serve_dir

    if not os.path.exists(target_dir):
        abort(404)

    if not os.path.isdir(target_dir):
        abort(400)

    # Security: prevent directory traversal
    real_target = os.path.realpath(target_dir)
    real_serve = os.path.realpath(serve_dir)
    if not real_target.startswith(real_serve):
        abort(403)

    files = []
    try:
        for entry in sorted(
            os.scandir(target_dir), key=lambda x: (not x.is_dir(), x.name.lower())
        ):
            try:
                size = entry.stat().st_size if entry.is_file() else 0
                files.append(
                    {
                        "name": entry.name,
                        "path": os.path.join(path, entry.name) if path else entry.name,
                        "type": "dir" if entry.is_dir() else "file",
                        "size": size,
                        "icon": get_file_icon(entry.name, entry.is_dir()),
                    }
                )
            except (OSError, PermissionError):
                continue
    except PermissionError:
        return jsonify({"error": "Permission denied"}), 403

    return jsonify({"files": files})


@app.route("/api/preview")
def preview_file():
    """Preview a file."""
    if not check_auth(request.headers.get("Authorization", "")):
        return jsonify({"error": "Unauthorized"}), 401

    path = request.args.get("path", "")
    file_path = os.path.join(serve_dir, path)

    if not os.path.exists(file_path):
        abort(404)

    if not os.path.isfile(file_path):
        abort(400)

    # Security check
    real_file = os.path.realpath(file_path)
    real_serve = os.path.realpath(serve_dir)
    if not real_file.startswith(real_serve):
        abort(403)

    ext = Path(file_path).suffix.lower()

    # Image preview
    if ext in IMAGE_EXTENSIONS:
        try:
            with open(file_path, "rb") as f:
                data = f.read()
            import base64

            mime = mimetypes.guess_type(file_path)[0] or "image/png"
            b64 = base64.b64encode(data).decode("utf-8")
            return jsonify({"type": "image", "content": f"data:{mime};base64,{b64}"})
        except Exception:
            return jsonify({"type": "binary"})

    # Text preview
    if ext in TEXT_EXTENSIONS:
        try:
            size = os.path.getsize(file_path)
            if size > MAX_FILE_PREVIEW_SIZE:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = (
                        f.read(MAX_FILE_PREVIEW_SIZE)
                        + f"\n\n... (truncated, {format_size(size)} total)"
                    )
            else:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            return jsonify({"type": "text", "content": content})
        except Exception:
            return jsonify({"type": "binary"})

    return jsonify({"type": "binary"})


@app.route("/api/download")
def download_file():
    """Download a file or folder (as zip)."""
    token = request.args.get("token", "")
    if not check_auth(f"Bearer {token}"):
        return jsonify({"error": "Unauthorized"}), 401

    path = request.args.get("path", "")
    file_path = os.path.join(serve_dir, path)

    if not os.path.exists(file_path):
        abort(404)

    # Security check
    real_file = os.path.realpath(file_path)
    real_serve = os.path.realpath(serve_dir)
    if not real_file.startswith(real_serve):
        abort(403)

    if os.path.isdir(file_path):
        # Create zip archive
        memory_file = io.BytesIO()
        folder_name = Path(path).name if path else "download"

        with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(file_path):
                for file in files:
                    file_full_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_full_path, serve_dir)
                    try:
                        zf.write(file_full_path, arcname)
                    except (OSError, PermissionError):
                        continue

        memory_file.seek(0)
        return send_file(
            memory_file,
            mimetype="application/zip",
            as_attachment=True,
            download_name=f"{folder_name}.zip",
        )
    else:
        return send_file(
            file_path, as_attachment=True, download_name=os.path.basename(file_path)
        )


@app.route("/api/upload", methods=["POST"])
def upload_file():
    """Upload files."""
    if not check_auth(request.headers.get("Authorization", "")):
        return jsonify({"error": "Unauthorized"}), 401

    target_dir = request.headers.get("X-Path", "")
    target_path = os.path.join(serve_dir, target_dir) if target_dir else serve_dir

    if not os.path.isdir(target_path):
        abort(400)

    # Security check
    real_target = os.path.realpath(target_path)
    real_serve = os.path.realpath(serve_dir)
    if not real_target.startswith(real_serve):
        abort(403)

    files = request.files.getlist("file")
    if not files:
        return jsonify({"error": "No files provided"}), 400

    uploaded = []
    for file in files:
        if file.filename:
            filename = secure_filename(file.filename)
            dest = os.path.join(target_path, filename)
            try:
                file.save(dest)
                uploaded.append(filename)
            except Exception as e:
                return jsonify({"error": f"Failed to save {filename}: {str(e)}"}), 500

    return jsonify({"success": True, "uploaded": uploaded})


@app.route("/api/mkdir", methods=["POST"])
def make_directory():
    """Create a new directory."""
    if not check_auth(request.headers.get("Authorization", "")):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    parent_path = data.get("path", "")
    name = data.get("name", "")

    if not name:
        return jsonify({"error": "Folder name required"}), 400

    parent_dir = os.path.join(serve_dir, parent_path) if parent_path else serve_dir

    if not os.path.isdir(parent_dir):
        return jsonify({"error": "Parent directory not found"}), 404

    # Security check
    real_parent = os.path.realpath(parent_dir)
    real_serve = os.path.realpath(serve_dir)
    if not real_parent.startswith(real_serve):
        abort(403)

    new_dir = os.path.join(parent_dir, secure_filename(name))

    try:
        os.makedirs(new_dir, exist_ok=False)
        return jsonify({"success": True})
    except FileExistsError:
        return jsonify({"error": "Folder already exists"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/delete", methods=["POST"])
def delete_path():
    """Delete a file or directory."""
    if not check_auth(request.headers.get("Authorization", "")):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    path = data.get("path", "")

    if not path:
        return jsonify({"error": "Path required"}), 400

    target_path = os.path.join(serve_dir, path)

    if not os.path.exists(target_path):
        return jsonify({"error": "Not found"}), 404

    # Security check
    real_target = os.path.realpath(target_path)
    real_serve = os.path.realpath(serve_dir)
    if not real_target.startswith(real_serve):
        abort(403)

    try:
        import shutil

        if os.path.isdir(target_path):
            shutil.rmtree(target_path)
        else:
            os.remove(target_path)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# QR Code Generation
# ============================================================================


def generate_qr_code(url):
    """Generate and return QR code as ASCII art."""
    if not QRCODE_AVAILABLE:
        return None

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=3,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)

    # Generate ASCII art
    qr_matrix = qr.get_matrix()
    blocks = []

    for row in qr_matrix:
        line = []
        for cell in row:
            line.append("██" if cell else "  ")
        blocks.append("".join(line))

    return "\n".join(blocks)


# ============================================================================
# Main Entry Point
# ============================================================================


def main():
    global serve_dir, password_hash

    parser = argparse.ArgumentParser(
        description="LNFS - Local Network File Sharing Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Serve current directory on port 8888
  %(prog)s --port 9000              # Serve on port 9000
  %(prog)s --password secret        # Require password "secret"
  %(prog)s /path/to/share           # Share specific directory
  %(prog)s -p 8080 -P mypass /data  # Port 8080, password, share /data
        """,
    )

    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to serve (default: current directory)",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port to listen on (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "-P", "--password", type=str, default=None, help="Set password protection"
    )

    args = parser.parse_args()

    # Resolve serve directory
    serve_dir = os.path.abspath(args.directory)

    if not os.path.isdir(serve_dir):
        print(f"Error: '{serve_dir}' is not a directory")
        sys.exit(1)

    # Set password if provided
    if args.password:
        password_hash = hash_password(args.password)
        print("🔐 Password protection enabled")

    # Get local IP
    local_ip = get_local_ip()

    # Print startup info
    print("\n" + "=" * 60)
    print(f"  📡 {APP_NAME} - Local Network File Sharing Server")
    print("=" * 60)
    print(f"\n  📂 Serving:    {serve_dir}")
    print(f"  🌐 Local URL:  http://localhost:{args.port}")
    print(f"  📱 Network:    http://{local_ip}:{args.port}")

    # Generate QR code
    if QRCODE_AVAILABLE:
        url = f"http://{local_ip}:{args.port}"
        qr_ascii = generate_qr_code(url)
        if qr_ascii:
            print(f"\n  📱 Scan to connect from mobile:")
            for line in qr_ascii.split("\n"):
                print(f"       {line}")

    print(f"\n  💡 Tip: Access from other devices on the same network")
    print(f"         Use the network URL above (not localhost)\n")
    print("=" * 60)
    print(f"\n  Press Ctrl+C to stop the server\n")

    # Run Flask
    app.run(host="0.0.0.0", port=args.port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
