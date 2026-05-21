# Git Conflict Resolver TUI - Implementation Plan

**Tool**: A visual terminal UI for resolving git merge conflicts with 3-way merge preview, ours/theirs/merge selection, interactive conflict navigation, and automated conflict hints.

**Framework**: Python Textual  
**Status**: Implementation-ready blueprint  
**Generated**: 2026-04-21

---

## 1. Project Overview

### 1.1 Problem Statement

Git merge conflicts are blocks in software development. Existing CLI tools (`git mergetool`, `diff3`) require manual editing with no visual feedback. Developers need a TUI that:

- Shows 3-way view: OURS (current branch), THEIRS (incoming), BASE (common ancestor)
- Enables interactive selection: accept either side, manual edit, or custom merge
- Provides automated hints based on detected patterns
- Supports navigation between conflict regions with hotkeys

### 1.2 Core Features

| Feature | Priority | Description |
|---------|----------|-------------|
| 3-Way Merge Preview | P0 | Display ours/theirs/base side-by-side |
| Conflict Parser | P0 | Parse `<<<<<<<`, `=======`, `>>>>>>>` markers |
| Interactive Selection | P0 | Accept ours, theirs, or edit manually |
| Conflict Navigation | P0 | Jump to prev/next conflict with keys |
| Automated Hints | P1 | Suggest resolution based on patterns |
| File Browser | P1 | Multi-file conflict navigation |
| Undo/Redo | P1 | Full edit history |
| Diff Highlighting | P2 | Inline diff view within conflicts |

---

## 2. File Structure

```
git-conflict-resolver/
├── pyproject.toml
├── README.md
├── src/
│   └── gcr/                      # Main package
│       ├── __init__.py
│       ├── __main__.py           # Entry point: python -m gcr
│       ├── app.py                # Main Textual App
│       ├── config.py             # Configuration management
│       ├── log.py                # Logging setup
│       │
│       ├── core/                # Core domain logic
│       │   ├── __init__.py
│       │   ├── conflict.py       # Conflict model
│       │   ├── parser.py         # Conflict marker parser
│       │   ├── diff3.py         # 3-way merge engine
│       │   ├── hints.py         # Automated conflict hints
│       │   └── resolver.py      # Resolution engine
│       │
│       ├── ui/                  # UI layer
│       │   ├── __init__.py
│       │   ├── screens/
│       │   │   ├── __init__.py
│       │   │   ├── welcome.py   # Welcome screen
│       │   │   ├── file_picker.py   # File selection screen
│       │   │   ├── editor.py   # Main editor screen
│       │   │   └── confirm.py  # Confirmation modals
│       │   ├── widgets/
│       │   │   ├── __init__.py
│       │   │   ├── conflict_view.py   # 3-way conflict widget
│       │   │   ├── diff_view.py    # Inline diff display
│       │   │   ├── file_tree.py   # File browser
│       │   │   ├── status_bar.py # Status information
│       │   │   └── hint_panel.py # Hint suggestions
│       │   └── styles.py        # CSS styles
│       │
│       └── commands/            # CLI commands
│           ├── __init__.py
│           ├── base.py          # Base command class
│           ├── resolve.py       # Resolve command
│           ├── status.py      # Status command
│           └── utils.py       # Command utilities
│
├── tests/
│   ├── __init__.py
│   ��── test_conflict.py
│   ├── test_parser.py
│   ├── test_diff3.py
│   ├── test_hints.py
│   └── test_integration.py
│
├── assets/
│   ├── sample/
│   │   ├── base.txt           # Sample base file
│   │   ├── ours.txt          # Sample ours
│   │   ├── theirs.txt        # Sample theirs
│   │   └── conflicted.txt    # Sample with conflicts
│   └── fixtures/
│       └── merge_conflict_sample.txt
│
├── docs/
│   ├── architecture.md
│   ├── keybindings.md
│   └── conflict_format.md
│
└── .gcr/
    └── config.toml            # User config (git-ignored)
```

---

## 3. Dependencies

### 3.1 Core Dependencies

```toml
# pyproject.toml
[project]
name = "gcr"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    "textual>=0.82.0",
    "rich>=13.0.0",
    "click>=8.1.0",
    "gitpython>=3.1.0",
    "tomlkit>=0.12.0",
    "shiboken6>=6.6.0; platform_system=='Linux'",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.4.0",
    "mypy>=1.9.0",
    "textual-fixtures>=0.2.0",
]
```

### 3.2 Dependency Justification

