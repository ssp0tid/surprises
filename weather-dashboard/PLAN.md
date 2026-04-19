# Terminal ASCII Weather Dashboard - Implementation Plan

## Project Overview

**Project Name:** Weather TUI
**Type:** Interactive Terminal User Interface (TUI) Application
**Framework:** Python + Textual
**Data Source:** Open-Meteo API (free, no API key required)

### Core Features
1. Current weather conditions display
2. Hourly forecast (24-48 hours)
3. 7-day forecast
4. Moon phase display
5. Sunrise/sunset times
6. Precipitation chance
7. Wind speed and direction
8. Beautiful ASCII art with Unicode symbols and ANSI colors
9. Location search with geocoding
10. Automatic IP-based location detection
11. Units toggle (metric/imperial)
12. Manual refresh
13. Offline mode with error handling
14. Response caching

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        WeatherApp (App)                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Header     │  │  LocationBar │  │   Footer     │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
├─────────────────────────────────────────────────────────────────┤
│                        MainScreen                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    WeatherDashboard                     │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │    │
│  │  │ CurrentPanel│  │ HourlyPanel │  │  DailyPanel │      │    │
│  │  │             │  │             │  │             │      │    │
│  │  │  ASCII Art  │  │  Forecast   │  │  7-Day      │      │    │
│  │  │  Temp/Hum   │  │  Table      │  │  Table      │      │    │
│  │  │  Wind/Precip│  │             │  │             │      │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │    │
│  │  ┌─────────────┐  ┌─────────────┐                       │    │
│  │  │  AstroPanel │  │ UnitsToggle  │                       │    │
│  │  │  Sun/Moon   │  │ RefreshBtn  │                       │    │
│  │  └─────────────┘  └─────────────┘                       │    │
│  └─────────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│                       SearchScreen                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  SearchInput                                             │    │
│  │  ┌─────────────────────────────────────────────────┐   │    │
│  │  │  LocationResultList                              │   │    │
│  │  │  > Berlin, Germany                               │   │    │
│  │  │    Tokyo, Japan                                 │   │    │
│  │  │    Toronto, Canada                               │   │    │
│  │  └─────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Module Structure

```
weather_tui/
├── main.py                    # Entry point
├── __init__.py
├── app.py                    # Main App class
├── config.py                 # Configuration management
├── api/
│   ├── __init__.py
│   ├── client.py             # Open-Meteo API client
│   ├── geocoding.py          # Location search
│   └── ip_location.py        # IP-based location detection
├── models/
│   ├── __init__.py
│   ├── weather.py            # Weather data models
│   └── location.py           # Location model
├── services/
│   ├── __init__.py
│   ├── weather_service.py    # Weather data fetching
│   └── cache_service.py      # Caching layer
├── screens/
│   ├── __init__.py
│   ├── dashboard_screen.py   # Main weather display
│   └── search_screen.py      # Location search
├── widgets/
│   ├── __init__.py
│   ├── ascii_weather.py      # ASCII art weather icons
│   ├── current_weather.py    # Current conditions widget
│   ├── hourly_forecast.py    # Hourly forecast widget
│   ├── daily_forecast.py     # 7-day forecast widget
│   ├── astro_panel.py        # Sun/moon display
│   ├── moon_phase.py          # Moon phase calculator
│   ├── wind_compass.py       # Wind direction display
│   ├── temperature_gauge.py   # Temperature visualization
│   └── search_input.py        # Location search input
├── utils/
│   ├── __init__.py
│   ├── units.py              # Unit conversion
│   ├── colors.py             # ANSI color utilities
│   └── formatters.py         # Data formatting
└── styles/
    └── theme.css             # Textual CSS styles
```

---

## Open-Meteo API Integration

### API Endpoints

#### 1. Weather Forecast API
```
Base URL: https://api.open-meteo.com/v1/forecast
```

**Required Parameters:**
- `latitude` - Location latitude (float)
- `longitude` - Location longitude (float)
- `timezone` - Timezone (string, e.g., "auto" for local)

