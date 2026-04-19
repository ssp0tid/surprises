# GitViz - Implementation Plan

**Interactive Terminal UI Git History Visualizer**

Version: 1.0.0  
Date: 2026-04-16  
Status: Implementation Plan

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Technology Stack](#technology-stack)
3. [File Structure](#file-structure)
4. [Core Data Models](#core-data-models)
5. [Module Architecture](#module-architecture)
6. [API Design](#api-design)
7. [Git Parser Implementation](#git-parser-implementation)
8. [Graph Rendering Algorithm](#graph-rendering-algorithm)
9. [UI/TUI Implementation](#uitui-implementation)
10. [User Interactions](#user-interactions)
11. [Error Handling](#error-handling)
12. [Edge Cases](#edge-cases)
13. [Dependencies](#dependencies)
14. [Testing Strategy](#testing-strategy)
15. [Implementation Phases](#implementation-phases)

---

## Executive Summary

GitViz is a standalone Python CLI tool that visualizes git commit history as an interactive ASCII graph in the terminal. Key differentiator: **zero external git dependencies** - parses the `.git` directory directly.

### Core Features
- Real-time ASCII branch visualization with proper branching/merging lines
- Commit details: hash (short), author, date, message preview
- Keyboard navigation (arrows, vim keys, page up/down)
- Mouse support (click to select, scroll)
- Search and filter by author/date
- Commit diff viewer on selection
- Color-coded branches and commit types
- Repository path discovery (auto-detect from current directory)

### Target Users
- Developers who prefer terminal-based workflows
- Users wanting quick git history visualization without git CLI
- Scripts/tools needing git history parsing without subprocess dependency

---

## Technology Stack

### TUI Framework: Textual (v0.7+)

**Why Textual over alternatives:**

| Library | Pros | Cons | Decision |
|---------|------|------|----------|
| **Textual** | Modern, reactive, 40+ widgets, CSS styling, async, built on Rich | Heavier than raw curses | **SELECTED** - Best developer experience, production-ready |
| Rich | Rich text formatting, fast | No interactive widgets | Foundation only |
| Urwid | Lightweight, mature | Older API, less features | Rejected - dated UX model |
| Prompt-toolkit | Good for CLIs | Not a full TUI framework | Rejected - lacks widget model |

**Textual Architecture:**
- Retained-mode rendering with dirty tracking
- Widget tree with CSS-like styling (TCSS)
- Reactive state management with `reactive` attributes
- Asyncio-native for non-blocking I/O
- 120 FPS rendering capability

### Pure Python Git Parser: Custom Implementation

Based on research of Dulwich (pure-Python git implementation), we implement:
- Loose object reading (`.git/objects/xx/xxx...`)
- Pack file parsing (`.git/objects/pack/*.pack`)
- Ref/resolution (`.git/HEAD`, `.git/refs/heads/*`)
- Commit object parsing (author, committer, parents, tree, message)

---

## File Structure

```
gitviz/
├── pyproject.toml                 # Package configuration
├── uv.lock                        # Dependency lock file (uv)
├── README.md                      # Project documentation
├── CHANGELOG.md                   # Version history
├── LICENSE                        # MIT License
│
├── src/
│   └── gitviz/
│       ├── __init__.py           # Package entry point
│       │                        #
│       ├── __main__.py           # CLI entry point
│       ├── cli.py                # CLI argument parsing
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── commit.py          # Commit dataclass
│       │   ├── branch.py          # Branch dataclass
│       │   ├── ref.py             # Ref (branch/tag/HEAD) models
│       │   └── repository.py      # Repository aggregate model
│       │
│       ├── parser/
│       │   ├── __init__.py
│       │   ├── base.py            # Object parser base class
│       │   ├── loose.py           # Loose object reading
│       │   ├── pack.py            # Pack file parsing
│       │   ├── commit.py          # Commit object parsing
│       │   ├── tree.py            # Tree object parsing
│       │   ├── ref_parser.py      # Ref resolution
│       │   └── repository_loader.py # Repository discovery/loading
│       │
│       ├── graph/
│       │   ├── __init__.py
│       │   ├── node.py            # Graph node representation
│       │   ├── layout.py          # Layout algorithm (pvigier-based)
│       │   ├── ascii_renderer.py  # ASCII character mapping
│       │   └── color.py           # Branch/commit coloring
│       │
│       ├── ui/
│       │   ├── __init__.py
│       │   ├── app.py             # Textual App main class
│       │   ├── screens/
│       │   │   ├── __init__.py
│       │   │   ├── main_screen.py # Main graph view
│       │   │   └── diff_screen.py # Diff viewer screen
│       │   ├── widgets/
│       │   │   ├── __init__.py
│       │   │   ├── graph_widget.py # Commit graph display
│       │   │   ├── commit_row.py  # Single commit line widget
│       │   │   ├── detail_panel.py # Commit details panel
│       │   │   ├── search_bar.py  # Search/filter input
│       │   │   └── status_bar.py  # Navigation hints, repo info
│       │   └── styles/
│       │       ├── __init__.py
│       │       └── theme.py       # Color theme definitions
│       │
│       ├── search/
│       │   ├── __init__.py
│       │   ├── filter_engine.py   # Filter compilation/execution
│       │   └── matcher.py         # Fuzzy/string matching
│       │
│       └── utils/
│           ├── __init__.py
│           ├── datetime_utils.py  # Date formatting/parsing
│           └── diff_utils.py      # Diff generation
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # Pytest fixtures
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_commit.py
│   │   ├── test_loose_parser.py
│   │   ├── test_pack_parser.py
│   │   ├── test_layout.py
│   │   └── test_graph_renderer.py
│   └── fixtures/
│       ├── simple_repo/          # Test git repository
│       ├── branched_repo/        # Repo with branches/merges
│       ├── packed_repo/          # Repo with pack files
│       └── shallow_repo/         # Shallow clone
│
└── scripts/
    └── generate_test_repos.py    # Script to create test fixtures
```

---

## Core Data Models

### Commit

```python
@dataclass
class Commit:
    """Represents a git commit object."""

    oid: bytes  # Full 20-byte SHA-1
    tree_oid: bytes
    parents: list[bytes]  # List of parent OIDs (empty for initial)
    author: Actor
    committer: Actor
    author_time: int  # Unix timestamp
    commit_time: int
    message: str
    encoding: str

    @property
    def short_oid(self) -> str:
        """First 7 characters of SHA-1."""
        return self.oid.hex()[:7]

    @property
    def is_merge(self) -> bool:
        """True if this commit has multiple parents."""
        return len(self.parents) > 1

    @property
    def short_message(self) -> str:
        """First line of commit message, truncated."""
        first_line = self.message.split('\n')[0]
        return first_line[:72] + '...' if len(first_line) > 72 else first_line
```

### Actor

```python
@dataclass
class Actor:
    """Represents a person (author or committer)."""

    name: str
    email: str

    def __str__(self) -> str:
        return f"{self.name} <{self.email}>"
```

### Branch

```python
@dataclass
class Branch:
    """Represents a git branch reference."""

    name: str  # e.g., "main", "feature/login"
    oid: bytes  # Points to this commit
    is_head: bool  # True if this is HEAD
    is_remote: bool  # True if remote branch
    is_current: bool  # True if this is the checked-out branch

    @property
    def full_name(self) -> str:
        if self.is_remote:
            return f"origin/{self.name}"
        return self.name
```

### Repository

```python
@dataclass
class Repository:
    """Represents a git repository with all its data."""

    path: Path  # Path to .git directory
    worktree: Path | None  # Working tree path (None for bare)
    commits: dict[bytes, Commit]  # OID -> Commit
    branches: list[Branch]
    tags: list[Tag]  # See Tag model below
    head: bytes  # Current HEAD commit OID

    def get_branch_for_commit(self, oid: bytes) -> Branch | None:
        """Find branch pointing to this commit."""

    def get_children(self, oid: bytes) -> list[bytes]:
        """Get commits that have this commit as parent."""
```

---

## Module Architecture

### Layer Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer                           │
│  (argparse, config loading, entry point)                   │
└────────────────────────┬───────────────────────────────────┘
                         │
┌────────────────────────▼───────────────────────────────────┐
│                     Parser Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐    │
│  │  Loose Obj  │  │  Pack File  │  │  Ref Resolver   │    │
│  │   Reader    │  │   Parser    │  │                 │    │
│  └─────────────┘  └─────────────┘  └─────────────────┘    │
│  ┌─────────────────────────────────────────────────┐      │
│  │            Repository Loader                     │      │
│  │  (Discovery, cache, incremental loading)         │      │
│  └─────────────────────────────────────────────────┘      │
└────────────────────────┬───────────────────────────────────┘
                         │
┌────────────────────────▼───────────────────────────────────┐
│                     Model Layer                            │
│     (Commit, Branch, Repository, GraphNode)                │
└────────────────────────┬───────────────────────────────────┘
                         │
┌────────────────────────▼───────────────────────────────────┐
│                     Graph Layer                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐    │
│  │   Layout    │  │    ASCII    │  │     Color      │    │
│  │  Algorithm  │  │  Renderer   │  │    Manager     │    │
│  └─────────────┘  └─────────────┘  └─────────────────┘    │
└────────────────────────┬───────────────────────────────────┘
                         │
┌────────────────────────▼───────────────────────────────────┐
│                      UI Layer                              │
│  ┌─────────────────────────────────────────────────┐      │
│  │               Textual Application                │      │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │      │
│  │  │  Graph   │  │  Detail  │  │  Search/     │   │      │
│  │  │  Widget  │  │  Panel   │  │  Filter Bar  │   │      │
│  │  └──────────┘  └──────────┘  └──────────────┘   │      │
│  └─────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Dependency Flow

```
cli.py ──────► parser/repository_loader.py ──────► parser/*.py
                     │
                     ▼
              models/repository.py
                     │
                     ▼
              graph/layout.py ──────► graph/ascii_renderer.py
                     │                        │
                     ▼                        ▼
              graph/node.py              graph/color.py
                     │
                     ▼
              ui/app.py ──────► ui/screens/*.py ──────► ui/widgets/*.py
```

---

## API Design

### Repository Loader API

```python
class RepositoryLoader:
    """Discovers and loads git repositories."""

    def discover(path: Path | None = None) -> Path | None:
        """
        Find .git directory starting from given path.
        Walks up directory tree if not found.
        Returns path to .git or None.
        """

    def load(
        path: Path,
        *,
        max_commits: int | None = None,
        branch_filter: list[str] | None = None,
        shallow: bool = False,
    ) -> Repository:
        """
        Load complete repository state.

        Args:
            path: Path to .git directory or repository root
            max_commits: Limit commits to load (for large repos)
            branch_filter: Only load specified branches
            shallow: Only load reachable from HEAD

        Returns:
            Populated Repository object

        Raises:
            NotAGitRepository: Path is not a git repo
            CorruptRepository: Git data is corrupted
        """
```

### Graph Layout API

```python
class GraphLayout:
    """Computes commit positions for ASCII graph rendering."""

    def __init__(self, repository: Repository):
        self.repo = repository
        self.columns: dict[bytes, int] = {}  # OID -> column
        self.rows: list[bytes] = []  # List of OIDs in row order

    def compute_layout(
        self,
        limit: int | None = None,
        start_oid: bytes | None = None,
    ) -> list[GraphNode]:
        """
        Compute 2D layout for all commits.

        Algorithm (pvigier-based):
        1. Topological sort commits (children before parents)
        2. Assign columns to branch lines
        3. Track active columns for branch continuation
        4. Generate GraphNode list with position data

        Returns:
            List of GraphNode sorted by row (top to bottom)
        """

class GraphNode:
    """Positioned commit for rendering."""

    oid: bytes
    row: int
    column: int
    color: str  # ANSI color code
    symbol: str  # '●', '○', '*', etc.
    edges: list[Edge]  # Lines to draw
    commit: Commit

@dataclass
class Edge:
    """A line segment in the graph."""

    from_row: int
    from_col: int
    to_row: int
    to_col: int
    color: str
```

### Search/Filter API

```python
class FilterEngine:
    """Compiles and evaluates commit filters."""

    # Supported filter syntax:
    #   author:name      - Match author name (fuzzy)
    #   author:email      - Match author email (fuzzy)
    #   date:2024-01      - Match commits from January 2024
    #   date:>2024-01-01  - After given date
    #   date:<2024-12-31  - Before given date
    #   branch:main       - On or merged into branch
    #   message:fix       - Match message (fuzzy)
    #   "exact phrase"    - Exact string match
    #   --not             - Negation (e.g., --not author:bot)

    def compile(expression: str) -> Filter:
        """
        Parse filter expression into executable filter.

        Raises:
            InvalidFilter: Syntax error in expression
        """

    def filter_commits(
        commits: list[Commit],
        filter: Filter,
    ) -> list[Commit]:
        """Apply filter to commit list, preserving order."""
```

---

## Git Parser Implementation

### Object Storage Overview

```
.git/
├── HEAD                    # Symbolic ref to current branch
├── refs/
│   ├── heads/             # Local branches (files)
│   │   ├── main
│   │   └── feature/login
│   ├── remotes/          # Remote branches
│   └── tags/             # Tags
├── objects/
│   ├── 00/               # Loose objects (2-char prefix)
│   │   └── 123456...     # Object content (zlib compressed)
│   ├── pack/
│   │   ├── pack-abc123.idx  # Pack index
│   │   └── pack-abc123.pack  # Pack data
├── packed-refs           # Packed references
├── reflog/
├── config               # Repository config
└── index                # Staging area
```

### Loose Object Reading

```python
class LooseObjectReader:
    """Reads uncompressed objects from .git/objects/."""

    def __init__(self, objects_dir: Path):
        self.objects_dir = objects_dir

    def get_object(self, oid: bytes) -> tuple[int, bytes]:
        """
        Read object by SHA-1 hash.

        Returns:
            Tuple of (object_type, decompressed_content)

        Object types:
            1 = commit
            2 = tree
            3 = blob
            4 = tag
            6 = ofs_delta
            7 = ref_delta

        Raises:
            ObjectNotFound: Object doesn't exist
        """
        # 40-char hex = 2 char dir + 38 char filename
        hex_oid = oid.hex()
        obj_path = self.objects_dir / hex_oid[:2] / hex_oid[2:]

        with open(obj_path, 'rb') as f:
            compressed = f.read()

        return decompress_object(compressed)

    def list_objects(self) -> Iterator[bytes]:
        """Iterate all loose object OIDs."""
        # Walk objects/00, objects/01, ... objects/ff
```

### Pack File Parsing

```python
class PackFileParser:
    """
    Parses git pack files (.pack) with index (.idx).

    Pack file format:
    - 4-byte signature: 'PACK'
    - 4-byte version: 2 or 3
    - 4-byte object count
    - Object entries (compressed deltas/whole objects)
    - 20-byte trailing SHA-1 checksum

    Index file format (v2):
    - 4-byte signature: 0xff744f63
    - 4-byte version: 2
    - 256-entry fanout table (cumulative counts)
    - Object names (20 bytes each, sorted)
    - CRC-32 checksums
    - Pack file offsets (4 bytes each)
    - 20-byte SHA-1 of pack file
    - 20-byte SHA-1 of index file
    """

    def __init__(self, pack_path: Path, index_path: Path):
        self.pack_path = pack_path
        self.index = PackIndex(index_path)

    def get_object(self, oid: bytes) -> tuple[int, bytes]:
        """Get object from pack file by OID."""
        offset = self.index.find_offset(oid)
        return self._read_object_at(offset)

    def _read_object_at(self, offset: int) -> tuple[int, bytes]:
        """Read and decompress object at specific offset."""
        # 1. Read variable-length header (type + size)
        # 2. Read zlib-compressed data
        # 3. Handle delta objects (resolve base, apply delta)
```

### Commit Object Parsing

```python
class CommitParser:
    """Parses commit object content into Commit dataclass."""

    # Commit object format:
    # tree <sha1>\n
    # parent <sha1>\n
    # parent <sha1>\n  (for merges)
    # author Name <email> timestamp timezone\n
    # committer Name <email> timestamp timezone\n
    # \n
    # <commit message>

    def parse(self, data: bytes) -> Commit:
        """
        Parse raw commit content.

        Content is text with headers, blank line, then message.
        Headers are space-separated: "tree", "parent", "author", "committer"
        """

    def _parse_actor(self, line: str) -> Actor:
        """Parse 'Name <email> timestamp tz' into Actor."""

    def _parse_timestamp(self, line: str) -> tuple[int, str]:
        """Parse timestamp and timezone from actor line."""
```

---

## Graph Rendering Algorithm

### ASCII Graph Characters

```python
# Git-style ASCII graph characters
GRAPH_CHARS = {
    'pipe':           '│',   # Vertical line (continuing branch)
    'dash':           '-',   # Horizontal line (to commit)
    'corner_down':    '┌',   # First commit in branch
    'corner_up':     '└',   # Branch joins another
    'merge_left':     '┐',   # Branch diverges
    'merge_right':    '┘',   # Branch rejoins
    'split_left':     '├',   # Split to parent
    'split_right':    '┤',   # Split from parent
    'cross':          '┼',   # Branches cross
    'dot':            '●',   # Commit node
    'empty':          '○',   # Commit node (not on displayed branch)
    'head':           '*',   # HEAD commit
    'space':          ' ',   # No line
}

# Example output:
# │ * commit message on feature
# │ │
# │ ●   Merge branch 'main' into feature
# │ ┌┴┐
# │ │ │ ● another commit
# │ │ ├─╯
# │ │ │
# │ ● │   first feature commit
# ├─┼─┘
# │ │
# │ ●   Merge branch 'feature'
# ├─┼─────╮
# │ │     │
# │ │     ● commit on main
```

### Layout Algorithm (pvigier-based)

```python
def compute_layout(commits: list[Commit]) -> list[GraphNode]:
    """
    Compute ASCII graph layout using straight-branches algorithm.

    Steps:
    1. Build children map (OID -> list of child OIDs)
    2. Topological sort (DFS, children before parents)
    3. Initial column assignment (new column per branch head)
    4. Column allocation:
       - Branch child: reuse parent's column
       - Merge child: find first free column
       - No children: close column, reuse for parents
    5. Generate edges and positioning
    """

    # Track active columns
    active_columns: dict[int, bytes] = {}  # col -> commit_oid
    next_column = 0

    # Column states during iteration
    commit_columns: dict[bytes, int] = {}  # oid -> assigned column

    for commit in sorted_commits:  # Topological order
        # Assign column to this commit
        if commit in commit_columns:
            col = commit_columns[commit]
        else:
            col = next_column
            next_column += 1

        # Determine edges to parents
        edges = []
        for parent_oid in commit.parents:
            parent_col = commit_columns.get(parent_oid)
            if parent_col is not None:
                # Draw line from (col, commit) to (parent_col, parent)
                edges.append(Edge(
                    from_row=commit.row,
                    from_col=col,
                    to_row=parent.row,
                    to_col=parent_col,
                    color=branch_color(col)
                ))
            else:
                # Parent not in view, draw to edge of screen
                edges.append(Edge(...))

        # Determine children handling
        children = children_map.get(commit.oid, [])

        if len(children) == 0:
            # Branch ends here, free column
            if col not in needed_for_parents:
                del active_columns[col]
        elif len(children) > 1:
            # Merge point - handle column redistribution
            pass

        yield GraphNode(
            oid=commit.oid,
            row=commit.row,
            column=col,
            symbol='●' if col == selected_column else '○',
            edges=edges,
            commit=commit
        )
```

### Color Assignment

```python
BRANCH_COLORS = [
    'blue',      # main, master
    'green',     # feature/*
    'magenta',   # bugfix/*
    'cyan',      # hotfix/*
    'yellow',    # release/*
    'white',     # tags
    'bright_blue',
    'bright_green',
    # ... cycle through for many branches
]

def get_branch_color(branch_name: str, branch_index: int) -> str:
    """Get ANSI color for branch."""
    if branch_name in ('main', 'master'):
        return 'cyan'
    if branch_name.startswith('feature/'):
        return 'green'
    if branch_name.startswith('bugfix/'):
        return 'magenta'
    return BRANCH_COLORS[branch_index % len(BRANCH_COLORS)]
```

---

## UI/TUI Implementation

### Main Application Structure

```python
from textual.app import App
from textual.screen import Screen
from textual.binding import Binding

class GitVizApp(App):
    """Main TUI application."""

    CSS = """
    Screen {
        background: $surface;
    }

    # graph-panel {
        height: 70%;
        border: solid $primary;
    }

    # detail-panel {
        height: 30%;
        border: solid $secondary;
    }

    # search-bar {
        height: 3;
        background: $surface-darken-1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("g", "go_top", "Top", show=False),
        Binding("G", "go_bottom", "Bottom", show=False),
        Binding("/", "focus_search", "Search", show=True),
        Binding("f", "toggle_filter", "Filter", show=True),
        Binding("d", "show_diff", "Diff", show=True),
        Binding("b", "checkout", "Checkout", show=True),
        Binding("c", "copy_hash", "Copy", show=True),
        Binding("h", "scroll_left", "Left", show=False),
        Binding("l", "scroll_right", "Right", show=False),
        Binding("left", "scroll_left", ""),
        Binding("right", "scroll_right", ""),
        Binding("up", "cursor_up", ""),
        Binding("down", "cursor_down", ""),
        Binding("pageup", "page_up", ""),
        Binding("pagedown", "page_down", ""),
        Binding("escape", "clear_search", ""),
        Binding("ctrl+c", "quit", ""),
    ]

    def __init__(self, repo_path: Path):
        super().__init__()
        self.repo_path = repo_path
        self.repository: Repository | None = None
        self.graph_nodes: list[GraphNode] = []
        self.filter_engine = FilterEngine()
        self.current_filter: Filter | None = None

    async def on_mount(self) -> None:
        """Initialize application after mount."""
        await self.load_repository()
        await self.compute_layout()
        self.push_screen(MainScreen())

    async def load_repository(self) -> None:
        """Load git repository data."""
        loader = RepositoryLoader()
        self.repository = await loader.load(self.repo_path)
```

### Main Screen

```python
class MainScreen(Screen):
    """Main graph visualization screen."""

    def compose(self):
        yield Header()
        yield SearchBar(id="search-bar")
        yield GraphWidget(id="graph-panel")
        yield DetailPanel(id="detail-panel")
        yield StatusBar()

    def on_mount(self):
        """Set focus to graph widget."""
        self.query_one("#graph-panel", GraphWidget).focus()
```

### Graph Widget

```python
class GraphWidget(Widget):
    """Displays the commit graph with scrolling support."""

    commit_rows: list[CommitRow]
    selected_index: int
    visible_start: int
    visible_height: int

    def __init__(self):
        super().__init__()
        self.commit_rows = []
        self.selected_index = 0
        self.visible_start = 0

    def render_commit(self, node: GraphNode) -> str:
        """Render single commit line with graph and info."""
        # Graph part: 10-15 characters wide
        graph = self._render_graph_column(node)
        # Commit info: hash, author, date, message
        info = f" {node.commit.short_oid} "
        info += f"{node.commit.author.name:<20} "
        info += f"{format_date(node.commit.author_time):<12} "
        info += f"{node.commit.short_message}"
        return graph + info

    def _render_graph_column(self, node: GraphNode) -> str:
        """Render the ASCII graph portion for this commit."""
        # Build per-character column mapping
        # Return string like "│ * │ │ │ │" or "├─┤ │ │ │"
```

### Diff Viewer

```python
class DiffScreen(Screen):
    """Shows diff for selected commit."""

    def __init__(self, commit: Commit, repository: Repository):
        super().__init__()
        self.commit = commit
        self.repo = repository

    async def on_mount(self) -> None:
        """Generate and display diff."""
        diff = await self.generate_diff()
        self.query_one("#diff-content", RichLog).append(
            diff,
            auto_scroll=False
        )

    async def generate_diff(self) -> str:
        """Generate unified diff for this commit."""
        if not self.commit.parents:
            # Initial commit - show all files
            tree = self.repo.get_tree(self.commit.tree_oid)
            return self._diff_tree(tree)
        else:
            parent = self.repo.get_commit(self.commit.parents[0])
            return self._diff_trees(
                parent.tree_oid,
                self.commit.tree_oid
            )
```

---

## User Interactions

### Keyboard Navigation

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
| `b` | Checkout selected branch |
| `c` | Copy commit hash |
| `Esc` | Close dialogs, clear search |
| `q` | Quit |

### Mouse Interactions

| Action | Result |
|--------|--------|
| Click on commit | Select commit |
| Click on branch | Checkout branch |
| Scroll up/down | Navigate commits |
| Double-click | Show diff |
| Right-click | Context menu |

### Search & Filter

**Search Mode** (press `/`):
- Fuzzy match on: commit hash, author name, author email, message
- Results filter the view
- Press `Esc` to clear

**Filter Mode** (press `f`):
- Opens filter panel with presets:
  - By author: "Show commits by specific author"
  - By date: "Last 7 days", "Last 30 days", "This year"
  - By branch: "On main", "On current branch"
  - By message: Custom pattern
- Multiple filters can be combined
- Clear all with `Esc`

---

## Error Handling

### Error Types

```python
class GitVizError(Exception):
    """Base exception for all gitviz errors."""
    pass

class NotAGitRepository(GitVizError):
    """Path does not contain a .git directory."""

class ObjectNotFound(GitVizError):
    """Requested git object doesn't exist."""

class CorruptRepository(GitVizError):
    """Repository data is corrupted."""

class PackFileError(GitVizError):
    """Error parsing pack file."""

class InvalidFilter(GitVizError):
    """Filter expression is malformed."""

class DiffError(GitVizError):
    """Cannot generate diff for commit."""
```

### Recovery Strategies

| Error | Handling |
|-------|----------|
| `NotAGitRepository` | Show helpful message, suggest `git init` |
| `ObjectNotFound` | Log warning, skip object, continue |
| `CorruptRepository` | Log error, offer to run `git fsck` |
| `PackFileError` | Fall back to loose objects if possible |
| `InvalidFilter` | Show syntax help, don't clear current view |
| `DiffError` | Show error in detail panel, continue |

### User-Facing Messages

```python
# Informational
"Loading repository: {path}"
"Found {n} commits, {b} branches"
"Filtered to {n} commits"

# Errors
"Error: Not a git repository: {path}"
"Warning: Object {oid} not found (may be shallow clone)"
"Error: Cannot read pack file: {reason}"

# Help
"Press '/' to search, 'f' to filter, 'd' for diff"
"Use arrow keys to navigate, 'q' to quit"
```

---

## Edge Cases

### Large Repositories

**Problem**: Repositories with 100k+ commits cause memory/performance issues.

**Solutions**:
1. **Lazy loading**: Only load visible commits, prefetch ahead
2. **Pagination**: Load commits in batches, virtual scrolling
3. **Head-only mode**: `--max-commits N` flag
4. **Branch filtering**: Only show commits reachable from selected branches
5. **Date filtering**: `--since="2024-01-01"` to limit range

```python
# Example: Lazy loading implementation
class LazyRepository:
    """Repository with on-demand commit loading."""

    def __init__(self, path: Path, batch_size: int = 1000):
        self.path = path
        self.batch_size = batch_size
        self._commit_cache: dict[bytes, Commit] = {}
        self._loaded_all = False

    def get_commit(self, oid: bytes) -> Commit:
        if oid not in self._commit_cache:
            self._ensure_loaded([oid])
        return self._commit_cache[oid]

    def get_visible_commits(self, start: int, count: int) -> list[Commit]:
        """Get commits in range, loading as needed."""
```

### Shallow Clones

**Problem**: Shallow clones don't have full history.

**Detection**:
```python
def is_shallow(repo_path: Path) -> bool:
    """Check if repository is shallow."""
    shallow_file = repo_path / '.git' / 'shallow'
    return shallow_file.exists()
```

**Handling**:
- Show warning: "Shallow clone - history may be incomplete"
- Adjust layout: no lines going above available commits
- Indicate cut-off with `...` marker

### Orphan Commits

**Problem**: Commits not reachable from any ref (reflog-only, dangling).

**Solutions**:
- Option `--all` to include reflog
- Option `--no-opt` to show unreachable
- Indicate with different color/symbol

### Detached HEAD

**Problem**: HEAD points directly to commit, not branch.

**Handling**:
- Show `(HEAD detached at {short_oid})`
- Don't offer checkout action
- Treat as special "branch" with no name

### Binary Files in Diffs

**Problem**: Cannot show unified diff for binary files.

**Handling**:
```python
def is_binary(tree_entry) -> bool:
    """Check if file is binary."""
    # Check gitattributes
    # Check for null bytes in content
    return False  # placeholder

def format_diff_entry(entry) -> str:
    if is_binary(entry):
        return f"  {entry.path}: Binary file"
```

### Non-UTF8 Content

**Problem**: Git objects may contain non-UTF8 encoding.

**Handling**:
```python
def safe_decode(data: bytes, encoding: str = 'utf-8') -> str:
    """Decode bytes, fallback to latin-1."""
    try:
        return data.decode(encoding)
    except UnicodeDecodeError:
        return data.decode('latin-1', errors='replace')
```

### Rebase In Progress

**Problem**: `.git/rebase-merge` or `.git/rebase-apply` exists.

**Handling**:
- Detect rebase state
- Show current rebase status in status bar
- Offer to abort/continue rebase (if git available)

### Merge Conflicts

**Problem**: Unmerged commits in index.

**Handling**:
- Show conflicted files differently
- Allow `git checkout --ours/--theirs` (if git available)

---

## Dependencies

### Runtime Dependencies

```toml
[project]
dependencies = [
    "textual>=0.7.0",
    "textual-dev>=1.0.0",  # For dev tools only
]
```

**Why these only?**
- Textual handles: terminal I/O, rendering, widgets, CSS, async
- Everything else (git parsing, graph layout, etc.) is pure Python

### Development Dependencies

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "pytest-cov>=4.0",
    "ruff>=0.1",
    "mypy>=1.0",
    "pre-commit>=3.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

### Dependency Rationale

| Library | Purpose | Why Needed |
|---------|---------|------------|
| textual | TUI framework | Core rendering, widgets, events |
| (standard library) | Git parsing | zlib (decompress), pathlib, struct |
| (standard library) | Data structures | dataclasses, collections, typing |

**Explicitly NOT included**:
- `gitpython` - Would add git subprocess dependency
- `pygit2` - C extension complexity
- `dulwich` - Alternative; we're implementing our own for learning/control

---

## Testing Strategy

### Test Structure

```
tests/
├── conftest.py           # Shared fixtures
├── unit/
│   ├── test_commit.py    # Commit parsing
│   ├── test_pack.py      # Pack file reading
│   ├── test_layout.py    # Graph layout algorithm
│   └── test_filter.py    # Filter engine
└── integration/
    ├── test_simple_repo.py
    ├── test_branching.py
    └── test_performance.py
```

### Test Fixtures

**simple_repo/**:
```
* abc1234 (HEAD -> main) Third commit
* def5678 Second commit
* 0123456 Initial commit
```

**branched_repo/**:
```
*   xyz7890 (HEAD -> main) Merge branch 'feature'
|\  
| * uvw3456 (feature) Feature commit 2
| * rst6789 Feature commit 1
* | qrs4567 Commit on main
|/  
* mno0123 Base commit
```

**packed_repo/**:
- Same structure as branched_repo
- All objects in pack file (no loose objects)
- Tests pack file parsing

**shallow_repo/**:
- Same structure
- Contains `.git/shallow` file
- Tests shallow clone handling

### Key Test Cases

```python
def test_commit_parsing():
    """Test commit object parsing."""
    raw = b"""tree 4b825dc642cb6eb9a060e54bf8d69288fbee4904
author Alice <alice@example.com> 1704067200 +0000
committer Alice <alice@example.com> 1704067200 +0000

Initial commit
"""
    commit = CommitParser().parse(raw)
    assert commit.author.name == "Alice"
    assert commit.short_message == "Initial commit"

def test_graph_layout_branching():
    """Test layout assigns correct columns for branches."""
    commits = load_fixture("branched_repo")
    layout = GraphLayout(commits)
    nodes = layout.compute_layout()
    
    # Feature branch should have separate column
    feature_commits = [n for n in nodes if "feature" in n.commit.message]
    assert len(set(n.column for n in feature_commits)) == 1

def test_filter_by_author():
    """Test author filtering."""
    commits = load_fixture("branched_repo")
    filter = FilterEngine.compile("author:Alice")
    result = list(FilterEngine.filter_commits(commits, filter))
    assert all("Alice" in c.author.name for c in result)
```

### Performance Tests

```python
def test_large_repo_performance():
    """Ensure layout completes in reasonable time for large repos."""
    import time
    commits = generate_large_repo(n=50000)
    start = time.perf_counter()
    layout = GraphLayout(commits)
    nodes = layout.compute_layout()
    elapsed = time.perf_counter() - start
    
    assert elapsed < 5.0  # Should complete in under 5 seconds
```

---

## Implementation Phases

### Phase 1: Core Git Parser (Week 1)

**Goal**: Parse git repositories without git CLI

**Deliverables**:
- [ ] Loose object reader
- [ ] Pack file parser (v2 index)
- [ ] Commit object parser
- [ ] Ref/resolution system
- [ ] Repository loader with discovery
- [ ] Unit tests for parser module

**Milestone**: Can load any git repository from `.git` directory

### Phase 2: Graph Layout Engine (Week 2)

**Goal**: Compute commit positions for ASCII visualization

**Deliverables**:
- [ ] Topological commit sorting
- [ ] Column allocation algorithm
- [ ] Edge generation
- [ ] Color assignment
- [ ] ASCII character mapping
- [ ] Unit tests for layout

**Milestone**: Can render static ASCII graph of any repository

### Phase 3: TUI Application (Week 3)

**Goal**: Interactive terminal interface

**Deliverables**:
- [ ] Textual app scaffolding
- [ ] Graph widget with scrolling
- [ ] Commit detail panel
- [ ] Keyboard navigation
- [ ] Mouse support
- [ ] Status bar and hints

**Milestone**: Fully navigable graph visualization

### Phase 4: Search & Filter (Week 4)

**Goal**: Find and filter commits

**Deliverables**:
- [ ] Filter expression parser
- [ ] Author filter
- [ ] Date filter
- [ ] Branch filter
- [ ] Message filter
- [ ] Fuzzy search
- [ ] Combined filters

**Milestone**: Can efficiently find commits in large repositories

### Phase 5: Diff Viewer (Week 5)

**Goal**: Show commit changes

**Deliverables**:
- [ ] Tree object parser
- [ ] Diff generation between trees
- [ ] Diff screen/widget
- [ ] Syntax highlighting (optional)
- [ ] Navigate diff hunks

**Milestone**: Can inspect any commit's changes

### Phase 6: Polish & Performance (Week 6)

**Goal**: Production quality

**Deliverables**:
- [ ] Lazy loading for large repos
- [ ] Performance optimization
- [ ] Error handling improvements
- [ ] Documentation
- [ ] CLI argument refinement
- [ ] Edge case handling
- [ ] Integration tests

**Milestone**: Ready for production use

---

## CLI Interface

```python
# pyproject.toml entry point
[project.scripts]
gitviz = "gitviz.cli:main"
```

```bash
# Usage examples
gitviz                    # Auto-discover repo in current directory
gitviz /path/to/repo      # Specify repo path
gitviz --max-commits 100  # Limit history
gitviz --branch main      # Focus on specific branch
gitviz --since "2024-01"   # Date filter
gitviz --all              # Include all refs
gitviz --no-color         # Disable colors
```

---

## Success Criteria

1. **Parses standard repositories**: Works with Python, Linux kernel, any popular OSS repo
2. **Matches git log --graph**: Output visually matches `git log --graph --oneline`
3. **Smooth interaction**: 60 FPS scrolling, instant key response
4. **Handles edge cases**: Shallow clones, empty repos, detached HEAD, large repos
5. **Zero external dependencies**: Only Textual + stdlib
6. **Well-tested**: >90% code coverage on parser and layout modules

---

## Future Enhancements (Out of Scope for v1)

- Interactive rebase (requires git operations)
- Stash viewing
- Submodule support
- Remote fetching
- Bisect integration
- Graphite/branch visualization improvements
- Web deployment (Textual Web)
- Persistent settings
