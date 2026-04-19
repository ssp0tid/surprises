# TermTimer - Terminal-Based Timer & Alarm Clock

## Overview

TermTimer is a TUI (Text User Interface) application built with Python Textual for terminal-based time management. It provides countdown timers, stopwatch, pomodoro sessions, and custom alarms with system notifications.

---

## Tech Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Framework | Python 3.11+ | Modern async, type hints |
| TUI | Textual 0.80+ | Rich TUI with reactive bindings |
| Notifications | notify-run / plyer | Cross-platform desktop notifications |
| Audio | playsound / subprocess | Alarm sound playback |
| Time | asyncio + datetime | Non-blocking async operations |

### Dependencies (pyproject.toml)

```toml
[project]
name = "termtimer"
version = "0.1.0"
requires-python = ">=3.11"

[project.dependencies]
textual >= "0.80.0"
notify-run >= "0.2.0"
playsound >= "1.3.0"

[project.optional-dependencies]
dev = ["pytest", "pytest-asyncio", "ruff"]
```

---

## File Structure

```
termtimer/
├── pyproject.toml
├── README.md
├── termtimer/
│   ├── __init__.py
│   ├── __main__.py          # Entry point: python -m termtimer
│   ├── app.py               # Main Textual App class
│   ├── models/
│   │   ├── __init__.py
│   │   ├── timer.py         # Timer state machine (running/paused/stopped)
│   │   ├── stopwatch.py     # Stopwatch model
│   │   ├── pomodoro.py      # Pomodoro session manager
│   │   └── alarm.py         # Alarm model with sound path
│   ├── screens/
│   │   ├── __init__.py
│   │   ├── home.py          # Main dashboard with mode selector
│   │   ├── countdown.py     # Countdown timer screen
│   │   ├── stopwatch.py     # Stopwatch screen
│   │   ├── pomodoro.py      # Pomodoro timer screen
│   │   └── alarm.py         # Alarm clock screen
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── time_display.py  # Large monospace time renderer
│   │   ├── timer_controls.py # Start/Pause/Reset buttons
│   │   ├── progress_ring.py # ASCII/Unicode progress indicator
│   │   └── input_digit.py   # Digit input for setting time
│   ├── services/
│   │   ├── __init__.py
│   │   ├── notifier.py      # System notification dispatcher
│   │   ├── audio.py         # Sound playback service
│   │   └── storage.py       # JSON persistence for settings/presets
│   ├── css/
│   │   └── styles.tcss      # Textual CSS styles
│   └── sounds/
│       └── alarm.mp3        # Default alarm sound (bundled)
└── tests/
    ├── __init__.py
    ├── test_timer.py
    ├── test_stopwatch.py
    ├── test_pomodoro.py
    └── test_alarm.py
```

---

## Core Features

### 1. Countdown Timer

| Feature | Description |
|---------|-------------|
| Time input | Set hours, minutes, seconds via digit input |
| Presets | Quick-select common durations (5m, 10m, 15m, 25m, 30m, 45m, 60m) |
| Start/Pause/Reset | Standard timer controls |
| Progress indicator | Visual countdown progress (percentage + ETA) |
| Completion | System notification + optional sound |

### 2. Stopwatch

| Feature | Description |
|---------|-------------|
| Lap times | Record lap splits, display lap table |
| Start/Stop | Toggle stopwatch |
| Reset | Clear all laps and time |
| Display | Large time display (HH:MM:SS.ms) |

### 3. Pomodoro

| Feature | Description |
|---------|-------------|
| Work interval | Configurable work duration (default 25 min) |
| Short break | Configurable break (default 5 min) |
| Long break | After N pomodoros (default 4), longer break (default 15 min) |
| Session counter | Track completed pomodoros |
| Auto-advance | Automatically start next phase |
| Notifications | Notify on interval completion |

### 4. Custom Alarms

| Feature | Description |
|---------|-------------|
| Time picker | Set alarm hour and minute |
| Repeat days | Configure repeat schedule (once, daily, weekdays, weekends, custom) |
| Label/description | Custom alarm name |
| Sound selection | Pick alarm sound from bundled options |
| Snooze | 5-minute snooze functionality |

---

## UI Design

### Color Scheme (Textual CSS)

```
# Background: dark #1a1a2e
# Primary accent: cyan #00d9ff
# Secondary accent: purple #9d4edd
# Warning: orange #ff6b35
# Success: green #39ff14
# Text: white #ffffff
# Muted: gray #6b7280
```

### Layout

```
┌─────────────────────────────────────────┐
│  TERMTIMER            [time] [date]     │
├─────────────────────────────────────────┤
│                                         │
│   ┌─────────┐  ┌─────────┐  ┌────────┐  │
│   │ COUNT   │  │ STOP    │  │ POMODOR│  │
│   │ DOWN    │  │ WATCH   │  │ O      │  │
│   └─────────┘  └─────────┘  └────────┘  │
│                                         │
│   ┌─────────┐                           │
│   │  ALARM  │                           │
│   └─────────┘                           │
│                                         │
├─────────────────────────────────────────┤
│  [settings gear icon]                   │
└─────────────────────────────────────────┘
```

### Screen States

| State | Visual Indicator |
|-------|------------------|
| Idle | Gray text, awaiting input |
| Running | Pulsing accent color |
| Paused | Blinking warning color |
| Completed | Green flash, notification sent |

---

## Architecture

### State Management

```
App
├── current_mode: Literal["countdown", "stopwatch", "pomodoro", "alarm"]
├── timers: dict[str, Timer]
├── alarms: list[Alarm]
└── settings: AppSettings
```

### Timer State Machine

```
States: IDLE → RUNNING ⇄ PAUSED → COMPLETED
              ↓
            RESET → IDLE
```

### Async Event Loop

- Use `asyncio` for timer ticks (update every 100ms for stopwatch, 1s for countdown)
- Schedule alarms using `asyncio.create_task` with calculated delay
- Textual reactive bindings for UI updates

---

## Implementation Phases

### Phase 1: Foundation
- [ ] Project setup (pyproject.toml, directory structure)
- [ ] Basic Textual app skeleton with screen navigation
- [ ] Time display widget
- [ ] Timer model (state machine)

### Phase 2: Core Features
- [ ] Countdown timer screen
- [ ] Stopwatch screen
- [ ] Timer controls widget

### Phase 3: Advanced Features
- [ ] Pomodoro screen + session management
- [ ] Alarm screen + scheduling
- [ ] System notifications

### Phase 4: Polish
- [ ] Sound playback
- [ ] Settings persistence (JSON)
- [ ] CSS styling pass
- [ ] Keyboard shortcuts

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `q` | Quit application |
| `1-4` | Switch modes (countdown, stopwatch, pomodoro, alarm) |
| `Space` | Start/Pause current timer |
| `r` | Reset current timer |
| `s` | Stop (stopwatch) / Snooze (alarm) |
| `?` | Show help |

---

## Acceptance Criteria

1. ✅ Countdown timer counts down accurately to 0
2. ✅ Stopwatch tracks time with lap functionality
3. ✅ Pomodoro cycles through work/break intervals
4. ✅ Alarms trigger notification and sound at set time
5. ✅ All screens navigable via keyboard
6. ✅ Settings persist between sessions
7. ✅ Application runs without errors in terminal