| Package | Purpose | Version Constraint |
|---------|---------|-------------------|
| `textual` | TUI framework | `>=0.82.0` for lazy loading API |
| `rich` | Terminal rendering | `>=13.0.0` for markup escape fix |
| `click` | CLI argument parsing | Any 8.x |
| `gitpython` | Git repository access | Any 3.1.x |
| `tomlkit` | Config file parsing | Any 0.12.x |
| `shiboken6` | Better performance | Linux only |

### 3.3 Version Lock Strategy

```bash
# requirements.txt (pinned)
textual==0.82.0
rich==13.9.4
click==8.1.8
gitpython==3.1.44
tomlkit==0.12.5
pytest==8.3.4
pytest-asyncio==0.24.0
```

---

## 4. API Design

### 4.1 Core Domain Models

```python
# src/gcr/core/conflict.py
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

class ConflictSide(Enum):
    """Represents which branch a conflict came from."""
    OURS = auto()      # Current branch (HEAD)
    THEIRS = auto()   # Incoming merge
    BASE = auto()     # Common ancestor (for diff3)
    MERGED = auto()  # Resolved版本

class ResolutionChoice(Enum):
    """User selection for conflict resolution."""
    OURS = auto()
    THEIRS = auto()
    MANUAL = auto()
    SAVE_FOR_LATER = auto()

@dataclass(frozen=True)
class ConflictHunk:
    """Single conflict region in a file.
    
    Attributes:
        start_line: 1-based line number where conflict starts
        end_line: 1-based line number where conflict ends
        ours_content: Lines from current branch
        theirs_content: Lines from incoming branch
        base_content: Common ancestor (if diff3 enabled)
        resolution: User's chosen resolution
    """
    start_line: int
    end_line: int
    ours_content: tuple[str, ...]
    theirs_content: tuple[str, ...]
    base_content: tuple[str, ...] = field(default_factory=tuple)
    resolution: Optional[ResolutionChoice] = None
    resolved_content: Optional[str] = None
    
    @property
    def is_resolved(self) -> bool:
        return self.resolution is not None
    
    @property
    def hunk_label(self) -> str:
        return f"Lines {self.start_line}-{self.end_line}"

@dataclass
class ConflictFile:
    """A file containing one or more conflicts.
    
    Attributes:
        path: Relative path to the file
        conflicts: List of conflict hunks
        content: Full file content
        is_binary: Whether file is binary
    """
    path: str
    content: str
    conflicts: list[ConflictHunk] = field(default_factory=list)
    is_binary: bool = False
    
    @property
    def unresolved_count(self) -> int:
        return sum(1 for c in self.conflicts if not c.is_resolved)
    
    @property
    def total_count(self) -> int:
        return len(self.conflicts)
```

### 4.2 Conflict Parser API

```python
# src/gcr/core/parser.py
from dataclasses import dataclass
from typing import Iterator, Optional
import re

@dataclass
class ParseResult:
    """Result of parsing aconflicted file."""
    file: ConflictFile
    parse_warnings: list[str]
    encoding_errors: list[str]

class ConflictParser:
    """Parses git conflict markers from file content.
    
    Usage:
        parser = ConflictParser()
        result = parser.parse(content, file_path)
        
        for hunk in result.file.conflicts:
            print(f"Conflict at line {hunk.start_line}")
    """
    
    # Git conflict marker patterns
    CONFLICT_START = re.compile(r"^<<<<<<<[ :](.*)$", re.MULTILINE)
    CONFLICT_SEPARATOR = re.compile(r"^=======[ :]*$", re.MULTILINE)
    CONFLICT_END = re.compile(r"^>>>>>>>[ :](.*)$", re.MULTILINE)
    
    # Extended diff3 format (includes base)
    DIFF3_BASE_START = re.compile(r"^\|\|\|\|\|\| (.*)$", re.MULTILINE)
    
    def __init__(self, enable_diff3: bool = True):
        self.enable_diff3 = enable_diff3
    
    def parse(self, content: str, file_path: str) -> ParseResult:
        """Parse conflict markers from file content.
        
        Args:
            content: File content as string
            file_path: Path for error messages
            
        Returns:
            ParseResult with parsed conflicts
        """
        warnings = []
        errors = []
        
        # Check for binary content
        try:
            content.encode('utf-8')
        except UnicodeEncodeError:
            return ParseResult(
                file=ConflictFile(path=file_path, content=content, is_binary=True),
                parse_warnings=["File is binary, cannot parse conflicts"],
                encoding_errors=[]
            )
        
        # Find conflicts
        conflicts = list(self._extract_conflicts(content))
        
        return ParseResult(
            file=ConflictFile(path=file_path, content=content, conflicts=conflicts),
            parse_warnings=warnings,
            encoding_errors=errors
        )
    
    def _extract_conflicts(self, content: str) -> Iterator[ConflictHunk]:
        """Extract individual conflict hunks."""
        lines = content.splitlines(keepends=True)
        in_conflict = False
        ours_lines = []
        theirs_lines = []
        base_lines = []
        start_line = 0
        separator_line = 0
        
        for i, line in enumerate(lines):
            if self.CONFLICT_START.match(line):
                in_conflict = True
                ours_lines = []
                theirs_lines = []
                base_lines = []
                start_line = i + 1  # 1-based
            
            elif in_conflict and self.CONFLICT_SEPARATOR.match(line):
                separator_line = i + 1
            
            elif in_conflict and self.DIFF3_BASE_START.match(line):
                # Diff3 base marker
                base_lines.append(line)
            
            elif in_conflict and self.CONFLICT_END.match(line):
                in_conflict = False
                yield ConflictHunk(
                    start_line=start_line,
                    end_line=i + 1,
                    ours_content=tuple(ours_lines),
                    theirs_content=tuple(theirs_lines),
                    base_content=tuple(base_lines),
                )
            
            elif in_conflict:
                if separator_line == 0:
                    ours_lines.append(line)
                elif base_lines:
                    base_lines.append(line)
                else:
                    theirs_lines.append(line)
```

