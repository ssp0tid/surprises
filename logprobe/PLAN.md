# LogProbe - Implementation Plan

## Interactive Terminal Log Explorer & Analyzer

A TUI (Terminal User Interface) CLI utility for opening, searching, filtering, and exploring large log files in the terminal.

---

## 1. Project Overview

### Goals
- Build a high-performance log file viewer handling files from KB to 10GB+
- Provide vim-like keyboard navigation familiar to developers
- Enable real-time log monitoring with live tailing
- Support powerful search and filtering without loading entire files into memory

### Target Users
- DevOps engineers debugging production systems
- Backend developers analyzing application logs
- System administrators monitoring server logs
- Anyone needing to explore large log files interactively

---

## 2. Feature Specifications

### Core Features

| Feature | Priority | Description |
|---------|----------|-------------|
| **File Loading** | P0 | Open log files via CLI arg, lazy-load lines on scroll |
| **Live Tailing** | P0 | Follow file changes in real-time (tail -f mode) |
| **Regex Search** | P0 | Search with highlight matches, incremental results |
| **Level Filtering** | P0 | Filter by DEBUG/INFO/WARN/ERROR/FATAL |
| **Timestamp Filter** | P0 | Filter by time range with date picker |
| **Line Numbers** | P1 | Optional display of line numbers |
| **Bookmarks** | P1 | Save/restore line positions |
| **Split View** | P1 | Filtered + full view side-by-side |
| **Keyboard Nav** | P0 | Vim-like: j/k, gg/G, /, n/N, ctrl-u/d |
| **Mouse Support** | P2 | Scroll, click to select lines |

### Search Features
- Regex search with match highlighting
- Case-sensitive/insensitive toggle
- Whole-word matching
- Search history (up/down arrows)
- Jump to next/previous match (n/N)

### Filter Features
- Log level checkboxes (multi-select)
- Time range picker (start date/time, end date/time)
- Combine filters (AND logic)
- Invert filter (show non-matching)

### Navigation
| Key | Action |
|-----|--------|
| `j` / `k` | Line down/up |
| `gg` / `G` | First/last line |
| `ctrl-d` / `ctrl-u` | Half page down/up |
| `ctrl-f` / `ctrl-b` | Full page down/up |
| `/` | Open search |
| `n` / `N` | Next/prev match |
| `:` | Command mode |
| `m[a-z]` | Set bookmark |
| `'[a-z]` | Jump to bookmark |
| `q` | Quit |

---

## 3. File Structure

```
logprobe/
├── Cargo.toml
├── README.md
├── LICENSE
├── src/
│   ├── bin/
│   │   └── main.rs           # CLI entry, arg parsing, event loop
│   ├── lib.rs              # Library root, re-exports
│   ├── app.rs              # App state, key handling
│   ├── config.rs           # Config loading, defaults
│   ├── ui/
│   │   ├── mod.rs          # UI module
│   │   ├── layout.rs       # Layout definitions
│   │   ├── views.rs       # Custom views/widgets
│   │   ├── state.rs       # UI state (scroll, selection)
│   │   └── styles.rs      # Theme, colors
│   ├── log/
│   │   ├── mod.rs         # Log module
│   │   ├── file.rs       # File handling (mmap, streaming)
│   │   ├── parser.rs      # Log line parsing
│   │   ├── level.rs      # Log level detection
│   │   ├── timestamp.rs   # Timestamp extraction
│   │   └── watcher.rs    # File watching (inotify)
│   ├── search/
│   │   ├── mod.rs        # Search module
│   │   ├── engine.rs    # Search engine
│   │   ├── regex.rs     # Regex utilities
│   │   └── index.rs    # Line offset index
│   ├── bookmarks/
│   │   ├── mod.rs         # Bookmarks module
│   │   └── storage.rs    # Bookmark persistence
│   └── errors.rs           # Error types
└── tests/
    └── integration.rs
```

