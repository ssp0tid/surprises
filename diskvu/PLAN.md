# diskvu — Interactive Terminal Disk Usage Analyzer

A lightweight ncdu-style disk usage explorer for the terminal. Navigate directories, see sizes at a glance with bar charts, sort by size/name/count, and drill into subdirectories interactively.

## Tech Stack

- Python 3 curses (stdlib only — no external dependencies)
- Single file implementation

## Constraints

- No external packages (stdlib only)
- Must handle permission errors gracefully (skip unreadable dirs)
- Must work on Linux terminals with at least 80x24
- Responsive to terminal resize

## File Structure

```
diskvu/
├── PLAN.md
├── README.md
└── diskvu.py          # Entry point — all logic in one file
```

## Features

### 1. Directory Scanning
- `scan_directory(path: str) -> DirNode` — recursively walks the filesystem
- Returns a tree of `DirNode` dataclass instances:
  ```python
  @dataclasses.dataclass
  class DirNode:
      path: str           # absolute path
      name: str           # basename
      size: int           # total bytes (recursive)
      is_dir: bool
      children: list      # list of DirNode, sorted by size desc
      file_count: int     # number of files (recursive)
      error: str | None   # permission error message if any
  ```
- Handles PermissionError, OSError gracefully — stores error message in node
- Uses `os.scandir()` for performance

### 2. Interactive Navigation (curses UI)
- `class DiskVuApp` — main application class
- Key bindings:
  - `↑/k` — move cursor up
  - `↓/j` — move cursor down
  - `Enter/→/l` — enter directory
  - `Backspace/←/h` — go to parent
  - `s` — cycle sort mode (size desc, size asc, name asc, file count)
  - `d` — delete selected item (with confirmation prompt)
  - `q/Esc` — quit
  - `r` — rescan current directory
  - `?` — toggle help overlay

### 3. Display Layout
```
┌─ diskvu: /home/user ──────────────────── 4.2 GB total ─┐
│                                                          │
│   4.1 GB [##########] .local/          (1,204 files)    │
│  89.3 MB [#         ] Documents/         (342 files)    │
│  12.1 MB [          ] .config/            (89 files)    │
│   1.2 MB [          ] .bashrc               (1 file)    │
│                                                          │
├──────────────────────────────────────────────────────────┤
│ [s]ort [d]elete [r]escan [?]help [q]uit                 │
└──────────────────────────────────────────────────────────┘
```

- Each line shows: human-readable size, proportional bar (10 chars), name (with `/` suffix for dirs), file count
- Highlighted row shows full path in status bar
- Bar width proportional to largest item in current view

### 4. Size Formatting
- `format_size(bytes: int) -> str` — returns human-readable string
  - < 1024 → "N B"
  - < 1024² → "N.N KB"
  - < 1024³ → "N.N MB"
  - < 1024⁴ → "N.N GB"
  - else → "N.N TB"

### 5. Delete with Confirmation
- `delete_item(node: DirNode)` — shows confirmation prompt at bottom
- Prompt: "Delete [name]? (y/N)"
- Uses `shutil.rmtree()` for dirs, `os.unlink()` for files
- After delete, rescans parent

### 6. Command-Line Interface
- `python3 diskvu.py [PATH]` — start exploring PATH (default: current directory)
- `python3 diskvu.py --help` — show usage
- Uses `argparse` for argument parsing

### 7. Progress Indicator
- During initial scan, show "Scanning... [N files found]" with a spinner
- Update every 100ms using non-blocking scan with threading

## Entry Point

`diskvu.py` — run with `python3 diskvu.py [path]`

## Implementation Notes

- Use `curses.wrapper()` for safe terminal init/cleanup
- Handle `curses.KEY_RESIZE` for terminal resize events
- Use `threading.Thread` for background scanning so UI stays responsive during rescan
- Scrolling: track `scroll_offset` and `cursor_pos`, ensure cursor stays visible
- Color pairs: use `curses.init_pair()` for directory (blue), file (white), bar (cyan), error (red)
