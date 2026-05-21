"""Configuration management for AudioWave."""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional

from audiowave.utils.exceptions import ConfigFileError, InvalidOptionError
from audiowave.utils.logging import get_logger

logger = get_logger(__name__)

DEFAULT_CONFIG: Dict[str, Any] = {
    "visualization": {
        "default_width": 1920,
        "default_height": 400,
        "default_dpi": 100,
        "default_style": "classic",
    },
    "analysis": {
        "fft_size": 2048,
        "hop_size": 512,
        "window": "hann",
        "default_bars": 64,
        "default_db_range": 80,
    },
    "beat_detection": {
        "sensitivity": 1.0,
        "min_bpm": 60,
        "max_bpm": 200,
    },
    "colors": {
        "waveform": "#2196F3",
        "spectrum": "#4CAF50",
        "beats": "#FF5722",
    },
    "output": {
        "default_format": "png",
        "output_dir": "./audiowave_output",
    },
}

_global_config: Dict[str, Any] = {}


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from file or use defaults.

    Args:
        config_path: Optional path to config file (JSON)

    Returns:
        Configuration dictionary with all settings
    """
    global _global_config

    config = DEFAULT_CONFIG.copy()

    if config_path:
        config_file = Path(config_path)
        if not config_file.exists():
            raise ConfigFileError(f"Config file not found: {config_path}")

        try:
            with open(config_file, "r") as f:
                user_config = json.load(f)
            config = _merge_configs(config, user_config)
            logger.debug(f"Loaded config from {config_path}")
        except json.JSONDecodeError as e:
            raise ConfigFileError(f"Invalid JSON in config file: {e}")

    _global_config = config
    return config


def _merge_configs(default: Dict, user: Dict) -> Dict:
    """Recursively merge user config with defaults."""
    result = default.copy()
    for key, value in user.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_configs(result[key], value)
        else:
            result[key] = value
    return result


def get_config(key: Optional[str] = None) -> Any:
    """Get configuration value by key.

    Args:
        key: Dot-separated key path (e.g., "visualization.default_width")
              If None, returns entire config

    Returns:
        Configuration value or full config dict

    Raises:
        InvalidOptionError: If key is invalid
    """
    if not _global_config:
        load_config()

    if key is None:
        return _global_config.copy()

    keys = key.split(".")
    value = _global_config
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            raise InvalidOptionError(f"Invalid config key: {key}")

    return value


def set_config(key: str, value: Any) -> None:
    """Set configuration value.

    Args:
        key: Dot-separated key path
        value: Value to set
    """
    global _global_config

    if not _global_config:
        load_config()

    keys = key.split(".")
    target = _global_config
    for k in keys[:-1]:
        if k not in target:
            target[k] = {}
        target = target[k]
    target[keys[-1]] = value