### Module Responsibilities

| Module | Responsibility |
|--------|---------------|
| `bin/main.rs` | CLI args (clap), terminal setup, event loop |
| `app.rs` | Application state, key event routing |
| `config.rs` | Config file loading, keybindings, themes |
| `ui/` | All TUI rendering, layouts, widgets |
| `log/file.rs` | mmap or streaming file I/O |
| `log/parser.rs` | Parse log lines (level, timestamp, fields) |
| `log/watcher.rs` | File change notifications |
| `search/` | Regex search, line index |
| `bookmarks/` | Save/restore positions |

---

## 4. API Design

### Public API (Library Usage)

```rust
use logprobe::{LogViewer, Config};

// Basic usage
let viewer = LogViewer::new("app.log")?;
viewer.run()?;

// With configuration
let config = Config::default()
    .with_theme("dark")
    .with_keybindings(Keybindings::vim());
let viewer = LogViewer::with_config("app.log", config)?;
viewer.run()?;

// Programmatic access
let lines = viewer.file().lines(0..1000)?;
let matches = viewer.search().regex(r"ERROR.*timeout")?;
```

### Internal Architecture

```
LogViewer
├── file: LogFile          # mmap + line index
│   ├── mmap: Mmap        # Memory map
│   └── index: LineIndex   # Offset → line position
├── search: SearchEngine  # Regex + results
│   ├── pattern: Regex
│   └── matches: Vec<Match>
├── filters: Filters     # Active filters
│   ├── levels: BitSet
│   └── time_range: Range
├── bookmarks: BookmarkStore
└── ui: UIState           # Scroll, selection
    ├── scroll: u64
    ├── selection: u64
    └── view_mode: ViewMode
```

### Key Types

```rust
// LogFile: Efficient file access
pub struct LogFile {
    path: PathBuf,
    mmap: Option<Mmap>,
    index: LineIndex,
}

// LineIndex: Line offset caching
pub struct LineIndex {
    offsets: Vec<u64>,  // byte offset per line
    cache: RwLock<Arc<Vec<u64>>>,
}

// SearchEngine: Search with highlighting
pub struct SearchEngine {
    pattern: Regex,
    cache: RegexCache,
}

// LogLine: Parsed line
pub struct LogLine {
    text: String,
    level: Level,
    timestamp: Option<DateTime<Utc>>,
    line_number: u64,
}

// Level: Log severity
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Level {
    Debug,
    Info,
    Warn,
    Error,
    Fatal,
    Unknown,
}
```

---

## 5. Dependencies

### Core Dependencies

| Crate | Version | Purpose |
|-------|---------|---------|
| **ratatui** | ^0.30 | TUI rendering (immediate mode) |
| **crossterm** | ^0.28 | Terminal I/O, events |
| **clap** | ^5.0 | CLI argument parsing |
| **memmap2** | ^0.9 | Memory-mapped file I/O (static files only!) |
| **notify** | ^7.0 | File watching (inotify/FSEvents) |
| **regex** | ^1.0 | Regex search |
| **chrono** | ^0.4 | Timestamp parsing |
| **serde** / **serde_json** | ^1.0 | JSON log parsing |
| **thiserror** | ^2.0 | Error types |
| **tokio** | ^1.0 | Async runtime |
| **tracing** | ^0.1 | Debug logging |
| **tracing-subscriber** | ^0.3 | Log output |

### Optional Widget Extensions

| Crate | Purpose |
|-------|---------|
| **tui-widget-list** | Enhanced scrolling, page-up/down |
| **tui-textarea** | Multi-line text input for search |
| **ratatui-widget-scrolling** | Virtual scrolling for large lists |

### Ratatui v0.30 Architecture

```
ratatui           # Complete crate (re-exports)
├── ratatui-core  # Core traits/types
└── ratatui-widgets  # Built-in widgets
```

### Cargo.toml Starter

