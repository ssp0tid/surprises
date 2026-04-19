# ShellMem - Terminal Shell History Manager

## Project Overview

**Project Name**: ShellMem
**Type**: CLI/TUI Application
**Language**: Rust (recommended) or Go
**Core Functionality**: Index, search, and organize command history from bash/zsh/fish shells with full-text fuzzy search, tagging, bookmarking, deduplication, and time filtering.
**Target Users**: Developers, system administrators, power users who work extensively in the terminal.

---

## 1. Shell History Format Research

### 1.1 Bash (`~/.bash_history`)
- **Location**: `$HISTFILE` (default: `~/.bash_history`)
- **Format**: Plain text, one command per line
- **Timestamp**: Optional - encoded as comment `#<unix_timestamp>` immediately before command when `HISTTIMEFORMAT` is set
- **Multiline**: Multiple lines joined with backslash `\` or newlines preserved
- **Edge Cases**: 
  - Commands with leading spaces ignored if `HISTCONTROL=ignorespace`
  - Duplicates removed if `HISTCONTROL=erasedups`

### 1.2 Zsh (`~/.zsh_history`)
- **Location**: `$HISTFILE` (default: `~/.zsh_history`)
- **Format**: `: <begin_time>:<elapsed_seconds>;<command>` (with EXTENDED_HISTORY)
- **Format**: `<command>` only (with INC_APPEND_HISTORY)
- **Begin time**: Unix timestamp
- **Elapsed seconds**: Time command ran (optional)
- **Edge Cases**:
  - Empty commands stored as `: :0;`
  - Multi-line commands use `\n` escapes

### 1.3 Fish (`~/.local/share/fish/fish_history`)
- **Location**: `~/.local/share/fish/fish_history` (configurable via `fish_history` var)
- **Format**: YAML-like
```
- cmd: git commit -m "fix bug"
  when: 1708784400
  cwd: /home/user/project
  status: 0
```
- **Fields**: `cmd`, `when` (Unix timestamp), `cwd`, `status`
- **Edge Cases**: Invalid lines ignored, partial writes on crash

### 1.4 Other Shells
- **tcsh**: `~/.history` or `~/.tcshrc` - rarely used
- **dash/ash**: No persistent history by default
- **PowerShell**: `Get-History` cmdlet - JSON exportable

---

## 2. File Structure

```
shellmem/
├── Cargo.toml                    # Rust project manifest
├── shellmem-core/               # Core library (no TUI/CLI dependencies)
│   ├── Cargo.toml
│   ├── src/
│   │   ├── lib.rs             # Public API exports
│   │   ├── models.rs          # Data structures
│   │   ├── history.rs        # History entry types
│   │   ├── parser/           # Shell history parsers
│   │   │   ├── mod.rs
│   │   │   ├── bash.rs
│   │   │   ├── zsh.rs
│   │   │   └── fish.rs
│   │   ├── storage/          # Database layer
│   │   │   ├── mod.rs
│   │   │   ├── sqlite.rs
│   │   │   └── migrations.rs
│   │   ├── search/          # Fuzzy search
│   │   │   └── mod.rs
│   │   └── sync/            # Background sync
│   │       └── mod.rs
├── shellmem-cli/             # CLI interface
│   ├── Cargo.toml
│   └── src/
│       └── main.rs
├── shellmem-tui/            # TUI interface
│   ├── Cargo.toml
│   └── src/
│       ├── main.rs
│       ├── app.rs           # App state
│       ├── ui.rs            # UI components
│       ├── widgets/         # Custom widgets
│       └── input.rs         # Input handling
├── tests/
├── docs/
└── README.md
```

---

## 3. Dependencies

### 3.1 Core Dependencies
| Crate | Version | Purpose |
|-------|---------|---------|
| `rusqlite` | `0.39` | Embedded SQLite database |
| `fuzzy-matcher` | `0.21` | Fuzzy string matching |
| `serde` | `1.0` | Serialization |
| `serde_json` | `1.0` | JSON handling |
| `chrono` | `0.4` | Date/time handling |
| `tokio` | `1.0` | Async runtime |
| `thiserror` | `1.0` | Error handling |

### 3.2 CLI Dependencies
| Crate | Version | Purpose |
|-------|---------|---------|
| `clap` | `5.0` | CLI argument parsing |
| `clap_complete` | `5.0` | Shell completions |

### 3.3 TUI Dependencies
| Crate | Version | Purpose |
|-------|---------|---------|
| `ratatui` | `0.30` | Terminal UI framework |
| `crossterm` | `0.29` | Terminal input/output |
| `color-eyre` | `0.6` | Pretty error reporting |

### 3.4 Recommended Alternatives
- **Fuzzy search**: `nucleo` (faster) or `frizbee` (SIMD-based)
- **Database**: `sled` (embedded KV), `redb` (pure Rust)

---

## 4. Database Schema

### 4.1 Tables

```sql
-- Core command history
CREATE TABLE commands (
    id              INTEGER PRIMARY KEY,
    command         TEXT NOT NULL,
    shell           TEXT NOT NULL,          -- 'bash', 'zsh', 'fish'
    source_file     TEXT NOT NULL,          -- Original history file path
    source_id      TEXT,                 -- Original line/entry ID
    timestamp      INTEGER NOT NULL,     -- Unix timestamp
    duration_ms    INTEGER,              -- Command duration (zsh)
    working_dir    TEXT,                 -- Working directory (fish)
    exit_status    INTEGER,               -- Exit code
    is_favorite    BOOLEAN DEFAULT FALSE,
    is_deleted     BOOLEAN DEFAULT FALSE,
    created_at     INTEGER NOT NULL,
    updated_at     INTEGER NOT NULL,
    hash           TEXT NOT NULL UNIQUE -- For deduplication
);

