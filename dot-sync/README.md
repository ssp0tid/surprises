# dot-sync

CLI tool for dotfiles synchronization across multiple machines.

## Features

- **Track dotfiles**: Add files and directories to track
- **Git-backed storage**: Version control your dotfiles with Git
- **Encryption support**: Encrypt sensitive files with AES-256-GCM
- **Machine-specific configs**: Manage different configurations per machine
- **Network sharing**: Share dotfiles via network or mount point
- **Change detection**: Track file modifications with checksums

## Installation

### From source

```bash
# Clone the repository
git clone <repo-url>
cd dot-sync

# Install dependencies
npm install

# Build TypeScript
npm run build

# Link globally
npm link
```

### Usage

```bash
# Initialize a new dot-sync repository
dot-sync init [name]

# Add files to tracking
dot-sync add ~/.bashrc ~/.zshrc
dot-sync add --glob "**/.config/**"

# Remove files from tracking
dot-sync remove ~/.bashrc
dot-sync remove --keep ~/.secret  # Keep local file after removal

# Sync dotfiles across machines
dot-sync sync
dot-sync sync --machine work
dot-sync sync --dry-run

# Check status
dot-sync status
dot-sync status --verbose

# Share dotfiles over network
dot-sync share --host          # Host mode
dot-sync share --connect host:8765  # Client mode

# Machine management
dot-sync machine --action list
dot-sync machine --action add --name work

# Configuration
dot-sync config --action list
dot-sync config --action set --key sourceDir --value ~/dotfiles
dot-sync config --action get --key repoUrl
```

## Configuration

Configuration is stored in `~/.config/dot-sync/` (or equivalent platform path).

### Default Config

```json
{
  "sourceDir": "~/dotfiles",
  "repoUrl": "",
  "branch": "main",
  "encryption": {
    "enabled": false,
    "algorithm": "aes-256-gcm",
    "kdf": "pbkdf2",
    "iterations": 100000,
    "keyLength": 32
  },
  "git": {
    "authorName": "<username>",
    "authorEmail": "",
    "commitMessage": "Update dotfiles via dot-sync",
    "autoCommitInterval": 0
  }
}
```

### Encryption

To enable encryption:

```bash
dot-sync config --action set --key encryption.enabled --value true
```

### Git Integration

Configure Git author:

```bash
dot-sync config --action set --key git.authorName --value "Your Name"
dot-sync config --action set --key git.authorEmail --value "your@email.com"
```

Set up a repository:

```bash
dot-sync config --action set --key repoUrl --value "https://github.com/user/dotfiles.git"
```

## Commands

| Command | Description |
|---------|-------------|
| `init [name]` | Initialize a new dot-sync repository |
| `add <files...>` | Add files to tracking |
| `remove <files...>` | Remove files from tracking |
| `sync` | Sync tracked dotfiles |
| `status` | Show status of tracked files |
| `share` | Share dotfiles via network |
| `machine` | Manage machine configurations |
| `config` | Manage configuration |

## Options

### add
- `-g, --glob <pattern>` - Add files matching glob pattern
- `-e, --exclude <pattern>` - Exclude files matching pattern

### remove
- `-k, --keep` - Keep local files after removal

### sync
- `-m, --machine <name>` - Target machine name
- `-d, --dry-run` - Show changes without applying
- `-f, --force` - Force overwrite local changes

### status
- `-v, --verbose` - Show detailed status
- `-s, --short` - Show short format

### share
- `-p, --port <port>` - Port for sharing (default: 8765)
- `--host` - Act as host for sharing
- `--connect <address>` - Connect to shared dotfiles

## Architecture

```
src/
├── cli/          # CLI commands
├── config/       # Configuration management
├── core/         # Sync engine, encryption, git manager
├── storage/      # File store and manifest management
├── types/        # TypeScript interfaces
└── utils/        # Logger, path utilities, checksums
```

## License

MIT