```toml
[package]
name = "logprobe"
version = "0.1.0"
edition = "2021"

[dependencies]
ratatui = "0.30"
crossterm = { version = "0.28", features = ["event-stream"] }
clap = { version = "5", features = ["derive"] }
memmap2 = "0.9"
notify = "7"
regex = "1"
chrono = { version = "0.4", features = ["serde"] }
thiserror = "2"
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }

[dev-dependencies]
tempfile = "3"

[[bin]]
name = "logprobe"
path = "src/bin/main.rs"
```

---

## 6. Error Handling

### Error Types

```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum Error {
    #[error("File not found: {0}")]
    FileNotFound(PathBuf),

    #[error("Permission denied: {0}")]
    PermissionDenied(PathBuf),

    #[error("Invalid regex: {0}")]
    InvalidRegex(String),

    #[error("File changed during read")]
    FileChanged,

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("UTF-8 error at line {line}: {context}")]
    Utf8Error { line: u64, context: String },
}
```

### Error Recovery Strategy

| Error | Recovery |
|-------|----------|
| File not found | Prompt user with file picker |
| Permission denied | Show error, exit with code 1 |
| Invalid regex | Show error inline, don't apply filter |
| File changed | Auto-reload, show notification |
| Encoding error | Attempt Latin-1, show raw bytes |

---

## 7. Edge Cases

### File Handling

| Edge Case | Handling |
|----------|----------|
| Empty file | Show "Empty file" message |
| Binary file | Detect via null bytes, warn user |
| Long lines (>10KB) | Truncate display, show indicator |
| Rapid updates | Debounce tail (100ms), batch writes |
| File rotation | Detect inode change, auto-reload |
| Compressed (.gz) | Fork to `zcat`, stream output |
| Encrypted | Refuse with clear error |

### Search/Filter

| Edge Case | Handling |
|-----------|----------|
| Invalid regex | Show error, don't execute |
| No matches | Show "No matches" with query |
| Millions of matches | Paginate results, limit memory |
| Slow regex | Timeout (5s), show cancellation |

### UI

| Edge Case | Handling |
|----------|----------|
| Small terminal | Minimum 80x24, warn if smaller |
| Resize during use | Re-calculate layout, preserve scroll |
| Mouse not supported | Graceful fall back to keyboard |

---

## 8. Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Project setup (Cargo.toml, basic structure)
- [ ] File loading with mmap
- [ ] Basic TUI with line display
- [ ] Keyboard navigation (j/k, gg/G)

### Phase 2: Search (Week 2)
- [ ] Regex search with highlighting
- [ ] Search navigation (n/N)
- [ ] Case toggle, word toggle
- [ ] Search history

### Phase 3: Filters (Week 2-3)
- [ ] Level detection
- [ ] Level filtering (checkboxes)
- [ ] Timestamp extraction
- [ ] Time range filter

### Phase 4: Advanced (Week 3-4)
- [ ] Live tailing (notify)
- [ ] Bookmarks
- [ ] Split view
- [ ] Config, themes

### Phase 5: Polish (Week 4)
- [ ] Mouse support
- [ ] Performance tuning
- [ ] Testing
- [ ] Documentation

---

## 9. Keyboard Shortcuts Reference

### Navigation Mode

| Key | Action |
|-----|--------|
| `j` / `k` | Scroll line down/up |
| `↓` / `↑` | Scroll line down/up |
| `d` / `u` | Scroll half page down/up |
| `f` / `b` | Scroll full page down/up |
| `g` | Go to first line |
| `G` | Go to last line |
| `Ctrl-d` | Scroll half page down |
| `Ctrl-u` | Scroll half page up |
| `Ctrl-f` | Scroll full page down |
| `Ctrl-b` | Scroll full page up |
| `Enter` | Begin search ( `/` ) |

### Search Mode