-- Tags for commands
CREATE TABLE tags (
    id       INTEGER PRIMARY KEY,
    name     TEXT NOT NULL UNIQUE,
    color    TEXT DEFAULT '#ffffff'
);

-- Many-to-many: commands <-> tags
CREATE TABLE command_tags (
    command_id INTEGER REFERENCES commands(id),
    tag_id    INTEGER REFERENCES tags(id),
    PRIMARY KEY (command_id, tag_id)
);

-- Sync metadata
CREATE TABLE sync_state (
    shell        TEXT PRIMARY KEY,
    source_file  TEXT NOT NULL,
    last_pos    INTEGER NOT NULL,
    last_hash  TEXT
);

-- User preferences
CREATE TABLE settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Indexes
CREATE INDEX idx_commands_timestamp ON commands(timestamp DESC);
CREATE INDEX idx_commands_hash ON commands(hash);
CREATE INDEX idx_commands_favorite ON commands(is_favorite) WHERE is_favorite = TRUE;
CREATE INDEX idx_command_tags_command ON command_tags(command_id);
CREATE INDEX idx_command_tags_tag ON command_tags(tag_id);
```

---

## 5. API Design

### 5.1 Public API (shellmem-core)

```rust
// Models
pub struct Command {
    pub id: i64,
    pub command: String,
    pub shell: Shell,
    pub timestamp: DateTime<Utc>,
    pub duration_ms: Option<i64>,
    pub working_dir: Option<String>,
    pub exit_status: Option<i32>,
    pub is_favorite: bool,
    pub tags: Vec<Tag>,
}

pub enum Shell {
    Bash,
    Zsh,
    Fish,
}

pub struct Tag {
    pub id: i64,
    pub name: String,
    pub color: String,
}

pub struct SearchOptions {
    pub query: String,
    pub fuzzy: bool,
    pub shells: Vec<Shell>,
    pub from_time: Option<DateTime<Utc>>,
    pub to_time: Option<DateTime<Utc>,
    pub tags: Vec<i64>,
    pub favorites_only: bool,
    pub limit: i64,
    pub offset: i64,
}

