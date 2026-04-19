# GitViz

Interactive Terminal UI Git History Visualizer

## Overview

GitViz is a standalone Python CLI tool that visualizes git commit history as an interactive ASCII graph in the terminal. Key differentiator: **zero external git dependencies** - parses the `.git` directory directly.

## Features

- Real-time ASCII branch visualization with proper branching/merging lines
- Commit details: hash (short), author, date, message preview
- Keyboard navigation (arrows, vim keys, page up/down)
- Mouse support (click to select, scroll)
- Search and filter by author/date
- Color-coded branches and commit types
- Repository path discovery (auto-detect from current directory)
- Diff viewer for commit changes

## Installation

### Prerequisites

- Python 3.11 or higher
- pip or uv

### From Source

```bash
# Clone the repository
git clone https://github.com/gitviz/gitviz.git
cd gitviz

# Install with uv (recommended)
uv sync

# Or install with pip
pip install -e .
```

### Using pip directly

```bash
pip install gitviz
```

## Usage

### Basic Usage

Run gitviz in any git repository directory:

```bash
gitviz
```

### Specify Repository Path

```bash
gitviz /path/to/repo
```

### Limit Commits

```bash
gitviz --max-commits 100
```

### Focus on Specific Branch

```bash
gitviz --branch main
gitviz -b feature/login
```

### Filter by Date

```bash
gitviz --since 2024-01-01
```

### Show All Branches

```bash
gitviz --all
```

### Disable Colors

```bash
gitviz --no-color
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `j` / `↓` | Move selection down |
| `k` / `↑` | Move selection up |
| `g` | Jump to first commit |
| `G` | Jump to last commit |
| `PageUp` | Scroll up one page |
| `PageDown` | Scroll down one page |
| `h` / `←` | Scroll graph left |
| `l` / `→` | Scroll graph right |
| `/` | Open search |
| `f` | Open filter menu |
| `d` | Show diff for selected |
| `c` | Copy commit hash |
| `Esc` | Close dialogs, clear search |
| `q` | Quit |

## Mouse Interactions

| Action | Result |
|--------|--------|
| Click on commit | Select commit |
| Scroll up/down | Navigate commits |
| Double-click | Show diff |

## Search & Filter

### Search Mode (press `/`)

Fuzzy match on:
- Commit hash
- Author name
- Author email
- Message

Press `Esc` to clear search.

### Filter Mode (press `f`)

Filter by:
- `author:name` - Match author name
- `author:email` - Match author email
- `date:2024-01` - Commits from January 2024
- `date:>2024-01-01` - After given date
- `date:<2024-12-31` - Before given date
- `branch:main` - On or merged into branch
- `message:fix` - Match message

Multiple filters can be combined.

## Configuration

No configuration files required. GitViz works out of the box with sensible defaults.

## Architecture

GitViz consists of the following layers:

1. **Parser Layer** - Pure Python git object parsing (loose objects, pack files, refs)
2. **Model Layer** - Data structures (Commit, Branch, Repository)
3. **Graph Layer** - Layout algorithm and ASCII rendering
4. **UI Layer** - Textual TUI application

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=gitviz

# Run specific test file
pytest tests/unit/test_commit.py
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
mypy src/gitviz/
```

## Requirements

- Python 3.11+
- Textual >= 0.7.0

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Inspired by `git log --graph`
- Built with [Textual](https://textual.textualize.io/)
- Layout algorithm based on [pvigier/gitgraph](https://github.com/pvigier/gitgraph)