| Key | Action |
|-----|--------|
| `/` | Open search (forward) |
| `?` | Open search (backward) |
| `n` | Next match |
| `N` | Previous match |
| `Esc` | Exit search |
| `Ctrl-g` | Go to match count |

### Filter Mode

| Key | Action |
|-----|--------|
| `l` | Toggle level filter menu |
| `t` | Toggle timestamp filter |
| `Ctrl-r` | Reset filters |
| `v` | Invert filter |

### Bookmark Mode

| Key | Action |
|-----|--------|
| `m[a-z]` | Set bookmark a-z |
| `'[a-z]` | Jump to bookmark a-z |
| `m<Space>` | Clear all bookmarks |

### General

| Key | Action |
|-----|--------|
| `:` | Command mode |
| `q` | Quit |
| `Ctrl-c` | Quit (alternate) |
| `Ctrl-q` | Force quit |
| `Ctrl-z` | Background (suspend) |
| `F1` / `?` | Help |

### Command Mode

| Command | Action |
|---------|--------|
| `:q` | Quit |
| `:wq` | Save and quit |
| `:set theme=dark` | Set theme |
| `:goto 1000` | Go to line 1000 |
| `/pattern` | Search |

---

## 10. Reference Implementations

### Projects to Study

| Project | URL | Why |
|---------|-----|-----|
| **logana** | github.com/pauloremoli/logana | Memory-mapped log analysis |
| **qlog** | github.com/jojonv/qlog | Clean module structure |
| **logradar** | github.com/nanook72/logradar | Multi-source streaming |
| **lnav** | github.com/tstack/lnav | Feature-rich, SQLite backend |
| **ratatui examples** | github.com/ratatui/ratatui/tree/main/examples | TUI patterns |

### TUI Framework Choice

**Recommended: Ratatui v0.30**

Rationale:
- Active maintenance (19k+ stars)
- Immediate-mode rendering (efficient for large files)
- Excellent for keyboard-driven interfaces
- Large ecosystem (2,100+ crates use it)
- Full control over event loop

---

## 11. Performance Targets

| Metric | Target |
|--------|--------|
| Startup time | < 500ms for 1GB file |
| Scroll latency | < 16ms (60 FPS) |
| Search startup | < 100ms for results |
| Memory (idle) | < 50MB |
| Memory (1GB file) | ~200MB (index + viewport) |

---

## 11.1 Critical Implementation Notes

### File I/O Strategy (CRITICAL - READ THIS)

**CRITICAL INSIGHT from lnav architecture**: Do NOT use `mmap` for files that may change!

> "File contents are consumed using `pread(2)`/`read(2)` and not `mmap(2)` since `mmap(2)` does not react well to files changing out from underneath it. For example, a truncated file would likely result in a `SIGBUS`."

**Recommended Approach:**
```rust
// Use streaming with line index cache (inspired by lnav/logana)
pub struct LogFile {
    path: PathBuf,
    file: File,
    index: Arc<RwLock<LineIndex>>,  // Cache line offsets
}

// Read chunks on demand, cache offsets
fn read_line(&self, line_num: u64) -> Result<LogLine> {
    let offset = self.index.read().await.get_offset(line_num)?;
    let mut buf = vec![0u8; 4096];
    let n = self.file.read_at(&mut buf, offset)?;
    // ...
}
```

**Hybrid Approach:**
- Detect if file is actively being written to → use streaming
- For static files → optionally use mmap for faster random access
- Use file watcher to detect changes and invalidate cache

### Ratatui Widget Ecosystem

**Framework Decision**: **Ratatui** is the clear winner based on research:
- 19.8k+ stars, actively maintained (forked in 2023)
- Best performance for large files (sub-millisecond rendering)
- Rich ecosystem: loghew, logana, taill all use it

**Key Widgets:**
```rust
// For log viewing, combine these widgets:
use ratatui::{
    widgets::{Paragraph, List, Table, Scrollbar},
    layout::{Constraint, Layout, Direction},
};
```

