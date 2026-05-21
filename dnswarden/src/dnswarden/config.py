"""Configuration loader."""

import os
import yaml
from pathlib import Path


class Config:
    """DNSWarden configuration."""

    DEFAULT_CONFIG_PATHS = [
        "/etc/dnswarden/config.yaml",
        "config/config.yaml",
        ".dnswarden.yaml",
    ]

    def __init__(self, config_path=None):
        self.config_path = config_path
        self.data = {}
        self._load()

    def _load(self):
        path = self.config_path
        if not path:
            for p in self.DEFAULT_CONFIG_PATHS:
                if Path(p).exists():
                    path = p
                    break

        if path:
            try:
                self.data = yaml.safe_load(Path(path).read_text()) or {}
            except Exception as e:
                print(f"Warning: Failed to load config from {path}: {e}")
                self.data = self._default_config()
        else:
            self.data = self._default_config()

    def _default_config(self):
        return {
            "server": {"bind_address": "0.0.0.0", "port": 53},
            "upstream": [
                {"host": "1.1.1.1", "port": 53},
                {"host": "8.8.8.8", "port": 53},
            ],
            "doh": {"enabled": False, "url": "https://cloudflare-dns.com/dns-query"},
            "blocklists": {"enabled": True, "sources": []},
            "zones": {"enabled": True},
            "logging": {
                "enabled": True,
                "backend": "sqlite",
                "path": "/var/lib/dnswarden/logs.db",
                "level": "info",
            },
            "security": {
                "rate_limit": {"enabled": True, "queries_per_second": 100, "burst": 200},
                "allowlist": {"enabled": False},
            },
            "admin": {"enabled": True, "bind_address": "127.0.0.1", "port": 8080},
        }

    def get(self, key, default=None):
        keys = key.split(".")
        val = self.data
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return default
            if val is None:
                return default
        return val

    def get_upstreams(self):
        upstreams = self.get("upstream", [])
        return [(u["host"], u.get("port", 53)) for u in upstreams]

    def get_blocklist_dir(self):
        return self.get("blocklists.dir", "/etc/dnswarden/blocklists")

    def get_log_path(self):
        return self.get("logging.path", "/var/lib/dnswarden/logs.db")
