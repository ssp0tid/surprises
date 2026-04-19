# LogProbe

**Interactive Terminal Log Explorer & Analyzer**

A high-performance TUI (Terminal User Interface) CLI utility for opening, searching, filtering, and exploring large log files in the terminal.

## Features

- 🚀 **High Performance**: Handles files from KB to 10GB+
- ⌨️ **Vim-like Navigation**: Familiar keyboard shortcuts (j/k, gg/G, /, n/N)
- 📡 **Live Tailing**: Follow file changes in real-time (tail -f mode)
- 🔍 **Regex Search**: Powerful search with match highlighting
- 🎛️ **Log Filtering**: Filter by DEBUG/INFO/WARN/ERROR/FATAL levels
- ⏰ **Timestamp Filtering**: Filter by time range
- 🔖 **Bookmarks**: Save and restore line positions
- 🎨 **Color Themes**: Dark and light themes with level-based highlighting

## Installation

### Prerequisites

- Rust 1.70+ (with Cargo)
- A terminal emulator (supports ANSI colors)

### Build from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/logprobe.git
cd logprobe

# Build release version
cargo build --release

# The binary will be at target/release/logprobe
```

### Install via Cargo

```bash
cargo install logprobe
```

## Usage

### Basic Usage

```bash
# Open a log file
logprobe app.log

# Open and follow new content (like tail -f)
logprobe -f /var/log/syslog

# Start at last 100 lines
logprobe -n 100 app.log
```

### Command Line Options

```
logprobe [OPTIONS] [FILE]

Positional Arguments:
  FILE              Log file to open

Options:
  -f, --follow      Follow file changes (tail -f mode)
  -n, --lines N     Start at last N lines
  -c, --config FILE Custom config file
  --theme THEME      Color theme (dark|light) [default: dark]
  --no-line-numbers  Hide line numbers
  -l, --level LEVELS    Filter by levels (e.g., ERROR,WARN)
  -t, --time-from T    Start time (ISO 8601)
  -T, --time-to T      End time (ISO 8601)
  -g, --grep PATTERN   Initial search pattern
  -h, --help        Show help
  -V, --version     Show version
```

### Keyboard Shortcuts

#### Navigation Mode

| Key | Action |
|-----|--------|
| `j` / `↓` | Scroll line down |
| `k` / `↑` | Scroll line up |
| `g` | Go to first line |
| `G` | Go to last line |
| `d` / `Ctrl+d` | Scroll half page down |
| `u` / `Ctrl+u` | Scroll half page up |
| `f` / `Ctrl+f` | Scroll full page down |
| `b` / `Ctrl+b` | Scroll full page up |

#### Search Mode

| Key | Action |
|-----|--------|
| `/` | Open search (forward) |
| `?` | Open search (backward) |
| `n` | Next match |
| `N` | Previous match |
| `Esc` | Exit search |

#### Filter Mode

| Key | Action |
|-----|--------|
| `l` | Open level filter |
| `d` | Toggle DEBUG level |
| `i` | Toggle INFO level |
| `w` | Toggle WARN level |
| `e` | Toggle ERROR level |
| `f` | Toggle FATAL level |
| `a` | Enable all levels |
| `r` | Reset filters |

#### Bookmarks

| Key | Action |
|-----|--------|
| `m[a-z]` | Set bookmark a-z |
| `'[a-z]` | Jump to bookmark a-z |

#### General

| Key | Action |
|-----|--------|
| `:` | Command mode |
| `q` | Quit |
| `Ctrl+c` | Quit (alternate) |
| `?` / `F1` | Help |

### Command Mode

| Command | Action |
|---------|--------|
| `:q` | Quit |
| `:wq` | Save and quit |
| `:set theme=dark` | Set theme |
| `:goto 1000` | Go to line 1000 |
| `/pattern` | Search |

## Configuration

LogProbe reads configuration from `~/.config/logprobe/config.toml` (Linux/macOS) or `%APPDATA%\logprobe\config.toml` (Windows).

### Example Configuration