**Scroll Performance**: Ratatui PR #1622 fixed paragraph scroll performance (99% speedup for u16::MAX lines).

**For page-up/page-down scrolling**, implement custom state or use `tui-widget-list`:
```rust
use tui_widget_list::{ListBuilder, ListState, ListView};

let list = ListView::new(builder, item_count)
    .scrollbar(ScrollbarWidget::default())
    .scroll_padding(1);
```

### Log Format Detection (Multi-format)

**Try formats in order** (inspired by lnav):
```rust
pub fn detect_format(line: &str) -> Option<LogFormat> {
    // 1. Try JSON (structured logs)
    if let Ok(json) = serde_json::from_str::<Value>(line) {
        return Some(LogFormat::Json);
    }
    // 2. Try Apache/Nginx Combined Log
    // 3. Try Syslog (RFC 3164/5424)
    // 4. Try ISO timestamp prefix
    // 5. Fall back to plaintext
    None
}
```

**Log Format Regex Patterns:**
```regex
// Apache/Nginx Combined Log
^(\S+) \S+ \S+ \[([^\]]+)\] "([^"]*)" (\d+) (\d+|-)

// Syslog (RFC 3164)
^<(\d+)>(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\S+):\s+(.*)$

// ISO timestamp prefix
^(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)
```

### Timestamp Parsing Priority

```rust
const TIMESTAMP_FORMATS: &[&str] = &[
    "%Y-%m-%dT%H:%M:%S%.f%z",  // ISO 8601 with timezone
    "%Y-%m-%d %H:%M:%S%.f",     // ISO 8601 without timezone
    "%Y-%m-%d %H:%M:%S",        // ISO date without fractional seconds
    "%d/%b/%Y:%H:%M:%S %z",    // Apache/Nginx
    "%b %d %H:%M:%S",          // Syslog (month-day timestamp)
    "%s",                       // Unix timestamp (seconds)
    "%L",                       // Unix timestamp (milliseconds)
];
```

### Log Level Detection

```rust
fn detect_level(text: &str) -> Level {
    let upper = text.to_uppercase();
    if upper.contains("FATAL") || upper.contains("PANIC") {
        Level::Fatal
    } else if upper.contains("ERROR") || upper.contains("ERR") || upper.contains("[E]") {
        Level::Error
    } else if upper.contains("WARN") || upper.contains("WARNING") || upper.contains("[W]") {
        Level::Warn
    } else if upper.contains("INFO") || upper.contains("[I]") {
        Level::Info
    } else if upper.contains("DEBUG") || upper.contains("TRACE") || upper.contains("[D]") {
        Level::Debug
    } else {
        Level::Unknown
    }
}
```

### Async Event Loop Architecture

```rust
use tokio::sync::mpsc;

pub struct App {
    file_tx: mpsc::Sender<FileCommand>,
    search_tx: mpsc::Sender<SearchCommand>,
}

enum FileCommand {
    Load(PathBuf),
    Reload,
    Watch,
}

enum SearchCommand {
    Search { pattern: String, case_insensitive: bool },
    Cancel,
}

// Main loop using tokio::select!
loop {
    tokio::select! {
        Some(event) = crossterm_events.next() => handle_terminal_event(event),
        Some(cmd) = file_rx.recv() => handle_file_command(cmd),
        Some(result) = search_rx.recv() => handle_search_result(result),
    }
}
```

### Reference Projects (Study These)

| Project | URL | Framework | Key Learning |
|---------|-----|-----------|--------------|
| **logana** | github.com/pauloremoli/logana | Ratatui | Memory-mapped log analysis, millions of lines |
| **loghew** | github.com/nehadyounis/loghew | Ratatui | Lazy line indexing |
| **taill** | github.com/zhangzhishanlo/taill | Ratatui | Real-time monitoring |
| **lnav** | github.com/tstack/lnav | C++ | Architecture patterns, log format detection |