**Variables to Fetch:**

| Category | Variables | Purpose |
|----------|-----------|---------|
| Current | `temperature_2m`, `relative_humidity_2m`, `apparent_temperature`, `precipitation`, `weather_code`, `cloud_cover`, `wind_speed_10m`, `wind_direction_10m`, `is_day` | Current conditions |
| Hourly | `temperature_2m`, `relative_humidity_2m`, `precipitation_probability`, `precipitation`, `weather_code`, `wind_speed_10m`, `wind_direction_10m` | Hourly forecast |
| Daily | `weather_code`, `temperature_2m_max`, `temperature_2m_min`, `sunrise`, `sunset`, `precipitation_sum`, `precipitation_probability_max`, `wind_speed_10m_max`, `wind_direction_10m_dominant` | 7-day forecast |

#### 2. Geocoding API
```
Base URL: https://geocoding-api.open-meteo.com/v1/search
```

**Required Parameters:**
- `name` - Search query (string, min 2 chars for fuzzy matching)

**Optional Parameters:**
- `count` - Number of results (default: 10, max: 100)
- `language` - Response language (default: "en")

#### 3. IP-Based Location (External)
```
Service: http://ip-api.com/json/ (free, no key required)
Alternative: https://ipapi.co/json/
```

---

## Data Models

### WeatherData
```python
@dataclass
class WeatherData:
    location: Location
    current: CurrentWeather
    hourly: List[HourlyForecast]
    daily: List[DailyForecast]
    timezone: str
    last_updated: datetime
```

### CurrentWeather
```python
@dataclass
class CurrentWeather:
    temperature: float
    feels_like: float
    humidity: int
    precipitation: float
    weather_code: int
    cloud_cover: int
    wind_speed: float
    wind_direction: int
    is_day: bool
```

### DailyForecast
```python
@dataclass
class DailyForecast:
    date: date
    weather_code: int
    temp_max: float
    temp_min: float
    sunrise: datetime
    sunset: datetime
    precipitation_sum: float
    precipitation_probability: int
    wind_speed_max: float
    wind_direction: int
```

---

## UI Design System

### Color Palette (ANSI)