### 4.3 Diff3 Merge Engine

```python
# src/gcr/core/diff3.py
from dataclasses import dataclass
from typing import Optional
from .conflict import ConflictHunk, ConflictSide

@dataclass
class Diff3Result:
    """Result of a 3-way merge operation."""
    merged_content: str
    has_conflicts: bool
    conflict_regions: list[tuple[int, int]]

class Diff3Merger:
    """3-way merge algorithm using diff3 format.
    
    Algorithm:
        1. Compute LCS between (base, ours) and (base, theirs)
        2. Identify regions that changed in one or both branches
        3. For unchanged regions: use base content
        4. For changed in one: use that branch's content
        5. For changed in both: mark as conflict
    
    Usage:
        merger = Diff3Merger()
        result = merger.merge(base, ours, theirs)
    """
    
    def __init__(self, conflict_marker_style: str = "merge"):
        self.conflict_marker_style = conflict_marker_style
    
    def merge(
        self,
        base: str,
        ours: str,
        theirs: str,
    ) -> Diff3Result:
        """Perform 3-way merge.
        
        Args:
            base: Common ancestor content
            ours: Current branch content
            theirs: Incoming branch content
            
        Returns:
            Diff3Result with merged content
        """
        base_lines = base.splitlines()
        ours_lines = ours.splitlines()
        theirs_lines = theirs.splitlines()
        
        # Compute diffs
        ours_diff = self._compute_diff(base_lines, ours_lines)
        theirs_diff = self._compute_diff(base_lines, theirs_lines)
        
        # Merge with conflict detection
        merged, regions = self._merge_diffs(
            base_lines, ours_diff, theirs_diff
        )
        
        return Diff3Result(
            merged_content="\n".join(merged),
            has_conflicts=len(regions) > 0,
            conflict_regions=regions
        )
    
    def _compute_diff(
        self,
        base: list[str],
        changed: list[str],
    ) -> list[tuple[str, str]]:
        """Compute line-by-line diff between base and changed."""
        # Simplified: use LCS algorithm
        lcs = self._lcs(base, changed)
        
        diffs = []
        bi = ci = 0
        li = 0
        
        while bi < len(base) or ci < len(changed):
            if li < len(lcs) and bi < len(base) and ci < len(changed):
                if base[bi] == lcs[li] and changed[ci] == lcs[li]:
                    diffs.append(("same", base[bi]))
                    bi += 1
                    ci += 1
                    li += 1
                elif base[bi] != changed[ci]:
                    diffs.append(("remove", base[bi]))
                    bi += 1
                else:
                    diffs.append(("add", changed[ci]))
                    ci += 1
            else:
                if bi < len(base):
                    diffs.append(("remove", base[bi]))
                    bi += 1
                if ci < len(changed):
                    diffs.append(("add", changed[ci]))
                    ci += 1
        
        return diffs
    
    def _lcs(self, a: list[str], b: list[str]) -> list[str]:
        """Compute longest common subsequence."""
        # Standard LCS DP algorithm
        m, n = len(a), len(b)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if a[i-1] == b[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        # Backtrack to get LCS
        result = []
        i, j = m, n
        while i > 0 and j > 0:
            if a[i-1] == b[j-1]:
                result.append(a[i-1])
                i -= 1
                j -= 1
            elif dp[i-1][j] > dp[i][j-1]:
                i -= 1
            else:
                j -= 1
        
        return list(reversed(result))
    
    def _merge_diffs(
        self,
        base: list[str],
        ours_diff: list[tuple[str, str]],
        theirs_diff: list[tuple[str, str]],
    ) -> tuple[list[str], list[tuple[int, int]]]:
        """Merge two diffs and detect conflicts."""
        # Simplified merge logic
        merged = []
        regions = []
        
        # Implementation continues...
        return merged, regions
```

