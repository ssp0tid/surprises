# Crono - Visual Cron Job Scheduler TUI

A terminal-based cron job scheduler and manager built with Python and Textual framework. Manage your cron jobs visually with keyboard navigation.


## Features

- Cron expression parser and validator with real-time validation
- Job CRUD operations (create, read, update, delete)
- Next run time calculation with human-readable output
- Job history logging with execution results
- Dark-themed terminal UI
- Full keyboard navigation


## Installation

```bash
pip install -r requirements.txt
```

Or from source:

```bash
pip install -e .
```


## Usage

Run the application:

```bash
python -m crono
```

Or if installed:

```bash
crono
```


## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `n` | Create new job |
| `e` | Edit selected job |
| `d` | Delete selected job |
| `Space` | Toggle job active/paused |
| `r` | Run job now |
| `l` | View job history |
| `F1` | Help |
| `q` / `Escape` | Quit |


## Creating Jobs

1. Press `n` to create a new job
2. Enter job name (e.g., `daily-backup`)
3. Enter command to execute (e.g., `backup.sh`)
4. Enter cron expression (e.g., `0 2 * * *`)
5. Optionally add description
6. Press Save


## Cron Expression Format

```
┌───────────── minute (0-59)
│ ┌─────────── hour (0-23)
│ │ ┌──────── day of month (1-31)
│ │ │ ┌────── month (1-12)
│ │ │ │ ┌──── day of week (0-6, Sunday=0)
* * * * *
```

Examples:
- `* * * * *` - Every minute
- `0 * * * *` - Every hour at minute 0
- `0 9 * * 1-5` - Weekdays at 9:00 AM
- `0 0 1 * *` - First day of every month at midnight


## Configuration

Jobs are stored in `~/.config/crono/data.json`.


## Requirements

- Python 3.10+
- textual >= 0.52.0
- python-croniter >= 2.0.0
- pydantic >= 2.0.0


## License

MIT