"""Gunicorn configuration for production deployment."""

import os
import yaml


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return {}


config = load_config()
app_config = config.get("app", {})

# Server socket
bind = f"{app_config.get('host', '0.0.0.0')}:{app_config.get('port', 5000)}"
backlog = 2048

# Worker processes
workers = int(os.environ.get("WEB_CONCURRENCY", 2))
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "git-activity-dash"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = os.environ.get("GUNICORN_KEYFILE", None)
certfile = os.environ.get("GUNICORN_CERTFILE", None)