---

## 12. Configuration

### Default Keybindings (Vim-style)

```yaml
keybindings:
  navigation:
    j: scroll_down
    k: scroll_up
    g: go_top
    G: go_bottom
    d: scroll_half_down
    u: scroll_half_up
  search:
    "/": search_forward
    "?": search_backward
    n: next_match
    N: prev_match
  filter:
    l: toggle_level_filter
    t: toggle_timestamp_filter
  bookmarks:
    m: set_bookmark
    "'": jump_bookmark
  general:
    ":": command_mode
    q: quit
```

### Default Theme (Dark)

```yaml
theme:
  background: "#1e1e2e"
  foreground: "#cdd6f4"
  selection: "#45475a"
  search_match: "#f38ba8"
  line_number: "#6c7086"
  levels:
    debug: "#6c7086"
    info: "#89b4fa"
    warn: "#f9e2af"
    error: "#f38ba8"
    fatal: "#d20f39"
```

### Additional Configuration Options

```yaml
# ~/.config/logprobe/config.toml

[display]
line_numbers = true
wrap = false
tab_width = 8
max_line_length = 10000  # Truncate longer lines
show_indent_guides = false

[performance]
index_cache_size = "100MB"      # Max memory for line index
read_ahead_lines = 1000         # Lines to prefetch
search_workers = 4               # Parallel search threads
tail_debounce_ms = 100           # Debounce live tail updates

[behavior]
follow_on_open = false           # Start in tail mode
auto_reload = true               # Reload on file change
confirm_quit = false             # Require y to quit
search_wrap = true               # Wrap around in search

[files]
follow_symlinks = true
auto_detect_format = true
supported_extensions = [".log", ".txt", ".json", ".out"]
```

---

## 13. Testing Strategy

### Unit Tests

```rust
// tests/unit/log_parsing.rs

#[test]
fn test_level_detection() {
    assert_eq!(detect_level("[INFO] Starting..."), Level::Info);
    assert_eq!(detect_level("2024-01-01 ERROR: failed"), Level::Error);
    assert_eq!(detect_level("WARN - low memory"), Level::Warn);
}

#[test]
fn test_timestamp_parsing() {
    let ts = parse_timestamp("2024-01-15T10:30:00.123Z").unwrap();
    assert_eq!(ts.date().year(), 2024);

    let ts = parse_timestamp("15/Jan/2024:10:30:00 +0000").unwrap();
    assert_eq!(ts.date().month(), 1);
}

#[test]
fn test_line_index_offsets() {
    let index = LineIndex::build("test.log").unwrap();
    assert_eq!(index.get_offset(0).unwrap(), 0);
    assert!(index.get_offset(1000).is_some());
}
```

### Integration Tests

```rust
// tests/integration.rs

#[tokio::test]
async fn test_live_tail() {
    let temp_file = NamedTempFile::new().unwrap();
    let mut viewer = LogViewer::new(temp_file.path()).unwrap();

    // Write initial content
    writeln!(temp_file, "Line 1");
    viewer.wait_for_line(1).await.unwrap();

    // Append content
    writeln!(temp_file, "Line 2");
    viewer.wait_for_line(2).await.unwrap();
}

#[tokio::test]
async fn test_search_highlighting() {
    let viewer = LogViewer::new("test.log").unwrap();
    viewer.search("ERROR").unwrap();

    let highlights = viewer.get_highlights(0..100);
    assert!(highlights.iter().any(|h| h.line == 42));
}
```

### Property-Based Tests

```rust
#[test]
fn test_log_level_detection_fuzz() {
    use proptest::prelude::*;

    proptest! {
        #[test]
        fn test_any_text_has_level(text: String) {
            let level = detect_level(&text);
            assert!(matches!(level, Level::Debug | Level::Info
                           | Level::Warn | Level::Error
                           | Level::Fatal | Level::Unknown));
        }
    }
}
```