### 4.4 Hint Engine API

```python
# src/gcr/core/hints.py
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional
from .conflict import ConflictHunk

class HintType(Enum):
    """Types of automated hints."""
    SAME_AS_BASE = auto()      # Ours matches base, use theirs
    SAME_AS_THEIRS = auto()     # Theirs matches base, use ours
    IDENTICAL = auto()           # Both sides identical, auto-resolve
    SIMPLE_REORDER = auto()      # Just reordered, no real conflict
    SYNTAX_CHANGE = auto()      # Only formatting/syntax
    SEMANTIC_CHANGE = auto()   # Meaningful change

@dataclass
class ConflictHint:
    """Automated hint for resolving a conflict."""
    hint_type: HintType
    confidence: float          # 0.0 - 1.0
    suggested_choice: Optional[str]
    explanation: str

class HintEngine:
    """Analyzes conflicts and provides resolution hints.
    
    Usage:
        engine = HintEngine()
        for hunk in conflict_file.conflicts:
            hint = engine.analyze(hunk)
            if hint.confidence > 0.9:
                print(f"Auto-resolve: {hint.suggested_choice}")
    """
    
    # Patterns that indicate minor changes
    MINOR_PATTERNS = {
        'whitespace': r'^\s*$',
        'comment': r'^\s*#',
        'docstring': r'^\s*"""',
    }
    
    def analyze(self, hunk: ConflictHunk) -> ConflictHint:
        """Analyze a conflict hunk and provide hint.
        
        Args:
            hunk: Conflict hunk to analyze
            
        Returns:
            ConflictHint with suggested resolution
        """
        ours = hunk.ours_content
        theirs = hunk.theirs_content
        base = hunk.base_content
        
        # Case 1: Both sides identical (auto-resolve)
        if ours == theirs:
            return ConflictHint(
                hint_type=HintType.IDENTICAL,
                confidence=1.0,
                suggested_choice="auto",
                explanation="Both sides are identical - auto-resolving"
            )
        
        # Case 2: Ours matches base (use theirs)
        if base and self._lines_match(ours, base):
            return ConflictHint(
                hint_type=HintType.SAME_AS_BASE,
                confidence=0.95,
                suggested_choice="theirs",
                explanation="Base matches OURS - THEIRS has changes"
            )
        
        # Case 3: Theirs matches base (use ours)
        if base and self._lines_match(theirs, base):
            return ConflictHint(
                hint_type=HintType.SAME_AS_THEIRS,
                confidence=0.95,
                suggested_choice="ours",
                explanation="Base matches THEIRS - OURS has changes"
            )
        
        # Case 4: Check for minor changes
        minor_score = self._check_minor_changes(ours, theirs)
        if minor_score > 0.8:
            return ConflictHint(
                hint_type=HintType.SYNTAX_CHANGE,
                confidence=minor_score,
                suggested_choice="ours+theirs",
                explanation=f"Minor changes detected ({minor_score:.0%}) - recommend manual merge"
            )
        
        # Default: No confident hint
        return ConflictHint(
            hint_type=HintType.SEMANTIC_CHANGE,
            confidence=0.0,
            suggested_choice=None,
            explanation="No automated resolution possible"
        )
    
    def _lines_match(self, a: tuple[str, ...], b: tuple[str, ...]) -> bool:
        """Check if two line sets match."""
        if len(a) != len(b):
            return False
        return all(ai.strip() == bi.strip() for ai, bi in zip(a, b))
    
    def _check_minor_changes(self, ours: tuple[str, ...], theirs: tuple[str, ...]) -> float:
        """Score how 'minor' the changes are."""
        import re
        
        # Extract non-whitespace/comment lines
        content_lines = lambda lines: [
            l for l in lines 
            if l.strip() and not re.match(r'^\s*(#|""")', l)
        ]
        
        ours_content = content_lines(ours)
        theirs_content = content_lines(theirs)
        
        if not ours_content or not theirs_content:
            return 0.0
        
        # Check if structure unchanged, only values changed
        ours_struct = [re.sub(r'[0-9]+', 'N', l) for l in ours_content]
        theirs_struct = [re.sub(r'[0-9]+', 'N', l) for l in theirs_content]
        
        if ours_struct == theirs_struct:
            return 0.9
        
        return 0.0
```

