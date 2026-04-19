# Weather TUI

A beautiful terminal weather dashboard built with Python and Textual.

## Features

- **Current Weather**: Temperature, feels like, humidity, wind speed/direction
- **Hourly Forecast**: 24-hour forecast with temperature and precipitation
- **7-Day Forecast**: Daily high/low temperatures and conditions
- **Sun & Moon**: Sunrise/sunset times and moon phase
- **Location Search**: Search for any city worldwide
- **Auto Location**: Automatically detects your location via IP
- **Unit Toggle**: Switch between metric (°C) and imperial (°F)
- **Offline Support**: Cached data shown when offline
- **ASCII Art**: Beautiful weather icons and box-drawing characters

## Requirements

- Python 3.10+
- Textual
- httpx
- cachetools

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd weather-dashboard

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
python -m src.main
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `r` | Refresh weather data |
| `u` | Toggle metric/imperial units |
| `s` | Open location search |
| `Esc` | Close search/go back |
| `q` | Quit application |

## Configuration

Configuration is stored in `~/.config/weather_tui/config.json`:
- Unit preference (metric/imperial)
- Last location used
- Cache TTL settings

## Data Source

Weather data provided by [Open-Meteo](https://open-meteo.com/) - free, no API key required.

## License

MIT
