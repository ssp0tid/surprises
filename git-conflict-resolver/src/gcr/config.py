"""Configuration management for GCR."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import tomlkit


@dataclass
class Config:
    """Application configuration."""

    backup_enabled: bool = True
    show_hints: bool = True
    auto_load_conflicts: bool = True
    theme: str = "dark"
    highlight_changes: bool = True
    config_path: Optional[Path] = None

    def __post_init__(self):
        if self.config_path is None:
            self.config_path = self._default_config_path()
        if self.config_path and self.config_path.exists():
            self.load()

    def _default_config_path(self) -> Optional[Path]:
        home = Path.home()
        gcr_dir = home / ".gcr"
        if gcr_dir.exists() or self._can_create_dir(gcr_dir):
            return gcr_dir / "config.toml"
        return None

    def _can_create_dir(self, path: Path) -> bool:
        parent = path.parent
        return parent.exists() and os.access(parent, os.W_OK)

    def load(self) -> None:
        if not self.config_path or not self.config_path.exists():
            return
        try:
            with open(self.config_path) as f:
                data = tomlkit.load(f)
            self.backup_enabled = data.get("backup_enabled", self.backup_enabled)
            self.show_hints = data.get("show_hints", self.show_hints)
            self.auto_load_conflicts = data.get("auto_load_conflicts", self.auto_load_conflicts)
            self.theme = data.get("theme", self.theme)
            self.highlight_changes = data.get("highlight_changes", self.highlight_changes)
        except Exception:
            pass

    def save(self) -> None:
        if not self.config_path:
            return
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w") as f:
                tomlkit.dump(
                    {
                        "backup_enabled": self.backup_enabled,
                        "show_hints": self.show_hints,
                        "auto_load_conflicts": self.auto_load_conflicts,
                        "theme": self.theme,
                        "highlight_changes": self.highlight_changes,
                    },
                    f,
                )
        except Exception:
            pass