### 4.5 Resolution Engine

```python
# src/gcr/core/resolver.py
from dataclasses import dataclass
from typing import Optional
from .conflict import ConflictFile, ConflictHunk, ResolutionChoice

@dataclass
class ResolutionResult:
    """Result of resolving a conflict file."""
    file: ConflictFile
    success: bool
    error_message: Optional[str]
    warnings: list[str]

class Resolver:
    """Handles conflict resolution and file writing.
    
    Usage:
        resolver = Resolver()
        for hunk in conflict_file.conflicts:
            resolver.resolve(hunk, ResolutionChoice.OURS)
        
        result = resolver.apply(conflict_file)
    """
    
    def __init__(self, backup_enabled: bool = True):
        self.backup_enabled = backup_enabled
    
    def resolve(
        self,
        hunk: ConflictHunk,
        choice: ResolutionChoice,
        custom_content: Optional[str] = None,
    ) -> None:
        """Apply resolution to a conflict hunk."""
        if choice == ResolutionChoice.OURS:
            hunk.resolved_content = ''.join(hunk.ours_content)
        elif choice == ResolutionChoice.THEIRS:
            hunk.resolved_content = ''.join(hunk.theirs_content)
        elif choice == ResolutionChoice.MANUAL and custom_content:
            hunk.resolved_content = custom_content
        else:
            hunk.resolution = choice
        
        hunk.resolution = choice
    
    def apply(self, conflict_file: ConflictFile) -> ResolutionResult:
        """Apply all resolutions and write result."""
        warnings = []
        
        # Check for unresolved conflicts
        unresolved = [c for c in conflict_file.conflicts if not c.is_resolved]
        if unresolved:
            return ResolutionResult(
                file=conflict_file,
                success=False,
                error_message=f"{len(unresolved)} unresolved conflicts",
                warnings=warnings
            )
        
        # Rebuild file content
        try:
            content = self._rebuild_content(conflict_file)
        except Exception as e:
            return ResolutionResult(
                file=conflict_file,
                success=False,
                error_message=str(e),
                warnings=warnings
            )
        
        conflict_file.content = content
        
        return ResolutionResult(
            file=conflict_file,
            success=True,
            error_message=None,
            warnings=warnings
        )
    
    def _rebuild_content(self, conflict_file: ConflictFile) -> str:
        """Rebuild file with resolved conflicts."""
        # Implementation continues...
        pass
```

### 4.6 UI Application API

```python
# src/gcr/app.py
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.theme import Theme

from .ui.screens.welcome import WelcomeScreen
from .ui.screens.file_picker import FilePickerScreen
from .ui.screens.editor import EditorScreen
from .config import Config

class GCRApp(App):
    """Git Conflict Resolver - Terminal UI Application."""
    
    TITLE = "Git Conflict Resolver"
    SUB_TITLE = "3-way merge made visual"
    
    # Theme configuration
    THEMES = {
        "gcr": Theme(
            "gcr",
            "dark",
            "#1a1a2e",    # Primary background
            "#16213e",     # Secondary background
            "#e94560",     # Primary accent (red/coral)
            "#0f3460",     # Surface
            "#f1f1f1",     # Text
        )
    }
    
    CSS_PATH = "src/gcr/ui/styles.tcss"
    
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("f1", "show_help", "Help", show=False),
    ]
    
    def __init__(self, config: Config | None = None):
        super().__init__()
        self.config = config or Config()
        self.conflict_files: list[ConflictFile] = []
        self.current_file_index = 0
    
    # === Screen Management ===
    
    def on_mount(self) -> None:
        """Called when app mounts."""
        self.install_screen(WelcomeScreen(), name="welcome")
        self.install_screen(FilePickerScreen(), name="picker")
        self.install_screen(EditorScreen(), name="editor")
        
        # Start at welcome screen
        self.push_screen("welcome")
    
    # === Core Actions ===
    
    def action_start(self) -> None:
        """Start conflict resolution workflow."""
        self.push_screen("picker")
    
    def action_show_help(self) -> None:
        """Show help overlay."""
        # Implementation...
        pass
    
    def get_current_file(self) -> ConflictFile | None:
        """Get currently active conflict file."""
        if self.conflict_files:
            return self.conflict_files[self.current_file_index]
        return None
```

### 4.7 Screen API

