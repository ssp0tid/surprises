"""Application configuration management."""

import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Optional


class Units(str, Enum):
    """Unit system for weather display."""

    METRIC = "metric"
    IMPERIAL = "imperial"


@dataclass
class Config:
    """Application configuration."""

    units: Units = Units.METRIC
    cache_ttl: int = 1800  # 30 minutes in seconds
    refresh_interval: int = 900  # 15 minutes in seconds
    default_location_name: Optional[str] = None
    default_latitude: Optional[float] = None
    default_longitude: Optional[float] = None
    last_location_name: Optional[str] = None
    last_latitude: Optional[float] = None
    last_longitude: Optional[float] = None

    # Config file path
    CONFIG_DIR: str = field(default="~/.config/weather_tui", repr=False)
    CONFIG_FILE: str = field(default="config.json", repr=False)

    @property
    def config_path(self) -> Path:
        """Get the path to the config file."""
        return Path(self.CONFIG_DIR).expanduser() / self.CONFIG_FILE

    @property
    def config_dir(self) -> Path:
        """Get the config directory path."""
        return Path(self.CONFIG_DIR).expanduser()

    def load(self) -> "Config":
        """Load configuration from file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, "r") as f:
                    data = json.load(f)

                self.units = Units(data.get("units", "metric"))
                self.cache_ttl = data.get("cache_ttl", 1800)
                self.refresh_interval = data.get("refresh_interval", 900)
                self.default_location_name = data.get("default_location_name")
                self.default_latitude = data.get("default_latitude")
                self.default_longitude = data.get("default_longitude")
                self.last_location_name = data.get("last_location_name")
                self.last_latitude = data.get("last_latitude")
                self.last_longitude = data.get("last_longitude")
        except (json.JSONDecodeError, IOError, ValueError) as e:
            # If loading fails, use defaults
            print(f"Warning: Failed to load config: {e}")

        return self

    def save(self) -> None:
        """Save configuration to file."""
        try:
            # Ensure config directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # Convert enum to string for JSON serialization
            data = {
                "units": self.units.value
                if isinstance(self.units, Units)
                else self.units,
                "cache_ttl": self.cache_ttl,
                "refresh_interval": self.refresh_interval,
                "default_location_name": self.default_location_name,
                "default_latitude": self.default_latitude,
                "default_longitude": self.default_longitude,
                "last_location_name": self.last_location_name,
                "last_latitude": self.last_latitude,
                "last_longitude": self.last_longitude,
            }

            with open(self.config_path, "w") as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Warning: Failed to save config: {e}")

    def toggle_units(self) -> None:
        """Toggle between metric and imperial units."""
        if self.units == Units.METRIC:
            self.units = Units.IMPERIAL
        else:
            self.units = Units.METRIC
        self.save()

    def set_last_location(self, name: str, latitude: float, longitude: float) -> None:
        """Set the last used location."""
        self.last_location_name = name
        self.last_latitude = latitude
        self.last_longitude = longitude
        self.save()

    def has_last_location(self) -> bool:
        """Check if there's a saved last location."""
        return (
            self.last_location_name is not None
            and self.last_latitude is not None
            and self.last_longitude is not None
        )

    def get_last_location(
        self,
    ) -> tuple[Optional[str], Optional[float], Optional[float]]:
        """Get the last used location."""
        return (self.last_location_name, self.last_latitude, self.last_longitude)


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global config instance."""
    global _config
    if _config is None:
        _config = Config().load()
    return _config


def reload_config() -> Config:
    """Reload configuration from file."""
    global _config
    _config = Config().load()
    return _config
