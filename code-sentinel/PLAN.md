# CodeSentinel - Implementation Plan

## Project Overview

**Project Name:** CodeSentinel
**Type:** AI-powered local code review assistant (CLI + TUI)
**Core Functionality:** Analyzes code for bugs, security issues, and anti-patterns using local LLMs (llama.cpp/GGUF), displays results in a Textual TUI with severity levels, line-by-line annotations, and actionable suggestions.
**Target Users:** Developers who want private, offline AI-assisted code review without sending code to external APIs.

---

## Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|----------|
| **LLM Engine** | llama-cpp-python | GGUF model loading, local inference, no API costs |
| **TUI Framework** | Textual 0.52+ | Python-native, rich widgets, battle-tested |
| **CLI Framework** | Typer | Type hints, Rich integration, ~70% less boilerplate |
| **Config** | TOML + pydantic | Workspace standard, validation |
| **Syntax Highlighting** | Textual TextArea (tree-sitter) | Built-in, multi-language |
| **Logging** | structlog | Structured logging, pretty dev / JSON prod |
| **Output** | Rich | Console formatting, tables, panels |

### Dependencies

```toml
[project]
dependencies = [
    "llama-cpp-python>=0.2.0",
    "textual>=0.52.0",
    "typer>=0.12.0",
    "rich>=13.0.0",
    "pydantic>=2.0.0",
    "structlog>=24.0.0",
]
```

---

## Feature Specification

### 1. File Analysis (Priority: High)

- **File Reading**: Support single files and directories
- **Language Detection**: Auto-detect via file extension
- **Diff Parsing**: Parse unified diff format (git diff)
- **Large File Handling**: Chunk files that exceed context window
- **Encoding Support**: UTF-8, handle BOM

### 2. LLM Integration (Priority: High)

- **Model Loading**: Load GGUF models from local path
- **Prompt Templates**: Pre-built system prompts for review types
- **Streaming**: Stream token-by-token for UX
- **Token Counting**: Track prompt/completion tokens
- **Context Management**: Truncate or chunk for large files
- **Temperature Control**: Low temperature (0.1-0.3) for code tasks

### 3. Review Categories (Priority: High)

| Category | Description | Key Checks |
|----------|------------|-----------|
| **Security** | Vulnerabilities | Injection, auth bypass, secrets |
| **Bugs** | Logic errors | Null checks, off-by-one, race conditions |
| **Anti-patterns** | Code smells | God functions, magic numbers |
| **Performance** | Efficiency issues | N+1, redundant computation |
| **Best Practices** | Modern patterns | Type hints, async/await |

### 4. Output Display (Priority: High)

- **Severity Levels**: CRITICAL, HIGH, MEDIUM, LOW
- **Line Numbers**: Per-issue line references
- **Code Preview**: Annotated source with highlights
- **Fix Suggestions**: Actionable code snippets
- **CWE/OWASP Mapping**: Industry classifications

### 5. Interactive TUI (Priority: High)

- **File Tree**: File/directory navigation
- **Code View**: Syntax-highlighted code display
- **Issue List**: Filterable/sortable findings
- **Detail Panel**: Full issue context
- **Annotations**: Inline code markers

### 6. CLI Commands (Priority: High)

```bash
# Analyze a file
code-sentinel review src/auth.py

# Analyze with security focus
code-sentinel review src/auth.py --focus security

# Analyze with specific model
code-sentinel review src/auth.py --model models/codellama-7b.q4_k_m.gguf

# Output to JSON
code-sentinel review src/auth.py --format json

# Skip TUI, CLI only
code-sentinel review src/auth.py --no-tui

# Watch mode (re-analyze on change)
code-sentinel watch src/ --glob "*.py"
```

---

## Project Structure

