# ShellMem

A terminal shell history manager with fuzzy search, tagging, and favorites.

## Features

- **Shell History Parsing**: Supports bash, zsh, and fish shell history formats
- **Fuzzy Search**: Fast fuzzy matching across your entire command history
- **Tagging**: Organize commands with custom tags and colors
- **Favorites**: Bookmark frequently used commands
- **Deduplication**: Remove duplicate commands from your history
- **Sync**: Background file watching to keep your history in sync
- **Import/Export**: Import from shell history files or export to JSON/CSV
- **Interactive TUI**: Full terminal UI for browsing and managing history

## Project Structure

```
shellmem/
├── Cargo.toml              # Workspace manifest
├── shellmem-core/         # Core library (reusable)
│   └── src/
│       ├── lib.rs         # Public API exports
│       ├── config.rs      # Configuration management
│       ├── error.rs       # Error types
│       ├── models.rs      # Data structures
│       ├── parser/        # Shell history parsers
│       │   ├── bash.rs
│       │   ├── zsh.rs
│       │   └── fish.rs
│       ├── search/        # Fuzzy search engine
│       ├── storage/       # SQLite database layer
│       │   ├── migrations.rs
│       │   └── sqlite.rs
│       └── sync/         # File watcher for background sync
├── shellmem-cli/         # CLI application
│   └── src/main.rs
├── shellmem-tui/         # Terminal UI application
│   ├── Cargo.toml
│   └── src/
│       ├── main.rs
│       ├── app.rs        # Application state
│       ├── ui.rs         # UI rendering
│       ├── input.rs      # Input handling
│       └── widgets/      # Custom widgets
└── README.md
```

## Installation

### Prerequisites

