"""Location data model for Weather TUI application."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Location:
    """
    Represents a geographic location.

    Attributes:
        name: The name of the location (city name)
        latitude: Geographic latitude coordinate
        longitude: Geographic longitude coordinate
        country: Optional country name
        admin1: Optional state or region name
        timezone: Timezone identifier (e.g., 'America/New_York')
    """

    name: str
    latitude: float
    longitude: float
    timezone: str
    country: Optional[str] = None
    admin1: Optional[str] = None
