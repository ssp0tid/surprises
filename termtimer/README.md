# TermTimer

A terminal-based timer and alarm clock built with Python Textual.

## Features

- **Countdown Timer** - Set custom durations with presets (5m, 10m, 15m, 25m, 30m, 45m, 60m)
- **Stopwatch** - Track time with lap functionality
- **Pomodoro** - Work/break cycles (25min work, 5min short break, 15min long break)
- **Alarms** - Set alarms with repeat options (once, daily, weekdays, weekends)

## Requirements

- Python 3.11+
- textual >= 0.80.0
- notify-run >= 0.2.0 (for system notifications)
- playsound >= 1.3.0 (for alarm sounds)

## Installation

### From source

```bash
cd termtimer
pip install -e .
```

Or install dependencies manually:

```bash
pip install textual notify-run playsound
```

## Usage

Run the application:

```bash
python -m termtimer
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `q` | Quit application |
| `1` | Countdown timer |
| `2` | Stopwatch |
| `3` | Pomodoro |
| `4` | Alarm |
| `Space` | Start/Pause |
| `r` | Reset |
| `l` | Lap (stopwatch) |
| `s` | Snooze (alarm) |
| `escape` | Go to home |

### Countdown Timer

- Press preset buttons to set duration
- Press SPACE to start/pause
- Press R to reset

### Stopwatch

- Press SPACE to start/stop
- Press L to record lap
- Press R to reset

### Pomodoro

- Press SPACE to start work session
- Cycles automatically through work/break phases
- Shows session count

### Alarm

- Press SPACE to cycle through hours (starting at 6:00)
- Press S to snooze (5 minutes)
- Press C to clear alarm

## Configuration

Settings are stored in `~/.config/termtimer/`:
- `settings.json` - Application settings
- `alarms.json` - Saved alarms
- `presets.json` - Timer presets

## Development

### Install dev dependencies

```bash
pip install -e ".[dev]"
```

### Run tests

```bash
pytest tests/
```

## License

MIT License