```
code-sentinel/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/
│   └── code_sentinel/
│       ├── __init__.py
│       ├── __main__.py          # Entry: python -m code_sentinel
│       ├── cli.py              # Typer CLI definition
│       ├── config.py           # Configuration management
│       ├── logging.py         # Logging setup
│       ├── engine/            # LLM integration
│       │   ├── __init__.py
│       │   ├── llama.py       # llama-cpp-python wrapper
│       │   └── prompts.py     # Review prompt templates
│       ├── review/            # Review logic
│       │   ├── __init__.py
│       │   ├── analyzer.py    # Core analysis
│       │   ├── rules.py      # Rule definitions
│       │   └── parser.py     # Output parsing
│       ├── ui/               # Textual TUI
│       │   ├── __init__.py
│       │   ├── app.py        # Main TUI app
│       │   ├── screens.py   # Screen definitions
│       │   ├── widgets.py  # Custom widgets
│       │   └── styles.py  # CSS theming
│       └── output/           # Output formatters
│           ├── __init__.py
│           ├── json.py
│           ├── rich.py
│           └── sarif.py    # SARIF format
├── tests/
│   ├── __init__.py
│   ├── test_review.py
│   ├── test_engine.py
│   └── test_ui.py
├── models/                   # GGUF models (gitignored)
└── config.toml              # User configuration
```

---

## File Structure Detail

### Entry Point

```python
# src/code_sentinel/__main__.py
"""Entry point: python -m code_sentinel"""
from code_sentinel.cli import app

if __name__ == "__main__":
    app()
```

### CLI Definition

```python
# src/code_sentinel/cli.py
"""Main CLI application with Typer."""

import typer
from pathlib import Path
from typing import Optional

from code_sentinel.config import load_config
from code_sentinel.logging import configure_logging
from code_sentinel.engine.llama import LlamaEngine
from code_sentinel.review.analyzer import ReviewAnalyzer
from code_sentinel.ui.app import CodeSentinelApp

app = typer.Typer(
    name="code-sentinel",
    help="AI-powered local code review assistant",
    add_completion=False,
)

@app.command()
def review(
    path: str = typer.Argument(..., help="Path to file or directory to review"),
    focus: Optional[str] = typer.Option(
        None, "--focus", "-f", help="Review focus: security, bugs, patterns, all"
    ),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="GGUF model path"
    ),
    format: str = typer.Option("tui", "--format", help="Output: tui, json, text, sarif"),
    no_tui: bool = typer.Option(False, "--no-tui", help="Disable TUI, CLI output only"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file"),
) -> None:
    """Review code for issues and improvements."""
    configure_logging(verbose)
    cfg = load_config(config)

    # Initialize engine
    engine = LlamaEngine(model_path=model or cfg.default_model)

    # Run analysis
    analyzer = ReviewAnalyzer(engine, focus=focus)
    results = analyzer.analyze_path(Path(path))

    if no_tui or format != "tui":
        # CLI output
        from code_sentinel.output.rich import print_results
        print_results(results, format=format)
    else:
        # TUI mode
        app_tui = CodeSentinelApp(results)
        app_tui.run()


@app.command()
def watch(
    path: str = typer.Argument(..., help="Path to watch"),
    glob: str = typer.Option("*.py", "--glob", "-g", help="File pattern"),
    debounce: float = typer.Option(1.0, "--debounce", help="Debounce seconds"),
) -> None:
    """Watch path and re-analyze on changes."""
    # Implementation with watchfiles
    pass


@app.command()
def models() -> None:
    """List available models."""
    from code_sentinel.config import get_model_list
    for model in get_model_list():
        typer.echo(f"  {model}")


@app.command()
def config(
    show: bool = typer.Option(False, "--show", help="Show config"),
    set_key: Optional[str] = typer.Option(None, "--set", help="Set config key"),
    set_value: Optional[str] = typer.Option(None, "--value", help="Set config value"),
) -> None:
    """Manage configuration."""
    # Config management
    pass
```

### Configuration