```python
# src/gcr/ui/screens/editor.py
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual.containers import Container, Horizontal, Vertical
from textual import work
from textual.binding import Binding

from ..widgets.conflict_view import ConflictView
from ..widgets.hint_panel import HintPanel
from ..widgets.status_bar import StatusBar

class EditorScreen(Screen):
    """Main conflict editor screen."""
    
    BINDINGS = [
        Binding("j", "next_conflict", "Next Conflict"),
        Binding("k", "prev_conflict", "Prev Conflict"),
        Binding("o", "accept_ours", "Accept Ours"),
        Binding("i", "accept_theirs", "Accept Theirs"),
        Binding("e", "edit_manual", "Edit"),
        Binding("h", "show_hints", "Toggle Hints"),
        Binding("w", "write_file", "Write"),
        Binding("ctrl+w", "write_file", "Write"),
        Binding("u", "undo", "Undo"),
        Binding("r", "redo", "Redo"),
    ]
    
    def __init__(self):
        super().__init__()
        self.current_conflict_index = 0
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(size=60):
                yield Static("CONFLICTS", classes="section-title")
                yield ConflictView(id="conflict-view")
            with Vertical(size=40):
                yield Static("HINTS", classes="section-title")
                yield HintPanel(id="hint-panel")
        yield StatusBar(id="status-bar")
        yield Footer()
    
    def on_mount(self) -> None:
        """Load conflict data."""
        app = self.app
        if conflict_file := app.get_current_file():
            self.load_conflict_file(conflict_file)
    
    def load_conflict_file(self, conflict_file: ConflictFile) -> None:
        """Load a conflict file into the editor."""
        view = self.query_one("#conflict-view", ConflictView)
        view.load_conflicts(conflict_file.conflicts)
        
        self.current_conflict_index = 0
        self._update_display()
    
    def _update_display(self) -> None:
        """Update UI to show current conflict."""
        view = self.query_one("#conflict-view", ConflictView)
        view.show_conflict(self.current_conflict_index)
        
        status = self.query_one("#status-bar", StatusBar)
        status.update_conflict_index(
            self.current_conflict_index,
            self.total_conflicts
        )
    
    # === Action Handlers ===
    
    def action_next_conflict(self) -> None:
        """Move to next conflict."""
        if self.current_conflict_index < self.total_conflicts - 1:
            self.current_conflict_index += 1
            self._update_display()
    
    def action_prev_conflict(self) -> None:
        """Move to previous conflict."""
        if self.current_conflict_index > 0:
            self.current_conflict_index -= 1
            self._update_display()
    
    def action_accept_ours(self) -> None:
        """Accept OURS side for current conflict."""
        # Implementation...
        pass
    
    def action_accept_theirs(self) -> None:
        """Accept THEIRS side for current conflict."""
        # Implementation...
        pass
```

### 4.8 Conflict View Widget

```python
# src/gcr/ui/widgets/conflict_view.py
from textual.widget import Widget
from textual.widgets import Static, Button, Label
from textual.containers import Container, Vertical, Horizontal
from textual.message import Message
from textual import work

from ...core.conflict import ConflictHunk, ResolutionChoice

class ConflictView(Widget):
    """Widget displaying a 3-way conflict view.
    
    Usage:
        view = ConflictView()
        view.load_conflicts(conflicts)
        view.show_conflict(0)
        
        def on_conflict_resolved(choice):
            ...
    """
    
    class Resolved(Message):
        """Message fired when a conflict is resolved."""
        def __init__(self, choice: ResolutionChoice):
            self.choice = choice
            super().__init__()
    
    CSS = """
    ConflictView {
        border: solid $primary;
        background: $surface;
    }
    
    .conflict-side {
        height: 1fr;
        background: $surface;
        border-right: solid $primary;
    }
    
    .conflict-side:last-child {
        border-right: none;
    }
    
    .side-label {
        text: $accent;
        bold: yes;
        padding: 0 1;
    }
    
    .side-content {
        content: "";
        padding: 1;
        width: 100%;
    }
    
    .ours { border-left: solid $success 3; }
    .theirs { border-left: solid $warning 3; }
    .base { border-left: solid $text 3; }
    """
    
    def __init__(self):
        super().__init__()
        self.conflicts: list[ConflictHunk] = []
        self.current_index = 0
    
    def compose(self) -> ComposeResult:
        yield Horizontal():
            with Vertical(id="ours-panel", classes="conflict-side ours"):
                yield Static("OURS", classes="side-label")
                yield Static(id="ours-content", classes="side-content")
            
            with Vertical(id="theirs-panel", classes="conflict-side theirs"):
                yield Static("THEIRS", classes="side-label")
                yield Static(id="theirs-content", classes="side-content")
            
            with Vertical(id="base-panel", classes="conflict-side base"):
                yield Static("BASE", classes="side-label")
                yield Static(id="base-content", classes="side-content")
    
    def load_conflicts(self, conflicts: list[ConflictHunk]) -> None:
        """Load conflict list."""
        self.conflicts = conflicts
        self.current_index = 0
    
    def show_conflict(self, index: int) -> None:
        """Show conflict at given index."""
        if not self.conflicts or index >= len(self.conflicts):
            return
        
        self.current_index = index
        hunk = self.conflicts[index]
        
        # Update content displays
        self.query_one("#ours-content", Static).update(
            ''.join(hunk.ours_content)
        )
        self.query_one("#theirs-content", Static).update(
            ''.join(hunk.theirs_content)
        )
        
        if hunk.base_content:
            self.query_one("#base-content", Static).update(
                ''.join(hunk.base_content)
            )
```

