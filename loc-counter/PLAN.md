# loc-counter

**A fast lines-of-code counter CLI that breaks down source files into code, comments, and blank lines by language.**

## Tech Stack

- Python 3 (stdlib only — no external dependencies)
- `argparse` for CLI
- `pathlib` for file traversal
- `json` for JSON output
- `csv` for CSV output

## Constraints

- Zero external dependencies — stdlib only
- Must respect `.gitignore` patterns (parse `.gitignore` manually using `fnmatch`)
- Must handle binary file detection gracefully (skip them)
- Single entry point: `loc.py`

## File Structure

```
loc-counter/
├── PLAN.md
├── README.md
├── loc.py              # Entry point — CLI interface
├── counter.py          # Core counting logic
├── languages.py        # Language definitions (extensions, comment syntax)
├── gitignore.py        # .gitignore pattern parser
├── formatters.py       # Output formatters (table, JSON, CSV)
└── test_loc.py         # Basic tests
```

## Language Definitions (`languages.py`)

Define a `LANGUAGES` dict mapping file extensions to language info:

```python
@dataclass
class LangDef:
    name: str
    extensions: list[str]
    line_comment: str | None       # e.g. "//" or "#"
    block_comment_start: str | None  # e.g. "/*"
    block_comment_end: str | None    # e.g. "*/"
```

Support at minimum:
- Python (.py) — `#`, no block comments (triple-quote strings don't count as comments)
- JavaScript (.js, .mjs) — `//`, `/* */`
- TypeScript (.ts, .tsx) — `//`, `/* */`
- Go (.go) — `//`, `/* */`
- Rust (.rs) — `//`, `/* */`
- C (.c, .h) — `//`, `/* */`
- C++ (.cpp, .hpp, .cc) — `//`, `/* */`
- Java (.java) — `//`, `/* */`
- Ruby (.rb) — `#`, `=begin =end`
- Shell (.sh, .bash, .zsh) — `#`
- HTML (.html, .htm) — `<!-- -->`
- CSS (.css) — `/* */`
- SCSS (.scss) — `//`, `/* */`
- SQL (.sql) — `--`, `/* */`
- Lua (.lua) — `--`, `--[[ ]]`
- Haskell (.hs) — `--`, `{- -}`
- YAML (.yml, .yaml) — `#`
- TOML (.toml) — `#`
- Markdown (.md) — no comments (all lines are code)
- JSON (.json) — no comments
- Makefile (Makefile) — `#`
- Dockerfile (Dockerfile) — `#`
- Kotlin (.kt) — `//`, `/* */`
- Swift (.swift) — `//`, `/* */`
- PHP (.php) — `//`, `#`, `/* */`

## Core Counting Logic (`counter.py`)

```python
@dataclass
class FileStats:
    path: str
    language: str
    code: int
    comments: int
    blanks: int
    total: int  # code + comments + blanks

@dataclass
class LangSummary:
    language: str
    files: int
    code: int
    comments: int
    blanks: int
    total: int

def count_file(filepath: Path, lang_def: LangDef) -> FileStats:
    """Count lines in a single file. Handle block comments state machine."""
    ...

def count_directory(root: Path, ignore_patterns: list[str], exclude_dirs: set[str]) -> list[FileStats]:
    """Walk directory, skip ignored/binary files, count each recognized file."""
    ...

def summarize_by_language(file_stats: list[FileStats]) -> list[LangSummary]:
    """Aggregate file stats into per-language summaries."""
    ...
```

Counting algorithm for each file:
1. Read file line by line
2. Track `in_block_comment` state (bool)
3. For each line:
   - Strip whitespace → if empty, increment blanks
   - If `in_block_comment`: check for block end marker, increment comments
   - If line starts with line comment prefix: increment comments
   - If line contains block comment start: enter block state, increment comments
   - Otherwise: increment code
4. Handle edge cases: inline comments after code count as code lines

## .gitignore Parser (`gitignore.py`)

```python
def parse_gitignore(root: Path) -> list[str]:
    """Read .gitignore from root, return list of patterns."""
    ...

def is_ignored(path: Path, root: Path, patterns: list[str]) -> bool:
    """Check if path matches any gitignore pattern using fnmatch."""
    ...
```

Always ignore by default: `.git/`, `node_modules/`, `__pycache__/`, `.venv/`, `venv/`, `dist/`, `build/`, `.tox/`

## Output Formatters (`formatters.py`)

```python
def format_table(summaries: list[LangSummary], total: LangSummary) -> str:
    """Rich ASCII table with aligned columns, separator lines, totals row."""
    # Header: Language | Files | Code | Comments | Blanks | Total
    # Separator: ─────────
    # Rows sorted by code lines descending
    # Footer: Total row
    ...

def format_json(summaries: list[LangSummary], total: LangSummary) -> str:
    """JSON output with languages array and total object."""
    ...

def format_csv(summaries: list[LangSummary], total: LangSummary) -> str:
    """CSV with header row."""
    ...
```

## CLI Interface (`loc.py`)

```python
def main():
    parser = argparse.ArgumentParser(
        prog="loc",
        description="Count lines of code, comments, and blanks by language."
    )
    parser.add_argument("path", nargs="?", default=".",
                        help="Directory or file to analyze (default: current dir)")
    parser.add_argument("-f", "--format", choices=["table", "json", "csv"],
                        default="table", help="Output format")
    parser.add_argument("--by-file", action="store_true",
                        help="Show per-file breakdown instead of per-language summary")
    parser.add_argument("--exclude", nargs="*", default=[],
                        help="Additional directory names to exclude")
    parser.add_argument("--no-gitignore", action="store_true",
                        help="Don't respect .gitignore patterns")
    parser.add_argument("--sort", choices=["code", "files", "comments", "blanks", "name"],
                        default="code", help="Sort by column (default: code)")
    args = parser.parse_args()
    ...
```

## Features

1. **Multi-language detection** — 25+ languages recognized by extension
2. **Accurate comment counting** — state machine handles block comments, inline comments, nested edge cases
3. **Respects .gitignore** — parses project's .gitignore + default exclusions
4. **Multiple output formats** — rich ASCII table (default), JSON, CSV
5. **Per-file or per-language** — `--by-file` flag for granular view
6. **Sortable output** — sort by code, files, comments, blanks, or name
7. **Binary file detection** — skips non-text files gracefully
8. **Zero dependencies** — runs on any Python 3.9+ system
9. **Fast** — single-pass line counting, no regex for hot path

## Example Output (table format)

```
───────────────────────────────────────────────────────────────────
 Language       Files      Code   Comments     Blanks      Total
───────────────────────────────────────────────────────────────────
 Python            12      1847        234        312       2393
 JavaScript         8       956         89        145       1190
 TypeScript         3       412         56         78        546
 YAML               4        89         12         15        116
───────────────────────────────────────────────────────────────────
 Total             27      3304        391        550       4245
───────────────────────────────────────────────────────────────────
```