```toml
[display]
line_numbers = true
wrap = false
tab_width = 8
max_line_length = 10000

[performance]
index_cache_size = "100MB"
read_ahead_lines = 1000
search_workers = 4
tail_debounce_ms = 100

[behavior]
follow_on_open = false
auto_reload = true
confirm_quit = false
search_wrap = true

[files]
follow_symlinks = true
auto_detect_format = true
supported_extensions = [".log", ".txt", ".json", ".out"]
```

### Themes

#### Dark Theme (Default)

- Background: `#1e1e2e`
- Foreground: `#cdd6f4`
- Debug: `#6c7086`
- Info: `#89b4fa`
- Warn: `#f9e2af`
- Error: `#f38ba8`
- Fatal: `#d20f39`

#### Light Theme

- Background: `#eff1f5`
- Foreground: `#4c4f69`
- Debug: `#6c7086`
- Info: `#89b4fa`
- Warn: `#f9e2af`
- Error: `#d20f39`
- Fatal: `#d20f39`

## Log Format Support

LogProbe auto-detects and parses multiple log formats:

1. **JSON/JSONL**: Structured logs (detected first)
2. **Apache/Nginx Combined Log**: `127.0.0.1 - - [01/Jan/2024:10:30:00 +0000]`
3. **Syslog**: RFC 3164 format
4. **ISO Timestamp**: `2024-01-15T10:30:00.123Z`
5. **Plain Text**: Fallback for unstructured logs

## Development

### Project Structure

```
logprobe/
├── Cargo.toml
├── README.md
├── PLAN.md
├── src/
│   ├── bin/
│   │   └── main.rs           # CLI entry, arg parsing, event loop
│   ├── lib.rs                # Library root, re-exports
│   ├── app.rs                # App state, key handling
│   ├── config.rs             # Config loading, defaults
│   ├── errors.rs             # Error types
│   ├── ui/
│   │   ├── mod.rs            # UI module
│   │   ├── layout.rs         # Layout definitions
│   │   ├── views.rs          # Custom views/widgets
│   │   ├── state.rs          # UI state (scroll, selection)
│   │   └── styles.rs         # Theme, colors
│   ├── log/
│   │   ├── mod.rs            # Log module
│   │   ├── file.rs           # File handling (streaming)
│   │   ├── parser.rs         # Log line parsing
│   │   ├── level.rs          # Log level detection
│   │   ├── timestamp.rs      # Timestamp extraction
│   │   └── watcher.rs        # File watching
│   ├── search/
│   │   ├── mod.rs            # Search module
│   │   ├── engine.rs          # Search engine
│   │   ├── regex.rs           # Regex utilities
│   │   └── index.rs           # Line offset index
│   └── bookmarks/
│       ├── mod.rs            # Bookmarks module
│       └── storage.rs        # Bookmark persistence
└── tests/
    └── integration.rs
```

### Building

```bash
# Build debug version
cargo build

# Build release version
cargo build --release

# Run tests
cargo test

# Run with logging
RUST_LOG=debug cargo run --release app.log
```

### Dependencies

| Crate | Version | Purpose |
|-------|---------|---------|
| ratatui | 0.30 | TUI rendering |
| crossterm | 0.28 | Terminal I/O, events |
| clap | 5 (derive) | CLI argument parsing |
| notify | 7 | File watching |
| regex | 1 | Regex search |
| chrono | 0.4 (serde) | Timestamp parsing |
| thiserror | 2 | Error types |
| tokio | 1 (sync, time, rt) | Async runtime |
| serde | 1 (derive) | Serialization |
| serde_json | 1 | JSON parsing |
| toml | 0.8 | Config file parsing |
| dirs | 5 | Config directory lookup |
| bitvec | 1 | Efficient bitset operations |
| tracing | 0.1 | Debug logging |
| tempfile | 3 | Test file creation |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (normal exit) |
| 1 | Error (file not found, invalid args) |
| 2 | Signal interrupt (Ctrl+C) |

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please read the contribution guidelines and submit PRs.

## Similar Projects

- [lnav](https://github.com/tstack/lnav) - Feature-rich log viewer
- [logana](https://github.com/pauloremoli/logana) - Memory-mapped log analysis
- [qlog](https://github.com/jojonv/qlog) - Clean module structure