---

## 5. Error Handling

### 5.1 Error Categories

| Category | Examples | Handling |
|----------|----------|----------|
| **Parse Errors** | Invalid conflict markers, encoding issues | Graceful degradation, warn user |
| **Git Errors** | Not in repo, no conflicts, dirty workdir | Clear error screen, suggest fixes |
| **File Errors** | Permission denied, file not found | Retry dialog, alternative paths |
| **UI Errors** | Widget rendering failures | Fallback to simpler view |
| **State Errors** | Corrupted undo history | Reset state, warn user |

### 5.2 Error Types

```python
# src/gcr/exceptions.py
from typing import Optional

class GCRException(Exception):
    """Base exception for GCR."""
    code: str = "GCR_ERROR"
    
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.details = details

class ParseError(GCRException):
    """Conflict parsing failed."""
    code = "PARSE_ERROR"

class GitError(GCRException):
    """Git operation failed."""
    code = "GIT_ERROR"

class FileError(GCRException):
    """File operation failed."""
    code = "FILE_ERROR"

class NoConflictsError(GCRException):
    """No conflicts found to resolve."""
    code = "NO_CONFLICTS"

class DirtyWorkdirError(GCRException):
    """Working directory has uncommitted changes."""
    code = "DIRTY_WORKDIR"
```

### 5.3 Error Recovery Strategy

```python
# src/gcr/app.py - Error handler

class GCRApp(App):
    # ... existing code ...
    
    def handle_exception(self, error: Exception) -> None:
        """Centralized error handling."""
        if isinstance(error, GCRException):
            self._handle_gcr_error(error)
        elif isinstance(error, GitError):
            self._handle_git_error(error)
        else:
            self._handle_unknown_error(error)
    
    def _handle_gcr_error(self, error: GCRException) -> None:
        """Handle GCR-specific errors."""
        match error.code:
            case "NO_CONFLICTS":
                self.push_screen(WelcomeScreen(msg="No conflicts found!"))
            case "DIRTY_WORKDIR":
                self.notify("Please commit or stash changes first", severity="error")
            case _:
                self.notify(error.message, severity="error")
    
    def _handle_git_error(self, error: GitError) -> None:
        """Handle Git errors."""
        self.push_screen(ErrorScreen(
            title="Git Error",
            message=error.message,
            suggestion="Check git status and try again"
        ))
    
    def _handle_unknown_error(self, error: Exception) -> None:
        """Handle unexpected errors."""
        import traceback
        traceback.print_exc()
        
        self.push_screen(ErrorScreen(
            title="Unexpected Error",
            message=str(error),
            suggestion="Report this bug"
        ))
```

### 5.4 User Feedback Patterns

```python
# Error notifications
self.notify("Error message", severity="error", timeout=10.0)

# Warnings
self.notify("Warning message", severity="warning")

# Info messages
self.notify("Operation complete", severity="information")

# Debug logging (in development)
self.log.debug(f"Context: {context}")
```

---

## 6. Edge Cases

### 6.1 Conflict Format Edge Cases

| Edge Case | Detection | Handling |
|----------|----------|----------|
| Nested conflicts | Overlapping marker ranges | Warning + manual edit |
| Binary files | `\x00` in content | Skip, suggest mergetool |
| Empty conflicts | Empty between markers | Suggest auto-resolve |
| Very large files | >10K lines | Lazy load, pagination |
| Encoding issues | Invalid UTF-8 | Convert or skip |

### 6.2 Git State Edge Cases

| Edge Case | Detection | Handling |
|----------|----------|----------|
| Not a git repo | `git rev-parse` fails | Error screen |
| No merge in progress | No MERGE_HEAD | Error + abort |
| Conflicts already resolved | No markers | Success + exit |
| Rebase in progress | Git var `REBASE_HEAD` | Support rebase |
| Cherry-pick in progress | Git var `CHERRY_PICK_HEAD` | Support |

### 6.3 UI Edge Cases