// Core trait
pub trait HistoryStore {
    fn add_command(&mut self, cmd: Command) -> Result<i64>;
    fn get_command(&self, id: i64) -> Result<Option<Command>>;
    fn search(&self, options: SearchOptions) -> Result<Vec<Command>>;
    fn set_favorite(&self, id: i64, favorite: bool) -> Result<()>;
    fn add_tag(&self, command_id: i64, tag_id: i64) -> Result<()>;
    fn remove_tag(&self, command_id: i64, tag_id: i64) -> Result<()>;
    fn dedupe(&mut self) -> Result<DedupeReport>;
    fn set_deleted(&self, id: i64, deleted: bool) -> Result<()>;
}

// Background sync
pub trait HistoryWatcher {
    fn watch(&self, shell: Shell, path: &Path) -> Result<()>;
    fn get_changes(&self, shell: Shell) -> Result<Vec<Command>>;
}

// Import/Export
pub fn import_from_file(path: &Path, shell: Shell) -> Result<Vec<Command>>;
pub fn export_to_json(commands: &[Command], writer: impl Write) -> Result<()>;
pub fn export_to_csv(commands: &[Command], writer: impl Write) -> Result<()>;
```

### 5.2 CLI Commands

```bash
# Search (fuzzy by default)
shellmem search "git commit"
shellmem search --exact "docker ps"

# List recent
shellmem list --limit 20
shellmem list --from "2024-01-01" --to "2024-12-31"

# Favorites
shellmem fav                           # List favorites
shellmem fav add <id>                  # Add to favorites
shellmem fav remove <id>               # Remove from favorites

# Tags
shellmem tag create "docker" --color "#2496ed"
shellmem tag add <command-id> <tag-id>
shellmem tag remove <command-id> <tag-id>
shellmem tag list

# Import/Export
shellmem import bash ~/.bash_history
shellmem import zsh ~/.zsh_history
shellmem import fish ~/.local/share/fish/fish_history
shellmem export json history.json
shellmem export csv history.csv

# Deduplication
shellmem dedupe --dry-run
shellmem dedupe

# Sync
shellmem sync start
shellmem sync status
shellmem sync stop

# Settings
shellmem config get shellmem.home
shellmem config set shellmem.home /custom/path

# TUI
shellmem tui
```

### 5.3 TUI Keybindings

| Key | Action |
|-----|--------|
| `/` | Open search |
| `Enter` | Execute selected command |
| `c` | Copy command to clipboard |
| `f` | Toggle favorite |
| `t` | Add/remove tag |
| `Ctrl+r` | Refresh |
| `Ctrl+d` | Delete entry |
| `Esc` | Back/close |
| `q` | Quit |
| `Tab` | Switch panel |
| `Ctrl+f` | Filter by favorite |
| `Ctrl+t` | Filter by tag |

---

## 6. Implementation Details

### 6.1 History Parsing

```rust
// parser/bash.rs
pub fn parse_history(content: &str) -> Vec<Command> {
    let mut commands = Vec::new();
    let mut lines = content.lines().peekable();
    let mut pending_timestamp: Option<i64> = None;

    while let Some(line) = lines.next() {
        // Timestamp line: #<unix_timestamp>
        if line.starts_with('#') && line[1..].chars().all(|c| c.is_ascii_digit()) {
            pending_timestamp = line[1..].parse().ok();
            continue;
        }

        let cmd = line.trim();
        if !cmd.is_empty() {
            commands.push(Command {
                command: cmd.to_string(),
                timestamp: pending_timestamp.map_or(Utc::now(), |ts| DateTime::from_timestamp(ts, 0).unwrap()),
                ..Default::default()
            });
            pending_timestamp = None;
        }
    }
    commands
}
```

### 6.2 Fuzzy Search Implementation

```rust
use fuzzy_matcher::skim::SkimMatcherV2;
use fuzzy_matcher::FuzzyMatcher;