- **Rust 1.70+** - Install via [rustup](https://rustup.rs/)

### Build from Source

```bash
# Clone the repository
git clone https://github.com/shellmem/shellmem.git
cd shellmem

# Build the project
cargo build --release

# Install both CLI and TUI binaries
cp target/release/shellmem ~/.cargo/bin/
cp target/release/shellmem-tui ~/.cargo/bin/
```

Or add `~/.cargo/bin` to your PATH and run from the target directory.

### Quick Build for Development

```bash
# Debug build (faster)
cargo build

# Run CLI
cargo run --package shellmem-cli -- --help

# Run TUI
cargo run --package shellmem-tui
```

## Quick Start

```bash
# Import your shell history
shellmem import bash ~/.bash_history
shellmem import zsh ~/.zsh_history
shellmem import fish ~/.local/share/fish/fish_history

# Search your history
shellmem search "git commit"

# List recent commands
shellmem list

# Start the interactive TUI
shellmem tui
```

## Configuration

ShellMem looks for config at `$XDG_CONFIG_HOME/shellmem/config.toml` (typically `~/.config/shellmem/config.toml`).

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|--------------|
| `home` | string | `~/.local/share/shellmem` | Data directory |
| `shells.bash.history_file` | string | `~/.bash_history` | Bash history path |
| `shells.zsh.history_file` | string | `~/.zsh_history` | Zsh history path |
| `shells.fish.history_file` | string | `~/.local/share/fish/fish_history` | Fish history path |
| `sync.enabled` | bool | `false` | Enable background sync |
| `sync.interval` | seconds | 60 | Sync interval |
| `search.fuzzy` | bool | `true` | Use fuzzy search by default |
| `search.default_limit` | number | 50 | Default result limit |
| `search.max_results` | number | 1000 | Maximum results |

### Example Config

```toml
[shellmem]
home = "~/.local/share/shellmem"

[shells.bash]
history_file = "~/.bash_history"
parser = "bash"

[shells.zsh]
history_file = "~/.zsh_history"
parser = "zsh"

[shells.fish]
history_file = "~/.local/share/fish/fish_history"
parser = "fish"

[sync]
enabled = true
interval = 30

[search]
fuzzy = true
default_limit = 100
max_results = 5000

[tags]
[[tags]]
name = "docker"
color = "#2496ed"
[[tags]]
name = "git"
color = "#f05032"
```

## CLI Commands

### Search

```bash
shellmem search "git commit"           # Fuzzy search
shellmem search --exact "docker ps"   # Exact match
shellmem search --limit 20             # Limit results
shellmem search --shell bash           # Filter by shell
shellmem search --favorites-only       # Search only favorites
```

### List

```bash
shellmem list                          # Recent 50 commands
shellmem list --limit 20               # Limit to 20
shellmem list --from "2024-01-01"     # Filter by date
shellmem list --to "2024-12-31"
shellmem list --shell bash             # Filter by shell
```

### Favorites

```bash
shellmem fav add <id>                  # Add to favorites
shellmem fav remove <id>              # Remove from favorites
```

### Tags

```bash
shellmem tag create "docker" --color "#2496ed"  # Create tag
shellmem tag add <command-id> <tag-name>        # Tag a command
shellmem tag remove <command-id> <tag-name>     # Remove tag
shellmem tag list                             # List all tags
```

### Import/Export

```bash
shellmem import bash ~/.bash_history
shellmem import zsh ~/.zsh_history
shellmem import fish ~/.local/share/fish/fish_history
shellmem export json history.json
shellmem export csv history.csv
```

### Deduplication

```bash
shellmem dedupe --dry-run   # Preview without applying
shellmem dedupe            # Remove duplicates
```

### Sync

```bash
shellmem sync start    # Start background sync
shellmem sync stop     # Stop background sync
shellmem sync status   # Show sync status
```

### Config

```bash
shellmem config get fuzzy
shellmem config set interval 30
shellmem config show
```

### Shell Completions

```bash
shellmem completion bash > ~/.bash_completion.d/shellmem
shellmem completion zsh > ~/.zsh/completions/_shellmem
shellmem completion fish > ~/.config/fish/completions/shellmem.fish
```

### TUI

```bash
shellmem tui    # Start interactive TUI
```

## TUI Keybindings

| Key | Action |
|-----|--------|
| `/` | Open search mode |
| `Enter` | Print selected command |
| `c` | Copy command to clipboard |
| `f` | Toggle favorite |
| `t` | Toggle tag menu |
| `j` or `Down` | Move down |
| `k` or `Up` | Move up |
| `Tab` | Switch between list and detail panel |
| `Ctrl+r` | Refresh commands |
| `Ctrl+d` | Delete selected entry |
| `Ctrl+f` | Toggle favorites filter |
| `Ctrl+t` | Toggle tag menu |
| `Esc` | Back/close menus |
| `q` | Quit |

## Supported Shells

- **Bash** (`~/.bash_history`)
- **Zsh** (`~/.zsh_history`)
- **Fish** (`~/.local/share/fish/fish_history`)

## Shell Integration

### Fish Shell

Create `~/.config/fish/functions/shellmem.fish`:

```fish
function shellmem
    if count $argv > /dev/null
        command shellmem $argv
    else
        command shellmem tui
    end
end
```

### Zsh

Add to your `~/.zshrc`:

```zsh
HISTFILE=~/.zsh_history
```

### Bash

No special configuration needed - history is stored in `~/.bash_history`.

## Data Storage

ShellMem stores data in:
- **Database**: `~/.local/share/shellmem/shellmem.db`
- **Config**: `~/.config/shellmem/config.toml`

## Development

### Running Tests

```bash
cargo test --workspace
```

### Code Format

```bash
cargo fmt
```

### Linting

```bash
cargo clippy --workspace
```

## License

Licensed under either of:
- MIT license ([LICENSE-MIT](LICENSE-MIT) or http://opensource.org/licenses/MIT)
- Apache License 2.0 ([LICENSE-APACHE](LICENSE-APACHE) or http://www.apache.org/licenses/LICENSE-2.0)

at your option.

## Contributing

Contributions are welcome. Please open an issue or pull request on GitHub.

## Troubleshooting

### No history found

Run import to load your shell history:

```bash
shellmem import bash ~/.bash_history
```

### Slow search on large history

Enable background sync to keep your indexed history up to date, or increase `search.max_results`:

```toml
[search]
max_results = 5000
```

### TUI not displaying correctly

Ensure your terminal supports ANSI colors. Check that your terminal emulator supports 256 colors.

### Config file not found

Create the config directory:
```bash
mkdir -p ~/.config/shellmem
```