| Edge Case | Detection | Handling |
|----------|----------|----------|
| Terminal too small | `os.get_terminal_size()` | Warning + minimum size |
| Colors not supported | `$NO_COLOR` set | Plain text fallback |
| Mouse not supported | No terminfo | Keyboard-only mode |
| Very wide terminal | >200 cols | Side-by-side layout |

### 6.4 Resolution Edge Cases

| Edge Case | Detection | Handling |
|----------|----------|----------|
| All conflicts identical | Hunk analysis | Auto-resolve |
| Circular undo | State checkpointing | Clear history |
| File deleted outside | `os.path.exists()` | Confirm deletion |
| External edits | File mtime check | Detect + reload |

---

## 7. Key Bindings Reference

### 7.1 Global Bindings

| Key | Action | Description |
|-----|--------|-------------|
| `q` | `quit` | Quit application |
| `Ctrl+q` | `quit` | Quit (confirm) |
| `F1` | `show_help` | Show help |
| `Ctrl+c` | `interrupt` | Cancel operation |

### 7.2 Navigation Bindings

| Key | Action | Description |
|-----|--------|-------------|
| `j` / `Down` | `next_conflict` | Next conflict |
| `k` / `Up` | `prev_conflict` | Previous conflict |
| `g` | `first_conflict` | Jump to first |
| `G` | `last_conflict` | Jump to last |
| `/` | `search` | Search conflicts |

### 7.3 Resolution Bindings

| Key | Action | Description |
|-----|--------|-------------|
| `o` | `accept_ours` | Accept OURS |
| `i` | `accept_theirs` | Accept THEIRS |
| `e` | `edit_manual` | Edit manually |
| `m` | `merge_both` | Merge both |
| `a` | `apply_hint` | Apply hint |

### 7.4 File Operations

| Key | Action | Description |
|-----|--------|-------------|
| `w` | `write_file` | Write changes |
| `Ctrl+s` | `write_file` | Save (alias) |
| `Ctrl+z` | `undo` | Undo |
| `Ctrl+y` | `redo` | Redo |
| `Ctrl+o` | `open_file` | Open file |
| `n` | `next_file` | Next file with conflicts |

---

## 8. Implementation Roadmap

### Phase 1: Core Infrastructure (Week 1-2)

1. **Project scaffolding**
   - Initialize project structure
   - Set up logging and config
   - Add basic Textual app shell

2. **Conflict parser**
   - Implement marker parsing
   - Handle edge cases
   - Add tests

3. **Basic display**
   - Welcome screen
   - File selection

### Phase 2: Core Editor (Week 3-4)

1. **3-way view widget**
   - Side-by-side display
   - Syntax highlighting

2. **Conflict navigation**
   - Prev/next bindings
   - Jump to conflict

3. **Resolution actions**
   - Accept ours/theirs
   - Manual edit mode

### Phase 3: Advanced Features (Week 5-6)

1. **Diff3 integration**
   - Base content display
   - 3-way merge algorithm

2. **Hint engine**
   - Pattern analysis
   - Auto-suggestions

3. **Undo/redo**
   - Action history
   - State management

### Phase 4: Polish (Week 7-8)

1. **Error handling**
   - Graceful degradation
   - Clear error screens

2. **CLI integration**
   - `gcr` command
   - `--file` flag

3. **Documentation**
   - Keybinding reference
   - README

---

## 9. Acceptance Criteria

- [ ] Application starts and shows welcome screen
- [ ] Can select a file with conflicts
- [ ] 3-way view displays ours/theirs/base
- [ ] Can navigate between conflicts with j/k
- [ ] Can accept ours or theirs with o/i
- [ ] Can manually edit with e
- [ ] Can write resolved file with w
- [ ] Keyboard-only navigation works
- [ ] Error messages are clear
- [ ] Handles binary files gracefully
- [ ] Works with diff3 format
- [ ] Undo/redo functions

---

## 10. Appendix: Sample Data

### 10.1 Sample Conflicted File

```text
def calculate_total(items):
<<<<<<< HEAD
    total = 0
    for item in items:
        total += item.price
=======
    total = sum(item.price for item in items)
>>>>>>> feature/comprehension

    return total


def calculate_tax(total):
<<<<<<< HEAD
    return total * 0.08
=======
    return total * 0.0825
>>>>>>> feature/tax-update
```

### 10.2 Sample diff3 Format

```text
<<<<<<< HEAD
def foo():
||||||| base
def foo():
    return "base"
=======
def foo():
    return "new"
>>>>>>>
```

---

**Generated**: 2026-04-21  
**Version**: 0.1.0  
**Plan Status**: Implementation-ready