pub fn fuzzy_search(query: &str, commands: &[Command]) -> Vec<(i64, i64, Vec<usize>)> {
    let matcher = SkimMatcherV2::default();
    commands
        .iter()
        .filter_map(|cmd| {
            matcher.fuzzy_indices(&cmd.command, query)
                .map(|(score, indices)| (cmd.id, score, indices))
        })
        .collect::<Vec<_>>()
        .sort_by(|a, b| b.1.cmp(&a.1)); // Sort by score descending
}
```

### 6.3 Background Sync (File Watching)

```rust
use notify::{RecommendedWatcher, RecursiveMode, Watcher};
use std::sync::mpsc;

pub fn start_watcher(shell: Shell, path: &Path) -> notify::Result<notify::RecommendedWatcher> {
    let (tx, rx) = mpsc::channel();
    
    let mut watcher = RecommendedWatcher::new(move |res: Result<notify::Event>| {
        if let Ok(event) = res {
            tx.send(event).unwrap();
        }
    }, notify::Config::default())?;
    
    watcher.watch(path, RecursiveMode::NonRecursive)?;
    
    // Spawn handler in background
    std::thread::spawn(move || {
        while let Ok(event) = rx.recv() {
            // Handle modify/create events, re-parse new content
            // Update database
        }
    });
    
    Ok(watcher)
}
```

### 6.4 TUI Application State

```rust
pub struct App {
    pub commands: Vec<Command>,
    pub filtered: Vec<Command>,
    pub search_query: String,
    pub selected: usize,
    pub mode: AppMode,
    pub filters: Filters,
    pub tags: Vec<Tag>,
}

pub enum AppMode {
    Browse,
    Search,
    TagSelect,
    CommandDetail,
}

