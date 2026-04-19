# TextDiff

A CLI text diff/merge tool that compares two text files and shows visual ASCII diffs.

## Features

- **Visual ASCII diffs** - Side-by-side or inline diff display
- **Colored output** - Additions in green, deletions in red
- **Unified diff output** - Standard unified format
- **Ignore whitespace** - Compare files ignoring whitespace differences

## Installation

```bash
chmod +x textdiff.py
./textdiff.py file1.txt file2.txt
```

Or add to your PATH:

```bash
cp textdiff.py /usr/local/bin/textdiff
```

## Usage

```bash
textdiff.py FILE1 FILE2 [OPTIONS]
```

### Options

| Flag | Description |
|------|-------------|
| `-u, --unified` | Show unified diff output |
| `-i, --inline` | Show inline diff (default is side-by-side) |
| `-w, --ignore-whitespace` | Ignore whitespace differences |
| `-c, --context N` | Lines of context for unified diff (default: 3) |
| `--no-color` | Disable colored output |

### Examples

Side-by-side diff (default):
```bash
textdiff.py file1.txt file2.txt
```

Inline diff:
```bash
textdiff.py file1.txt file2.txt --inline
```

Unified diff output:
```bash
textdiff.py file1.txt file2.txt -u
```

Ignore whitespace:
```bash
textdiff.py file1.txt file2.txt -w
```

Combined options:
```bash
textdiff.py file1.txt file2.txt -u -w
```

### Output Formats

**Side-by-side** (default):
- Left side: old file with deletions in red
- Right side: new file with additions in green

**Inline**:
- Lines prefixed with `-` (red): removed
- Lines prefixed with `+` (green): added

**Unified**:
- Standard unified diff format
- Context lines shown without color