```python
# src/code_sentinel/config.py
"""Configuration management with pydantic."""

from dataclasses import dataclass, field
from pathlib import Path

import tomllib
from pydantic import Field


@dataclass
class Config:
    """Configuration for CodeSentinel."""

    # Model settings
    default_model: str = "codellama-7b-instruct.q4_k_m.gguf"
    model_dir: str = "models"
    n_ctx: int = 4096
    n_gpu_layers: int = 0  # 0 = CPU only

    # Review settings
    focus: str = "all"  # all, security, bugs, patterns
    severity_threshold: str = "low"
    max_issues: int = 50
    temperature: float = 0.2

    # Output settings
    output_format: str = "tui"
    show_line_numbers: bool = True
    show_explanations: bool = True

    # TUI settings
    dark_mode: bool = True
    sidebar_width: int = 25
    code_panel_width: int = 50


def load_config(config_path: Path | None = None) -> Config:
    """Load configuration from file."""
    if config_path is None:
        config_path = Path("config.toml")

    if not config_path.exists():
        return Config()

    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    return Config(**data.get("code_sentinel", {}))
```

### LLM Engine

```python
# src/code_sentinel/engine/llama.py
"""LLM engine wrapper for llama-cpp-python."""

from pathlib import Path
from typing import Iterator

from llama_cpp import Llama, ChatCompletionChunk


class LlamaEngine:
    """Engine for interacting with local GGUF models."""

    def __init__(
        self,
        model_path: str,
        n_ctx: int = 4096,
        n_gpu_layers: int = 0,
        n_threads: int | None = None,
        verbose: bool = False,
    ):
        """Initialize the LLM engine.

        Args:
            model_path: Path to GGUF model file.
            n_ctx: Context window size.
            n_gpu_layers: Layers to offload to GPU (0 = CPU only).
            n_threads: CPU threads (None = auto).
            verbose: Enable verbose logging.
        """
        self._model_path = model_path
        self._llm = self._load_model(
            model_path,
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers,
            n_threads=n_threads,
            verbose=verbose,
        )

    def _load_model(self, model_path: str, **kwargs) -> Llama:
        """Load the GGUF model."""
        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        return Llama(model_path=str(path), **kwargs)

    def generate(
        self,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        stop: list[str] | None = None,
        stream: bool = False,
    ) -> str | Iterator[str]:
        """Generate text from the model.

        Args:
            prompt: The prompt to generate from.
            temperature: Sampling temperature (0.0-2.0).
            max_tokens: Maximum tokens to generate.
            stop: Stop sequences.
            stream: Whether to stream the response.

        Returns:
            Generated text or stream iterator.
        """
        if stream:
            return self._stream_generate(prompt, temperature, max_tokens, stop or [])
        else:
            return self._generate(prompt, temperature, max_tokens, stop or [])

    def _generate(
        self, prompt: str, temperature: float, max_tokens: int, stop: list[str]
    ) -> str:
        """Generate synchronously."""
        result = self._llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop,
        )
        return result["choices"][0]["text"]

    def _stream_generate(
        self, prompt: str, temperature: float, max_tokens: int, stop: list[str]
    ) -> Iterator[str]:
        """Generate with streaming."""
        for chunk in self._llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop,
            stream=True,
        ):
            if chunk.get("choices"):
                text = chunk["choices"][0].get("text")
                if text:
                    yield text

    def token_count(self, text: str) -> int:
        """Count tokens in text."""
        return len(self._llm.tokenize(text.encode("utf-8")))

    def close(self) -> None:
        """Close the engine."""
        if self._llm:
            self._llm.close()
```

### Review Prompts