pub struct Filters {
    pub from_time: Option<DateTime<Utc>>,
    pub to_time: Option<DateTime<Utc>>,
    pub shells: Vec<Shell>,
    pub tags: Vec<i64>,
    pub favorites_only: bool,
}
```

---

## 7. Error Handling

### 7.1 Error Types

```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ShellmemError {
    #[error("Database error: {0}")]
    Database(#[from] rusqlite::Error),
    
    #[error("Parse error for {shell}: {message}")]
    Parse { shell: Shell, message: String },
    
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    
    #[error("Command not found: {0}")]
    NotFound(i64),
    
    #[error("Invalid timestamp: {0}")]
    InvalidTimestamp(String),
    
    #[error("Sync error: {0}")]
    Sync(String),
    
    #[error("Export error: {0}")]
    Export(String),
}
```

### 7.2 Recovery Strategies

| Error | Recovery |
|-------|---------|
| Database locked | Retry with exponential backoff (max 3 attempts) |
| Invalid history format | Skip line, log warning, continue |
| File not found | Create empty file or skip sync |
| Corrupt database | Backup and recreate |
| Sync conflict | Use latest timestamp wins |

---

## 8. Edge Cases

### 8.1 History File Edge Cases
- **Empty file**: Create empty database, return OK
- **Binary content**: Detect and skip with warning
- **Huge file (>1GB)**: Stream parse, batch insert
- **Partial write**: Detect incomplete lines, wait/retry
- **Concurrent write**: Use file locking or watch for stable state
- **Encoding issues**: Support UTF-8, Latin-1 fallback

### 8.2 Search Edge Cases
- **Empty query**: Return recent (limit applied)
- **No matches**: Return empty, show "No results"
- **Special chars**: Escape regex, use literal match
- **Unicode**: Normalize before matching
- **Very long command**: Limit display, full on detail

### 8.3 Deduplication Edge Cases
- **Same command, different timestamp**: Keep most recent
- **Same command, same timestamp**: Keep arbitrary one
- **Unicode differences**: Normalize before comparison

### 8.4 Import Edge Cases
- **Duplicate imports**: Use hash collision detection
- **Unknown shell format**: Error with supported formats list
- **Partial import**: Commit partial, report failures

---

## 9. Configuration

### 9.1 Config File Location
- `$XDG_CONFIG_HOME/shellmem/config.toml` (Linux)
- `~/Library/Application Support/shellmem/config.toml` (macOS)
- `%APPDATA%/shellmem/config.toml` (Windows)
- `~/.config/shellmem/config.toml` (fallback)

### 9.2 Config Format

```toml
[shellmem]
home = "~/.local/share/shellmem"

[shells]
bash = "~/.bash_history"
zsh = "~/.zsh_history"
fish = "~/.local/share/fish/fish_history"

[sync]
enabled = true
interval = 30  # seconds
watch = true

[search]
fuzzy = true
default_limit = 100
max_results = 1000

[ui]
theme = "default"
keybindings = "default"

[tags]
# Auto-generated tags
[[tags]]
name = "docker"
color = "#2496ed"
[[tags]]
name = "git"
color = "#f05032"
[[tags]]
name = "rust"
color = "#dea584"
```

---

## 10. Shell Integration

### 10.1 Fish Shell Integration

```fish
# ~/.config/fish/functions/shellmem.fish
function shellmem
    if count $argv > /dev/null
        command shellmem $argv
    else
        command shellmem tui
    end
end

# Share history with shellmem (fish 3.0+)
function fish_should_add_to_history
    # Allow shellmem to process all commands
    return 0
end
```

### 10.2 Zsh Integration

```zsh
# ~/.zshrc
# Share history with shellmem
HISTFILE=~/.zsh_history
```

---

## 11. Performance Considerations

| Operation | Target | Strategy |
|-----------|--------|----------|
| Initial import | 100k+ commands < 5s | Batch inserts (1000/batch) |
| Fuzzy search | < 100ms for 100k | Pre-filter with trie, use nucleo |
| File watch | < 1s latency | Inotify/FSEvents |
| Database size | < 10MB per 100k | JSON compression, optimize types |
| Memory | < 100MB idle | Lazy loading, LRU cache |

---

## 12. Testing Strategy

- **Unit tests**: Parser modules, search, models
- **Integration tests**: SQLite, file watching
- **Property tests**: Round-trip import/export
- **Benchmarks**: Search performance

---

## 13. Implementation Phases

### Phase 1: Core (Week 1-2)
- [ ] Project setup with workspace
- [ ] Database schema and migrations
- [ ] History parsers (bash, zsh, fish)
- [ ] Basic CLI with search/list

### Phase 2: Features (Week 3-4)
- [ ] Fuzzy search
- [ ] Tags and favorites
- [ ] Deduplication
- [ ] Import/export

### Phase 3: Sync (Week 5)
- [ ] Background file watcher
- [ ] Sync loop
- [ ] Config management

### Phase 4: TUI (Week 6-7)
- [ ] Basic TUI layout
- [ ] Search input
- [ ] Command list widget
- [ ] Keybindings

### Phase 5: Polish (Week 8)
- [ ] Error handling
- [ ] Edge cases
- [ ] Performance tuning
- [ ] Documentation

---

## 14. Future Enhancements

- **Cloud sync**: Server + mobile app
- **Command analytics**: Usage statistics
- **AI suggestions**: Command completion
- **Plugin system**: Custom workflows
- **Multiple machines**: Sync history across devices

---

## 15. References

- [Bash History Manual](https://www.gnu.org/software/bash/manual/html_node/Bash-History-Facilities.html)
- [Zsh History](http://zsh.sourceforge.net/Doc/Release/zsh_16.html)
- [Fish History](https://fishshell.com/docs/current/cmds/history.html)
- [ratatui](https://ratatui.rs/)
- [rusqlite](https://github.com/rusqlite/rusqlite)
- [fuzzy-matcher](https://github.com/skim-rs/fuzzy-matcher)