| Element | Metric | Imperial | Hex |
|---------|--------|----------|-----|
| Temperature Hot | Red (#FF6B6B) | Red | `\033[38;5;203m` |
| Temperature Warm | Orange (#FFA94D) | Orange | `\033[38;5;215m` |
| Temperature Mild | Yellow (#FFE066) | Yellow | `\033[38;5;226m` |
| Temperature Cool | Cyan (#66D9E8) | Light Blue | `\033[38;5;109m` |
| Temperature Cold | Blue (#339AF0) | Blue | `\033[38;5;75m` |
| Temperature Freeze | Purple (#9775FA) | Purple | `\033[38;5;141m` |
| Rain | Blue (#339AF0) | Blue | `\033[38;5;75m` |
| Snow | White (#FFFFFF) | White | `\033[38;5;15m` |
| Clouds | Gray (#ADB5BD) | Gray | `\033[38;5;145m` |
| Sun | Yellow (#FFD43B) | Yellow | `\033[38;5;227m` |
| Moon | Light Cyan (#99E9F2) | Light Cyan | `\033[38;5;117m` |
| Wind | Green (#51CF66) | Green | `\033[38;5;82m` |
| Error | Red (#FF6B6B) | Red | `\033[38;5;203m` |
| Info | Cyan (#22B8CF) | Cyan | `\033[38;5;44m` |

### Unicode Weather Symbols

```python
WEATHER_SYMBOLS = {
    0: "☀️",   # Clear sky
    1: "🌤️",  # Mainly clear
    2: "⛅",   # Partly cloudy
    3: "☁️",   # Overcast
    45: "🌫️", # Fog
    48: "🌫️", # Depositing rime fog
    51: "🌧️", # Light drizzle
    53: "🌧️", # Moderate drizzle
    55: "🌧️", # Dense drizzle
    56: "🌧️", # Light freezing drizzle
    57: "🌧️", # Dense freezing drizzle
    61: "🌧️", # Slight rain
    63: "🌧️", # Moderate rain
    65: "🌧️", # Heavy rain
    66: "🌧️", # Light freezing rain
    67: "🌧️", # Heavy freezing rain
    71: "🌨️", # Slight snow
    73: "🌨️", # Moderate snow
    75: "❄️",  # Heavy snow
    77: "🌨️", # Snow grains
    80: "🌦️", # Slight rain showers
    81: "🌦️", # Moderate rain showers
    82: "⛈️",  # Violent rain showers
    85: "🌨️", # Slight snow showers
    86: "🌨️", # Heavy snow showers
    95: "⛈️",  # Thunderstorm
    96: "⛈️",  # Thunderstorm with slight hail
    99: "⛈️",  # Thunderstorm with heavy hail
}
```

### ASCII Art Weather Icons

```python
CLEAR_SKY = """
    \\   |   /
      .---.
   -- (   ) --
      '---'
    /   |   \\
"""

SUNNY = """
     \\  o  /
    o .---. o
      |   |
     / .---. \\
    o  | |  o
     /  |  \\
"""

CLOUDY = """
      .--.
   .-(    ).
  (___.__)__)
     |  |
   __|  |__
  (        )
"""

RAINY = """
      .--.
   .-(    ).
  (___.__)__)
  ' ' ' ' '
  ' ' ' ' '
  ~~~~~~~~~~~
"""

SNOWY = """
      .--.
   .-(    ).
  (___.__)__)
   *  *  *
  *  *  *  *
   *  *  *
"""

THUNDERSTORM = """
      .--.
   .-(    ).
  (___.__)__)
    ⚡ || ⚡
    ||  ||
  ~~~~~~~~~~~
"""

NIGHT = """
      *   *
    *   .-.   *
   (    -   )
    *       *
      *   *
"""
```

### Box Drawing Characters

```python
BOX_HORIZONTAL = "─"
BOX_VERTICAL = "│"
BOX_CORNER_TOP_LEFT = "┌"
BOX_CORNER_TOP_RIGHT = "┐"
BOX_CORNER_BOTTOM_LEFT = "└"
BOX_CORNER_BOTTOM_RIGHT = "┘"
BOX_T_RIGHT = "┤"
BOX_T_LEFT = "├"
BOX_T_DOWN = "┬"
BOX_T_UP = "┴"
BOX_CROSS = "┼"
```

---

## Implementation Phases

### Phase 1: Project Setup
**Duration:** 1-2 hours

1. Create project structure
2. Set up virtual environment
3. Install dependencies:
   ```bash
   pip install textual httpx cachetools
   ```
4. Create configuration module
5. Set up logging

### Phase 2: API Client
**Duration:** 2-3 hours

1. Implement `APIClient` class
2. Implement `GeocodingClient` class
3. Implement `IPLocationClient` class
4. Add request error handling
5. Add response validation

### Phase 3: Data Layer
**Duration:** 2-3 hours

1. Create Pydantic/dataclass models
2. Implement `WeatherService` for business logic
3. Implement `CacheService` with TTL
4. Add unit conversion utilities

### Phase 4: UI Widgets
**Duration:** 4-6 hours

1. Create `ASCIIWeather` widget (weather icons)
2. Create `CurrentWeather` widget
3. Create `HourlyForecast` widget
4. Create `DailyForecast` widget
5. Create `AstroPanel` widget (sun/moon)
6. Create `MoonPhase` widget with calculation
7. Create `WindCompass` widget
8. Create `SearchInput` widget

### Phase 5: Screens
**Duration:** 2-3 hours

1. Implement `DashboardScreen`
2. Implement `SearchScreen`
3. Add screen transitions
4. Add keyboard navigation

### Phase 6: App Integration
**Duration:** 2-3 hours

1. Wire up screens in main App
2. Add header with title and controls
3. Add footer with keyboard hints
4. Implement refresh functionality
5. Add units toggle

### Phase 7: Styling
**Duration:** 1-2 hours

1. Create CSS theme file
2. Define color variables
3. Layout styling
4. Responsive adjustments

### Phase 8: Error Handling & Offline Mode
**Duration:** 2-3 hours

1. Implement connection checking
2. Show offline indicator
3. Display cached data when offline
4. Add retry logic
5. User-friendly error messages

### Phase 9: Testing & Polish
**Duration:** 2-3 hours

1. Test all features manually
2. Test error scenarios
3. Test offline mode
4. Test location search
5. Test units toggle
6. Test refresh

---

## Detailed Implementation Tasks

### Task 1: Configuration Module (`config.py`)

```python
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json

class Units(str, Enum):
    METRIC = "metric"
    IMPERIAL = "imperial"

@dataclass
class Config:
    units: Units = Units.METRIC
    cache_ttl: int = 1800  # 30 minutes
    refresh_interval: int = 900  # 15 minutes
    default_location: tuple[float, float] | None = None
    
    @classmethod
    def load(cls) -> "Config":
        # Load from ~/.config/weather_tui/config.json
        pass
    
    def save(self):
        # Save to ~/.config/weather_tui/config.json
        pass
```

### Task 2: API Client (`api/client.py`)

```python
import httpx
from typing import List, Optional
from models.weather import WeatherData, CurrentWeather, HourlyForecast, DailyForecast

class WeatherAPIClient:
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_weather(
        self,
        latitude: float,
        longitude: float,
        timezone: str = "auto"
    ) -> dict:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
            "current": [
                "temperature_2m", "relative_humidity_2m", "apparent_temperature",
                "precipitation", "weather_code", "cloud_cover",
                "wind_speed_10m", "wind_direction_10m", "is_day"
            ],
            "hourly": [
                "temperature_2m", "relative_humidity_2m",
                "precipitation_probability", "precipitation",
                "weather_code", "wind_speed_10m", "wind_direction_10m"
            ],
            "daily": [
                "weather_code", "temperature_2m_max", "temperature_2m_min",
                "sunrise", "sunset", "precipitation_sum",
                "precipitation_probability_max", "wind_speed_10m_max",
                "wind_direction_10m_dominant"
            ],
            "forecast_days": 7
        }
        
        response = await self.client.get(self.BASE_URL, params=params)
        response.raise_for_status()
        return response.json()
```

### Task 3: Geocoding Client (`api/geocoding.py`)

```python
class GeocodingClient:
    BASE_URL = "https://geocoding-api.open-meteo.com/v1/search"
    
    async def search(
        self,
        query: str,
        count: int = 10
    ) -> List[dict]:
        params = {
            "name": query,
            "count": count,
            "language": "en",
            "format": "json"
        }
        
        response = await self.client.get(self.BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
```

### Task 4: Moon Phase Calculator (`widgets/moon_phase.py`)

```python
from datetime import datetime
from math import sin, pi

def calculate_moon_phase(date: datetime) -> tuple[str, float]:
    """
    Calculate moon phase for a given date.
    Returns (phase_name, illumination_percentage)
    """
    # Known new moon: January 6, 2000
    known_new_moon = datetime(2000, 1, 6, 18, 14)
    lunation = 29.53058867  # Average lunar cycle in days
    
    days_since_new = (date - known_new_moon).total_seconds() / 86400
    lunar_cycle = (days_since_new % lunation) / lunation
    
    illumination = (1 - cos(lunar_cycle * 2 * pi)) / 2 * 100
    
    if lunar_cycle < 0.026:  # New Moon
        name = "🌑 New Moon"
    elif lunar_cycle < 0.223:  # Waxing Crescent
        name = "🌒 Waxing Crescent"
    elif lunar_cycle < 0.476:  # First Quarter
        name = "🌓 First Quarter"
    elif lunar_cycle < 0.726:  # Waxing Gibbous
        name = "🌔 Waxing Gibbous"
    elif lunar_cycle < 0.976:  # Full Moon
        name = "🌕 Full Moon"
    else:  # Waning Gibbous / Last Quarter / Waning Crescent
        name = "🌖 Waning Gibbous"
    
    return name, illumination

def get_moon_ascii(phase: float) -> str:
    """Generate ASCII moon based on illumination (0-100)."""
    if phase < 12.5:
        return "🌑"  # New Moon
    elif phase < 37.5:
        return "🌒"  # Waxing Crescent
    elif phase < 62.5:
        return "🌓"  # First Quarter
    elif phase < 87.5:
        return "🌔"  # Waxing Gibbous
    else:
        return "🌕"  # Full Moon
```

### Task 5: Wind Compass (`widgets/wind_compass.py`)

```python
def get_wind_direction_name(degrees: int) -> str:
    """Convert degrees to compass direction."""
    directions = [
        "N", "NNE", "NE", "ENE",
        "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW",
        "W", "WNW", "NW", "NNW"
    ]
    index = round(degrees / 22.5) % 16
    return directions[index]

def get_wind_arrow(degrees: int) -> str:
    """Get arrow character pointing in wind direction."""
    arrows = [
        "↓", "↙", "↙", "←",
        "←", "↔", "↗", "↗",
        "↑", "↗", "↗", "→",
        "→", "↘", "↘", "↓"
    ]
    index = round(degrees / 22.5) % 16
    return arrows[index]
```

### Task 6: Current Weather Widget (`widgets/current_weather.py`)

```python
from textual.widgets import Static
from textual.reactive import reactive

class CurrentWeatherWidget(Static):
    temperature = reactive(0.0)
    feels_like = reactive(0.0)
    humidity = reactive(0)
    wind_speed = reactive(0.0)
    wind_direction = reactive(0)
    weather_code = reactive(0)
    is_day = reactive(True)
    
    def render(self) -> str:
        weather_icon = WEATHER_SYMBOLS.get(self.weather_code, "❓")
        wind_dir = get_wind_direction_name(self.wind_direction)
        wind_arrow = get_wind_arrow(self.wind_direction)
        
        return f"""
╔══════════════════════════════════════╗
║           CURRENT WEATHER            ║
╠══════════════════════════════════════╣
║                                      ║
║            {weather_icon:^12}             ║
║                                      ║
║      🌡️ {self.temperature:>6.1f}°               ║
║      Feels like: {self.feels_like:>5.1f}°        ║
║                                      ║
║      💧 Humidity:    {self.humidity:>3}%          ║
║      💨 Wind:  {wind_arrow} {self.wind_speed:>5.1f} {self.wind_unit:<4}       ║
║              ({wind_dir:>4})                  ║
║                                      ║
╚══════════════════════════════════════╝
"""
```

### Task 7: Dashboard Screen (`screens/dashboard_screen.py`)

```python
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import LoadingIndicator
from textual.containers import VerticalScroll

class DashboardScreen(Screen):
    CSS = """
    DashboardScreen {
        layout: vertical;
    }
    
    # main-container {
        width: 100%;
        height: 100%;
        padding: 1;
    }
    
    .weather-panel {
        border: solid $primary;
        padding: 1 2;
        margin: 1 0;
        min-height: 1;
    }
    
    # current-panel {
        border-title: "Current Conditions";
    }
    
    # hourly-panel {
        border-title: "Hourly Forecast";
    }
    
    # daily-panel {
        border-title: "7-Day Forecast";
    }
    
    # astro-panel {
        border-title: "Sun & Moon";
    }
    """
    
    def compose(self) -> ComposeResult:
        with VerticalScroll(id="main-container"):
            yield CurrentWeatherWidget(id="current-panel", classes="weather-panel")
            yield HourlyForecastWidget(id="hourly-panel", classes="weather-panel")
            yield DailyForecastWidget(id="daily-panel", classes="weather-panel")
            yield AstroPanel(id="astro-panel", classes="weather-panel")
```

### Task 8: Search Screen (`screens/search_screen.py`)

```python
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Input, OptionList
from textual.events import Key

class SearchScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Input(placeholder="Search for a city...", id="search-input")
        yield OptionList(id="results-list")
    
    async def on_input_changed(self, event: Input.Changed) -> None:
        query = event.value
        if len(query) >= 2:
            results = await self.app.geocoding_client.search(query)
            self.query_one("#results-list").clear_options()
            for result in results:
                self.query_one("#results-list").add_option(
                    f"{result['name']}, {result.get('country', '')}"
                )
    
    async def on_option_list_option_selected(self, event) -> None:
        # Get selected location and navigate back
        pass
```

### Task 9: Main App (`app.py`)

```python
from textual.app import App, ComposeResult
from textual import work
from screens.dashboard_screen import DashboardScreen
from screens.search_screen import SearchScreen
from services.weather_service import WeatherService
from api.client import WeatherAPIClient
from api.geocoding import GeocodingClient
from api.ip_location import IPLocationClient

class WeatherApp(App):
    CSS_PATH = "styles/theme.css"
    
    def __init__(self):
        super().__init__()
        self.weather_client = WeatherAPIClient()
        self.geocoding_client = GeocodingClient()
        self.ip_client = IPLocationClient()
        self.weather_service = WeatherService(
            self.weather_client,
            self.geocoding_client
        )
        self.current_location = None
    
    async def on_mount(self) -> None:
        # Try to detect location via IP
        try:
            location = await self.ip_client.get_location()
            self.current_location = location
            await self.load_weather()
        except Exception:
            # Show search screen for manual location
            self.push_screen(SearchScreen())
    
    @work(exclusive=True)
    async def load_weather(self) -> None:
        if not self.current_location:
            return
        
        weather_data = await self.weather_service.get_weather(
            self.current_location.latitude,
            self.current_location.longitude
        )
        # Update widgets with new data
        self.query_one("#current-panel").update(weather_data.current)
        # ... update other panels
    
    def key_r(self) -> None:
        """Refresh weather data."""
        self.load_weather()
    
    def key_u(self) -> None:
        """Toggle units."""
        self.weather_service.toggle_units()
        self.load_weather()
    
    def key_s(self) -> None:
        """Open search screen."""
        self.push_screen(SearchScreen())
```

---

## Error Handling Strategy

### Network Errors
```python
try:
    data = await self.client.get(url)
except httpx.ConnectError:
    # Show offline indicator
    # Load from cache
    # Display: "📡 Offline - Showing cached data"
except httpx.TimeoutException:
    # Show timeout message
    # Display: "⏱️ Request timed out - Retrying..."
except httpx.HTTPStatusError as e:
    # Log error
    # Display user-friendly message
```

### Cache Strategy
```python
from cachetools import TTLCache
from datetime import datetime

cache = TTLCache(maxsize=100, ttl=1800)  # 30 min TTL

def get_cached_or_fetch(key: str, fetch_func):
    if key in cache:
        return cache[key]
    
    try:
        data = await fetch_func()
        cache[key] = (data, datetime.now())
        return data
    except Exception as e:
        if key in cache:
            # Return stale data with warning
            cached_data, cached_time = cache[key]
            return cached_data, "stale"
        raise
```

---

## Dependencies

```txt
# requirements.txt

textual>=0.50.0
httpx>=0.26.0
cachetools>=5.3.0
pydantic>=2.0.0
```

---

## File Structure (Final)

```
weather_tui/
├── main.py
├── requirements.txt
├── README.md
├── config/
│   └── settings.json
├── src/
│   ├── __init__.py
│   ├── app.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── geocoding.py
│   │   └── ip_location.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── weather.py
│   │   └── location.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── weather_service.py
│   │   └── cache_service.py
│   ├── screens/
│   │   ├── __init__.py
│   │   ├── dashboard_screen.py
│   │   └── search_screen.py
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── ascii_weather.py
│   │   ├── current_weather.py
│   │   ├── hourly_forecast.py
│   │   ├── daily_forecast.py
│   │   ├── astro_panel.py
│   │   ├── moon_phase.py
│   │   ├── wind_compass.py
│   │   └── search_input.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── units.py
│   │   ├── colors.py
│   │   └── formatters.py
│   └── styles/
│       └── theme.css
└── tests/
    ├── __init__.py
    ├── test_api.py
    ├── test_services.py
    └── test_widgets.py
```

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `r` | Refresh weather data |
| `u` | Toggle metric/imperial units |
| `s` | Open location search |
| `Esc` | Close search/go back |
| `q` / `Ctrl+C` | Quit application |
| `?` | Show help |

---

## WMO Weather Codes Reference

| Code | Description |
|------|-------------|
| 0 | Clear sky |
| 1, 2, 3 | Mainly clear, partly cloudy, overcast |
| 45, 48 | Fog and depositing rime fog |
| 51, 53, 55 | Light, moderate, dense drizzle |
| 56, 57 | Light and dense freezing drizzle |
| 61, 63, 65 | Slight, moderate, heavy rain |
| 66, 67 | Light and heavy freezing rain |
| 71, 73, 75 | Slight, moderate, heavy snowfall |
| 77 | Snow grains |
| 80, 81, 82 | Slight, moderate, violent rain showers |
| 85, 86 | Slight and heavy snow showers |
| 95 | Thunderstorm |
| 96, 99 | Thunderstorm with slight and heavy hail |

---

## Testing Checklist

- [ ] Current weather displays correctly
- [ ] Hourly forecast shows correct number of hours
- [ ] Daily forecast shows 7 days
- [ ] Moon phase calculation is accurate
- [ ] Sunrise/sunset times are correct for location
- [ ] Wind direction arrow points correctly
- [ ] Units toggle changes all displayed values
- [ ] Location search returns relevant results
- [ ] Refresh updates all data
- [ ] Offline mode shows cached data
- [ ] Error messages are user-friendly
- [ ] Keyboard shortcuts work
- [ ] App exits cleanly with `q` or `Ctrl+C`

---

## Estimated Total Development Time

| Phase | Time |
|-------|------|
| Project Setup | 1-2 hours |
| API Client | 2-3 hours |
| Data Layer | 2-3 hours |
| UI Widgets | 4-6 hours |
| Screens | 2-3 hours |
| App Integration | 2-3 hours |
| Styling | 1-2 hours |
| Error Handling | 2-3 hours |
| Testing & Polish | 2-3 hours |
| **Total** | **18-28 hours** |

---

## Future Enhancements (Out of Scope)

1. Multiple location support with tab navigation
2. Weather alerts and warnings
3. Historical weather data
4. Air quality index (AQI)
5. Customizable widget layouts
6. Save favorite locations
7. Animated weather effects (rain, snow)
8. Sound effects for weather conditions
9. Export data to JSON/CSV
10. Graphical charts for temperature trends

---

## Appendix: Research Findings Summary

### A. Open-Meteo API Complete Parameters

#### Moon Phase Data (from API, not calculated)
```python
DAILY_PARAMS = [
    "weather_code", "temperature_2m_max", "temperature_2m_min",
    "apparent_temperature_max", "apparent_temperature_min",
    "sunrise", "sunset",  # ISO 8601 format
    "daylight_duration",  # seconds
    "sunshine_duration",  # seconds
    "precipitation_sum", "precipitation_probability_max",
    "wind_speed_10m_max", "wind_direction_10m_dominant",
    "uv_index_max",
    "moon_phase",  # 0.0 to 1.0 (New=0/1, Full=0.5)
    "moonrise",  # ISO 8601
    "moonset",  # ISO 8601
]
```

#### Moon Phase Mapping (from API value)
```python
def moon_phase_name(phase: float) -> str:
    """Convert 0.0-1.0 to moon phase name."""
    if phase < 0.0625 or phase >= 0.9375:
        return "🌑 New Moon"
    elif phase < 0.1875:
        return "🌒 Waxing Crescent"
    elif phase < 0.3125:
        return "🌓 First Quarter"
    elif phase < 0.4375:
        return "🌔 Waxing Gibbous"
    elif phase < 0.5625:
        return "🌕 Full Moon"
    elif phase < 0.6875:
        return "🌖 Waning Gibbous"
    elif phase < 0.8125:
        return "🌗 Last Quarter"
    else:
        return "🌘 Waning Crescent"
```

### B. Textual Framework Patterns

#### Reactive Widget Pattern
```python
from textual.reactive import reactive
from textual.widget import Widget

class CurrentConditions(Widget):
    temperature = reactive[float](0.0)
    weather_code = reactive[int](0)
    
    def watch_temperature(self, temp: float) -> None:
        """Called automatically when temperature changes."""
        self.query_one("#temp").update(f"{temp:.1f}°C")
```

#### Async Data Loading with @work
```python
from textual import work

@work(exclusive=True)  # Cancels previous request if new one starts
async def fetch_weather(self) -> None:
    try:
        data = await self.client.get_weather(lat, lon)
        self.weather_data = data
        self.notify("Weather updated", severity="information")
    except Exception as e:
        self.notify(f"Error: {e}", severity="error")
```

#### Key Bindings Pattern
```python
BINDINGS = [
    ("q", "quit", "Quit"),
    ("r", "refresh", "Refresh"),
    ("f", "push_screen('search')", "Find"),
    ("u", "toggle_units", "Units"),
]
```

### C. Complete CSS Theme

```css
/* styles/theme.css */

Screen {
    background: $surface;
}

#header {
    dock: top;
    height: 3;
    background: $primary;
    color: $text;
}

.weather-panel {
    width: 100%;
    border: solid $primary;
    padding: 1 2;
    margin: 1 0;
}

.current-icon {
    width: auto;
    height: auto;
    text-style: bold;
    color: $accent;
}

.temp-display {
    text-style: bold;
    color: $warning;
}

.temp-low {
    color: $primary;
}

.forecast-row {
    height: auto;
    padding: 0 1;
}

.forecast-row:hover {
    background: $primary-muted;
}

.wind-display {
    color: $success;
}

.humidity-display {
    color: $info;
}

/* Loading spinner states */
.loading {
    text-style: italic;
    color: $text-muted;
}

.error {
    color: $error;
    text-style: bold;
}
```

### D. Cache TTL Recommendations

| Data Type | TTL | Reason |
|-----------|-----|--------|
| Current weather | 15-30 min | Updates every 15 min |
| Hourly forecast | 1-2 hours | Model updates 1-6x daily |
| Daily forecast | 4-6 hours | Low frequency changes |
| Geocoding | 24+ hours | Coordinates don't change |
| IP location | 24 hours | User may move, but not often |

### E. Terminal Compatibility Notes

1. **Unicode Weather Symbols**: Most terminals support U+2600-U+26FF. Extended emoji (U+1F300+) requires emoji font.

2. **Box Drawing**: Use Unicode box chars (─│┌┐└┘) for best compatibility.

3. **ANSI Colors**: 256-color mode (`\033[38;5;NNNm`) preferred over basic 16.

4. **Recommended Terminals**: iTerm2, Kitty, Alacritty, Windows Terminal all have excellent Unicode/color support.

---

## Implementation Quick Reference

### Run the App
```bash
cd weather-dashboard
python main.py
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Key Files to Create (in order)
1. `main.py` - Entry point
2. `src/app.py` - Main app class
3. `src/api/client.py` - Open-Meteo API
4. `src/models/weather.py` - Data models
5. `src/widgets/current_weather.py` - Current conditions
6. `src/widgets/hourly_forecast.py` - Hourly panel
7. `src/widgets/daily_forecast.py` - 7-day panel
8. `src/widgets/astro_panel.py` - Sun/moon
9. `src/screens/search_screen.py` - Location search
10. `src/styles/theme.css` - Styling

---

*Plan last updated: 2026-04-16*
*Includes research from: Open-Meteo docs, Textual framework, ASCII weather art patterns*
