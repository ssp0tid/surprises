"""Storage service for persistence."""

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class Storage:
    """JSON persistence for settings and presets."""

    def __init__(self) -> None:
        self._storage_dir = self._get_storage_dir()
        self._settings_file = self._storage_dir / "settings.json"
        self._alarms_file = self._storage_dir / "alarms.json"
        self._presets_file = self._storage_dir / "presets.json"

    def _get_storage_dir(self) -> Path:
        """Get the storage directory path."""
        # Use XDG_CONFIG_HOME or ~/.config/termtimer
        config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        storage_dir = config_home / "termtimer"
        storage_dir.mkdir(parents=True, exist_ok=True)
        return storage_dir

    def _read_json(self, file_path: Path) -> dict | list | None:
        """Read JSON from file."""
        try:
            if file_path.exists():
                with open(file_path, "r") as f:
                    return json.load(f)
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in {file_path}: {e}")
        except Exception as e:
            logger.warning(f"Failed to read {file_path}: {e}")
        return None

    def _write_json(self, file_path: Path, data: Any) -> None:
        """Write JSON to file."""
        try:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to write {file_path}: {e}")

    # Settings methods
    def load_settings(self) -> dict:
        """Load application settings."""
        data = self._read_json(self._settings_file)
        return data if isinstance(data, dict) else {}

    def save_settings(self, settings: dict) -> None:
        """Save application settings."""
        self._write_json(self._settings_file, settings)

    # Alarm methods
    def load_alarms(self) -> list:
        """Load saved alarms."""
        data = self._read_json(self._alarms_file)
        return data if isinstance(data, list) else []

    def save_alarms(self, alarms: list) -> None:
        """Save alarms."""
        self._write_json(self._alarms_file, alarms)

    # Preset methods
    def load_presets(self) -> list:
        """Load timer presets."""
        data = self._read_json(self._presets_file)
        return data if isinstance(data, list) else []

    def save_presets(self, presets: list) -> None:
        """Save timer presets."""
        self._write_json(self._presets_file, presets)