```python
# src/code_sentinel/engine/prompts.py
"""Review prompt templates."""

from dataclasses import dataclass


@dataclass
class ReviewPrompt:
    """Review prompt template."""

    system: str
    user_template: str


SECURITY_PROMPT = ReviewPrompt(
    system="""You are a security expert reviewing code for vulnerabilities.

## Severity Classification
- CRITICAL: RCE, SQL injection, auth bypass, data breach
- HIGH: XSS, CSRF, path traversal, insecure crypto
- MEDIUM: Missing validation, weak crypto, info leak
- LOW: Information disclosure, minor issues

## OWASP Top 10 Coverage
Map to: A01-Broken Access Control, A02-Crypto Failures, A03-Injection,
A04-Insecure Design, A05-Security Misconfiguration, A06-Vulnerable Components

## Output Format
JSON array of findings:
{"file", "line", "severity", "category", "cwe", "issue", "fix", "explanation"}
""",
    user_template="""Review this {language} code for security vulnerabilities:

```{language}
{code}
```

Respond with JSON array of findings. Focus only on exploitable security issues.""",
)


BUG_PROMPT = ReviewPrompt(
    system="""You are a code reviewer analyzing for bugs and logic errors.

## Bug Categories
- Null/undefined access
- Off-by-one errors
- Race conditions (TOCTOU)
- Silent failures
- Type coercion issues
- Edge cases (empty, zero, negative)

## Output Format
JSON array: {"line", "severity", "bug_type", "current", "expected", "explanation"}
""",
    user_template="""Analyze this {language} code for bugs:

```{language}
{code}
```

Identify logic errors and incorrect behavior.""",
)


ANTIPATTERN_PROMPT = ReviewPrompt(
    system="""You are a code reviewer detecting anti-patterns and code smells.

## Anti-patterns
- God functions (too many responsibilities)
- Magic numbers/strings
- Deep nesting
- Duplicate code
- Missing abstractions
- Tight coupling
- Premature optimization

## Output Format
JSON: {"line", "severity", "pattern", "issue", "suggestion"}
""",
    user_template="""Detect anti-patterns in:

```{language}
{code}
```""",
)


DEFAULT_PROMPT = ReviewPrompt(
    system="""You are an expert code reviewer analyzing code changes.

## Review Categories
1. SECURITY: Vulnerabilities, injection, auth issues
2. BUGS: Logic errors, null checks, race conditions
3. ANTI-PATTERNS: Code smells, maintainability
4. PERFORMANCE: Efficiency issues
5. BEST PRACTICES: Modern patterns, type hints

## Severity
CRITICAL > HIGH > MEDIUM > LOW

## Output Format
JSON array of findings with: file, line, severity, category, issue, fix, explanation
""",
    user_template="""Review this {language} code:

```{language}
{code}
```

Provide structured JSON findings for all issues found.""",
)


def get_prompt(focus: str = "all") -> ReviewPrompt:
    """Get prompt template by focus."""
    prompts = {
        "security": SECURITY_PROMPT,
        "bugs": BUG_PROMPT,
        "patterns": ANTIPATTERN_PROMPT,
        "all": DEFAULT_PROMPT,
    }
    return prompts.get(focus, DEFAULT_PROMPT)
```

### Core Analyzer

