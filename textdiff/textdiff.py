#!/usr/bin/env python3
"""
TextDiff - CLI text diff/merge tool

Compares two text files and shows visual ASCII diffs with:
- Additions in green
- Deletions in red
- Unified diff output option
- Ignore whitespace option
"""

import sys
import argparse
import difflib


# ANSI color codes
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"
BOLD = "\033[1m"


def read_file(path: str) -> list[str]:
    """Read file and return lines as list."""
    try:
        with open(path, "rb") as f:
            content = f.read()
            # reject binary files
            if b"\x00" in content:
                print(f"Error: Binary file detected: {path}", file=sys.stderr)
                sys.exit(1)
            text = content.decode("utf-8")
            return text.splitlines(keepends=True)
    except FileNotFoundError:
        print(f"Error: File not found: {path}", file=sys.stderr)
        sys.exit(1)
    except UnicodeDecodeError:
        print(f"Error: File is not valid UTF-8: {path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading {path}: {e}", file=sys.stderr)
        sys.exit(1)


def normalize_whitespace(lines: list[str]) -> list[str]:
    """Normalize whitespace in lines for comparison."""
    return [line.rstrip() for line in lines]


def show_side_by_side_diff(
    old_lines: list[str], new_lines: list[str], ignore_whitespace: bool = False
) -> None:
    """Show side-by-side diff with colored additions/deletions."""
    if ignore_whitespace:
        old_lines = normalize_whitespace(old_lines)
        new_lines = normalize_whitespace(new_lines)

    diff = list(difflib.ndiff(old_lines, new_lines))

    print(f"\n{BOLD}TextDiff - Side by Side{RESET}")
    print("=" * 60)

    old_idx = 1
    new_idx = 1

    for line in diff:
        code = line[0]
        text = line[2:].rstrip("\n")
        if code == " ":
            # Unchanged line
            print(f"  {old_idx:4d} │ {text}")
            print(f"       │ {text}")
            old_idx += 1
            new_idx += 1
        elif code == "-":
            # Deletion
            print(f"{RED}{old_idx:4d} │ {text}{RESET}")
            print(f"       │ ")
            old_idx += 1
        elif code == "+":
            # Addition
            print(f"       │ ")
            print(f"{GREEN}       │ {text}{RESET}")
            new_idx += 1
        elif code == "?":
            # Skip indicator lines
            pass


def show_inline_diff(
    old_lines: list[str], new_lines: list[str], ignore_whitespace: bool = False
) -> None:
    """Show inline diff with colored additions/deletions."""
    if ignore_whitespace:
        old_lines = normalize_whitespace(old_lines)
        new_lines = normalize_whitespace(new_lines)

    diff = list(
        difflib.unified_diff(
            old_lines, new_lines, lineterm="", fromfile="a", tofile="b"
        )
    )

    if not diff:
        print(f"\n{BOLD}TextDiff - No differences{RESET}")
        print("=" * 60)
        print("Files are identical.")
        return

    print(f"\n{BOLD}TextDiff - Inline{RESET}")
    print("=" * 60)

    for line in diff:
        # Skip metadata lines
        if line.startswith("---") or line.startswith("+++"):
            print(f"{BOLD}{line}{RESET}")
        elif line.startswith("@@"):
            print(f"{YELLOW}{line}{RESET}")
        elif line.startswith("-"):
            print(f"{RED}{line}{RESET}")
        elif line.startswith("+"):
            print(f"{GREEN}{line}{RESET}")
        else:
            print(line)


def show_unified_diff(
    old_lines: list[str],
    new_lines: list[str],
    ignore_whitespace: bool = False,
    context: int = 3,
) -> None:
    """Show unified diff output."""
    if ignore_whitespace:
        old_lines = normalize_whitespace(old_lines)
        new_lines = normalize_whitespace(new_lines)

    file1_path = "a"
    file2_path = "b"

    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=file1_path,
        tofile=file2_path,
        lineterm="",
        n=context,
    )

    diff_lines = list(diff)

    if not diff_lines:
        print(f"\n{BOLD}TextDiff - Unified Output{RESET}")
        print("=" * 60)
        print("Files are identical.")
        return

    print(f"\n{BOLD}TextDiff - Unified Diff{RESET}")
    print("=" * 60)

    for line in diff_lines:
        # Skip metadata lines
        if line.startswith("---") or line.startswith("+++"):
            print(f"{BOLD}{line}{RESET}")
        elif line.startswith("@@"):
            print(f"{YELLOW}{line}{RESET}")
        elif line.startswith("-"):
            print(f"{RED}{line}{RESET}")
        elif line.startswith("+"):
            print(f"{GREEN}{line}{RESET}")
        else:
            print(line)


def main():
    parser = argparse.ArgumentParser(
        description="TextDiff - CLI text diff/merge tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  textdiff.py file1.txt file2.txt           # Side-by-side diff
  textdiff.py file1.txt file2.txt --inline    # Inline diff
  textdiff.py file1.txt file2.txt -u          # Unified diff output
  textdiff.py file1.txt file2.txt --ignore    # Ignore whitespace
  textdiff.py file1.txt file2.txt -u -i       # Combined options
        """,
    )

    parser.add_argument("file1", help="First file to compare")
    parser.add_argument("file2", help="Second file to compare")
    parser.add_argument(
        "-u", "--unified", action="store_true", help="Show unified diff output"
    )
    parser.add_argument(
        "-i",
        "--inline",
        action="store_true",
        help="Show inline diff (default is side-by-side)",
    )
    parser.add_argument(
        "-w",
        "--ignore-whitespace",
        action="store_true",
        help="Ignore whitespace differences",
    )
    parser.add_argument(
        "-c",
        "--context",
        type=int,
        default=3,
        help="Lines of context for unified diff (default: 3)",
    )
    parser.add_argument(
        "--no-color", action="store_true", help="Disable colored output"
    )

    args = parser.parse_args()

    # Disable colors if requested
    global GREEN, RED, YELLOW, RESET, BOLD
    if args.no_color:
        GREEN = RED = YELLOW = RESET = BOLD = ""

    # Read files
    old_lines = read_file(args.file1)
    new_lines = read_file(args.file2)

    # Determine output mode
    if args.unified:
        show_unified_diff(old_lines, new_lines, args.ignore_whitespace, args.context)
    elif args.inline:
        show_inline_diff(old_lines, new_lines, args.ignore_whitespace)
    else:
        show_side_by_side_diff(old_lines, new_lines, args.ignore_whitespace)


if __name__ == "__main__":
    main()
