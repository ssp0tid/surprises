# diskvu

Interactive terminal disk usage analyzer. Navigate directories, see sizes at a glance with bar charts, sort by size/name/count, and drill into subdirectories — all from your terminal.

No external dependencies. Python 3 stdlib only.

## Usage

```bash
python3 diskvu.py [PATH]
```

If no path is given, the current directory is used.

```bash
python3 diskvu.py --help
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `↑` / `k` | Move cursor up |
| `↓` / `j` | Move cursor down |
| `Enter` / `→` / `l` | Enter directory |
| `Backspace` / `←` / `h` | Go to parent |
| `s` | Cycle sort mode (size ↓, size ↑, name, file count) |
| `d` | Delete selected item (with confirmation) |
| `r` | Rescan current directory |
| `?` | Toggle help overlay |
| `q` / `Esc` | Quit |

## Requirements

- Python 3.9+
- Linux terminal with at least 80x24
- No external packages needed