```python
# src/code_sentinel/review/analyzer.py
"""Core analysis logic."""

from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class ReviewFinding:
    """A single review finding."""

    file: str
    line: int
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str  # security, bugs, patterns, performance
    issue: str
    fix: str
    explanation: str
    cwe: str | None = None
    owasp: str | None = None


@dataclass
class ReviewResult:
    """Result of code review."""

    path: Path
    findings: list[ReviewFinding]
    files_reviewed: int
    duration_seconds: float


class ReviewAnalyzer:
    """Analyzer for code review."""

    def __init__(self, engine, focus: str = "all"):
        self.engine = engine
        self.focus = focus

    def analyze_path(self, path: Path) -> ReviewResult:
        """Analyze a file or directory."""
        import time

        start = time.time()

        if path.is_file():
            findings = self._analyze_file(path)
        else:
            findings = []
            for file in path.rglob("*"):
                if file.is_file() and self._should_analyze(file):
                    findings.extend(self._analyze_file(file))

        return ReviewResult(
            path=path,
            findings=findings,
            files_reviewed=len(set(f.file for f in findings)),
            duration_seconds=time.time() - start,
        )

    def _analyze_file(self, file: Path) -> list[ReviewFinding]:
        """Analyze a single file."""
        from code_sentinel.engine.prompts import get_prompt

        code = file.read_text(encoding="utf-8")
        prompt = get_prompt(self.focus)

        # Build user prompt
        lang = self._detect_language(file)
        user_prompt = prompt.user_template.format(language=lang, code=code)

        # Generate review
        response = self.engine.generate(
            prompt.system + "\n\n" + user_prompt,
            temperature=0.2,
            max_tokens=2048,
        )

        # Parse response
        return self._parse_response(response, file)

    def _parse_response(self, response: str, file: Path) -> list[ReviewFinding]:
        """Parse LLM response into findings."""
        # Try JSON parse first
        try:
            data = json.loads(response)
            if isinstance(data, list):
                return [
                    ReviewFinding(
                        file=str(file),
                        line=item.get("line", 0),
                        severity=item.get("severity", "MEDIUM"),
                        category=item.get("category", "unknown"),
                        issue=item.get("issue", item.get("message", "")),
                        fix=item.get("fix", ""),
                        explanation=item.get("explanation", ""),
                        cwe=item.get("cwe"),
                        owasp=item.get("owasp"),
                    )
                    for item in data
                ]
        except json.JSONDecodeError:
            pass

        # Fallback: text parsing
        return self._parse_text_response(response, file)

    def _should_analyze(self, file: Path) -> bool:
        """Check if file should be analyzed."""
        # Filter by extension
        SUPPORTED_EXTENSIONS = {
            ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs",
            ".java", ".kt", ".cs", ".cpp", ".c", ".h", ".rb",
            ".php", ".swift", ".kt", ".scala",
        }
        return file.suffix in SUPPORTED_EXTENSIONS

    def _detect_language(self, file: Path) -> str:
        """Detect programming language."""
        EXT_TO_LANG = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".kt": "kotlin",
            ".cs": "csharp",
            ".cpp": "cpp",
            ".c": "c",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
        }
        return EXT_TO_LANG.get(file.suffix, "text")
```

### Textual TUI App

```python
# src/code_sentinel/ui/app.py
"""Main Textual TUI application."""

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Header, Footer, Tree, TextArea, DataTable, Static
from textual.binding import Binding
from textual.reactive import reactive


class CodeSentinelApp(App):
    """Code review TUI application."""

    CSS = """
    Screen {
        layout: horizontal;
    }

    #files {
        width: 25;
        border-right: solid $primary;
    }

    #code-area {
        width: 1fr;
    }

    #details {
        width: 30;
        border-left: solid $primary;
    }

    #review-list {
        height: 40%;
    }

    #detail-view {
        height: 60%;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("n", "next_file", "Next File"),
        ("p", "prev_file", "Prev File"),
        ("a", "toggle_approve", "Approve"),
        ("r", "toggle_reject", "Reject"),
        ("ctrl+r", "refresh", "Refresh"),
    ]

    current_file = reactive[str | None](None)

    def __init__(self, results):
        super().__init__()
        self.results = results
        self.findings = results.findings

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            # File tree
            with Vertical(id="files"):
                yield Tree("Files", id="file-tree")

            # Code view
            with Vertical(id="code-area"):
                yield TextArea(
                    id="code-view",
                    language="python",
                    read_only=True,
                    show_line_numbers=True,
                )

            # Details panel
            with Vertical(id="details"):
                with VerticalScroll(id="review-list"):
                    yield DataTable(id="issues-table")
                with VerticalScroll(id="detail-view"):
                    yield Static(id="issue-detail")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the UI."""
        # Populate file tree
        tree = self.query_one("#file-tree", Tree)
        for file in set(f.file for f in self.findings):
            tree.root.add_leaf(file)

        # Populate issues table
        table = self.query_one("#issues-table", DataTable)
        table.add_columns("Line", "Severity", "Category")
        for finding in self.findings:
            table.add_row(
                str(finding.line),
                finding.severity,
                finding.category,
            )

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle file selection."""
        if event.node.data:
            self.load_file(event.node.data)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle issue selection."""
        finding = self.findings[event.row_key.value]
        self.show_finding_detail(finding)

    def load_file(self, file_path: str) -> None:
        """Load file content into code view."""
        code_view = self.query_one("#code-view", TextArea)
        try:
            content = Path(file_path).read_text()
            code_view.read_only = False
            code_view.text = content
            code_view.read_only = True
            self.current_file = file_path
        except FileNotFoundError:
            self.notify(f"File not found: {file_path}", severity="error")

    def show_finding_detail(self, finding) -> None:
        """Show finding details."""
        detail = self.query_one("#issue-detail", Static)
        detail.update(
            f"[bold]Issue[/bold]\n{finding.issue}\n\n"
            f"[bold]Severity[/bold]: {finding.severity}\n\n"
            f"[bold]Fix[/bold]\n{finding.fix}\n\n"
            f"[bold]Explanation[/bold]\n{finding.explanation}"
        )

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()
```

