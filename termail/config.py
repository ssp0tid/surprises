"""Configuration for Termail email client."""

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class EmailConfig:
    """Email account configuration."""
    imap_server: str = "imap.example.com"
    imap_port: int = 993
    imap_use_ssl: bool = True
    smtp_server: str = "smtp.example.com"
    smtp_port: int = 587
    smtp_use_tls: bool = True
    username: str = ""
    password: str = ""
    email: str = ""
    name: str = ""


class Config:
    """Configuration manager."""
    
    def __init__(self, config_dir: str = None):
        if config_dir is None:
            config_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "config.json"
        self.config: EmailConfig = EmailConfig()
        self._load()
    
    def _load(self):
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.config = EmailConfig(**data)
            except (json.JSONDecodeError, TypeError):
                self.config = EmailConfig()
    
    def save(self):
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            json.dump(asdict(self.config), f, indent=2)
    
    def update(self, **kwargs):
        """Update configuration values."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.save()