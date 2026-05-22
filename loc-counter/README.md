# loc-counter

A fast lines-of-code counter CLI that breaks down source files into code, comments, and blank lines by language.

## Requirements

- Python 3.9+
- No external dependencies (stdlib only)

## Usage

```bash
# Count current directory
python loc.py

# Count a specific directory
python loc.py /path/to/project

# Count a single file
python loc.py src/main.py

# JSON output
python loc.py -f json

# CSV output
python loc.py -f csv

# Per-file breakdown
python loc.py --by-file

# Sort by files count
python loc.py --sort files

# Exclude additional directories
python loc.py --exclude vendor third_party

# Ignore .gitignore patterns
python loc.py --no-gitignore
```

## Options

| Flag | Description |
|------|-------------|
| `path` | Directory or file to analyze (default: `.`) |
| `-f, --format` | Output format: `table`, `json`, `csv` (default: `table`) |
| `--by-file` | Show per-file breakdown instead of per-language summary |
| `--exclude` | Additional directory names to exclude |
| `--no-gitignore` | Don't respect .gitignore patterns |
| `--sort` | Sort by: `code`, `files`, `comments`, `blanks`, `name` (default: `code`). Note: `files` is ignored with `--by-file`. |

## Supported Languages

Python, JavaScript, TypeScript, Go, Rust, C, C++, Java, Ruby, Shell, HTML, CSS, SCSS, SQL, Lua, Haskell, YAML, TOML, Markdown, JSON, Kotlin, Swift, PHP, Makefile, Dockerfile.

## Example Output

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

## Running Tests

```bash
python test_loc.py
```

## Features

- 25+ languages recognized by file extension
- State machine for accurate block comment counting
- Respects .gitignore patterns + default exclusions (.git, node_modules, __pycache__, etc.)
- Multiple output formats (ASCII table, JSON, CSV)
- Per-file or per-language views
- Sortable output
- Binary file detection (skips non-text files)
- Zero external dependencies