---

## Error Handling

### Engine Errors

```python
class EngineError(Exception):
    """Base engine error."""
    pass


class ModelLoadError(EngineError):
    """Model loading failed."""
    pass


class InferenceError(EngineError):
    """Inference failed."""
    pass


class TokenLimitError(EngineError):
    """Prompt exceeds context window."""
    pass
```

### Review Errors

```python
class ReviewError(Exception):
    """Base review error."""
    pass


class ParseError(ReviewError):
    """Failed to parse LLM response."""
    pass


class FileReadError(ReviewError):
    """Failed to read file."""
    pass
```

### Error Recovery

- **Model not found**: Prompt user to download GGUF model
- **Inference timeout**: Retry with shorter prompt (chunk file)
- **Parse failure**: Show raw text output as fallback
- **Empty response**: Request retry with different temperature
- **Context overflow**: Chunk file into smaller segments

---

## Edge Cases

| Case | Handling |
|------|----------|
| **Large files** | Chunk into context-sized segments |
| **Binary files** | Skip with notification |
| **Empty files** | Skip with notification |
| **Encoding errors** | Try UTF-8, then latin-1 |
| **No model** | Error with download instructions |
| **Slow inference** | Show progress indicator |
| **Invalid prompt response** | Fallback to raw text |
| **Rate limits** | N/A (local model) |

---

## Configuration File

```toml
# config.toml
[code_sentinel]
default_model = "codellama-7b-instruct.q4_k_m.gguf"
model_dir = "models"
n_ctx = 4096
n_gpu_layers = 0

focus = "all"
severity_threshold = "low"
max_issues = 50
temperature = 0.2

output_format = "tui"
show_line_numbers = true

dark_mode = true
```

---

## CLI Examples

```bash
# Install
pip install -e .

# Basic review
code-sentinel review src/auth.py

# Security focus
code-sentinel review src/auth.py --focus security

# JSON output
code-sentinel review src/auth.py --format json

# Specific model
code-sentinel review src/auth.py --model models/lexicorp-13b.q4_k_m.gguf

# Watch mode
code-sentinel watch src/ --glob "*.py"

# Show config
code-sentinel config --show
```

---

## Implementation Roadmap

### Phase 1: Core Engine
- [ ] Project setup (pyproject.toml, entry points)
- [ ] Config management
- [ ] Logging setup
- [ ] LlamaEngine wrapper
- [ ] Basic CLI commands

### Phase 2: Analysis
- [ ] Prompt templates
- [ ] ReviewAnalyzer class
- [ ] Response parsing
- [ ] Output formatters (JSON, text)

### Phase 3: TUI
- [ ] Main TUI app structure
- [ ] File tree widget
- [ ] Code view with TextArea
- [ ] Issues table
- [ ] Detail panel

### Phase 4: Polish
- [ ] Keyboard shortcuts
- [ ] Annotations inline
- [ ] Watch mode
- [ ] SARIF output
- [ ] Tests