### Performance Benchmarks

```rust
// benches/performance.rs

#[tokio::main]
async fn benchmark() {
    // Create test file
    let file = generate_log_file(1_000_000); // 1M lines

    let start = Instant::now();
    let viewer = LogViewer::new(&file).unwrap();
    let index_time = start.elapsed();

    let start = Instant::now();
    viewer.scroll_to_line(500_000);
    let scroll_time = start.elapsed();

    let start = Instant::now();
    viewer.search("ERROR.*timeout");
    let search_time = start.elapsed();

    println!("Index: {:?}, Scroll: {:?}, Search: {:?}",
             index_time, scroll_time, search_time);
}
```

### Fuzz Testing

```rust
// fuzz/fuzz_targets/log_parser.rs

#![no_main]
use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    if let Ok(text) = std::str::from_utf8(data) {
        let _ = detect_level(text);
        let _ = parse_timestamp(text);
    }
});
```

---

## 14. Alternative Crate Recommendations

### Alternative TUI Frameworks

| Crate | Pros | Cons | Best For |
|-------|------|------|----------|
| **ratatui** | Active, immediate mode, ecosystem | No built-in page scroll | THIS PROJECT |
| **cursive** | Simple API, built-in views | No async, dated | Simple menus |
| **tuirealm** | React-like, components | New, smaller ecosystem | Web-like apps |
| **egui** | GPU rendering | Heavy, not pure terminal | Modern terminals |

### File I/O Alternatives

| Crate | Use Case |
|-------|----------|
| **memmap2** | Static file access (watch out for SIGBUS!) |
| **tokio::fs** | Async streaming |
| **BufReader** | Line-by-line reading |
| **streaming-iterator** | Memory-efficient iteration |

### Search Alternatives

| Crate | Use Case |
|-------|----------|
| **regex** | Standard regex (this project) |
| **fancy-regex** | PCRE-like features |
| **grep-searcher** | Memory-mapped grep |
| **tantivy** | Full-text search index |

### File Watching Alternatives

| Crate | Platform | Notes |
|-------|----------|-------|
| **notify** | All | Simple, async support |
| **notify-debouncer** | All | Debounced events |
| **hotwatch** | All | Simpler API |
| **inotify** | Linux only | Fastest on Linux |

---

## 15. Command Line Interface

### Usage

```console
$ logprobe [OPTIONS] [FILE]

Positional Arguments:
  FILE              Log file to open

Options:
  -f, --follow      Follow file changes (tail -f mode)
  -n, --lines N     Start at last N lines
  -c, --config FILE Custom config file
  --theme THEME      Color theme (dark|light)
  --no-line-numbers  Hide line numbers
  -h, --help        Show help
  -V, --version     Show version

Filter Options:
  -l, --level LEVELS    Filter by levels (e.g., ERROR,WARN)
  -t, --time-from T    Start time (ISO 8601)
  -T, --time-to T      End time (ISO 8601)
  -g, --grep PATTERN   Initial search pattern

Examples:
  $ logprobe app.log
  $ logprobe -f /var/log/syslog
  $ logprobe -l ERROR,WARN -g "timeout" debug.log
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (normal exit) |
| 1 | Error (file not found, invalid args) |
| 2 | Signal interrupt (Ctrl+C) |

---

## 16. Future Enhancements (Post-MVP)

| Feature | Priority | Complexity |
|---------|----------|------------|
| **Multiple files** | P1 | Medium |
| **SQLite query interface** | P2 | High |
| **JSON/JSONL pretty print** | P1 | Low |
| **Histogram view** | P2 | Medium |
| **Network log sources** | P3 | High |
| **Plugin system** | P3 | Very High |
| **Remote mode (SSH)** | P3 | Very High |

---

*Plan created: 2026-04-16*
*Last updated: 2026-04-16 (enhanced with implementation notes)*