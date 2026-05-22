#!/usr/bin/env python3
"""Lines-of-code counter CLI — entry point."""

import argparse
import sys
from pathlib import Path

from counter import FileStats, LangSummary, count_directory, count_file, summarize_by_language
from formatters import (
    format_csv,
    format_csv_by_file,
    format_json,
    format_json_by_file,
    format_table,
    format_table_by_file,
)
from gitignore import parse_gitignore
from languages import get_language


SORT_KEYS = {
    "code": lambda s: s.code,
    "files": lambda s: s.files,
    "comments": lambda s: s.comments,
    "blanks": lambda s: s.blanks,
    "name": lambda s: s.language.lower(),
}

SORT_KEYS_FILE = {
    "code": lambda s: s.code,
    "comments": lambda s: s.comments,
    "blanks": lambda s: s.blanks,
    "name": lambda s: s.path.lower(),
}


def build_total(summaries: list[LangSummary]) -> LangSummary:
    files = sum(s.files for s in summaries)
    code = sum(s.code for s in summaries)
    comments = sum(s.comments for s in summaries)
    blanks = sum(s.blanks for s in summaries)
    return LangSummary("Total", files, code, comments, blanks, code + comments + blanks)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="loc",
        description="Count lines of code, comments, and blanks by language.",
    )
    parser.add_argument(
        "path", nargs="?", default=".", help="Directory or file to analyze (default: current dir)"
    )
    parser.add_argument(
        "-f", "--format", choices=["table", "json", "csv"], default="table", help="Output format"
    )
    parser.add_argument(
        "--by-file", action="store_true", help="Show per-file breakdown instead of per-language summary"
    )
    parser.add_argument(
        "--exclude", nargs="*", default=[], help="Additional directory names to exclude"
    )
    parser.add_argument(
        "--no-gitignore", action="store_true", help="Don't respect .gitignore patterns"
    )
    parser.add_argument(
        "--sort",
        choices=["code", "files", "comments", "blanks", "name"],
        default="code",
        help="Sort by column (default: code)",
    )
    args = parser.parse_args()

    target = Path(args.path).resolve()
    if not target.exists():
        print(f"Error: path '{args.path}' does not exist.", file=sys.stderr)
        return 1

    if target.is_file():
        lang_def = get_language(target.name, target.suffix)
        if lang_def is None:
            print(f"Error: unrecognized language for '{target.name}'.", file=sys.stderr)
            return 1
        file_stats = [count_file(target, lang_def)]
    else:
        ignore_patterns: list[str] = []
        if not args.no_gitignore:
            ignore_patterns = parse_gitignore(target)
        exclude_dirs = set(args.exclude)
        file_stats = count_directory(target, ignore_patterns, exclude_dirs)

    if not file_stats:
        print("No source files found.", file=sys.stderr)
        return 0

    if args.by_file:
        if args.sort == "files":
            print("Warning: --sort files is not applicable with --by-file; sorting by code.", file=sys.stderr)
            args.sort = "code"
        sort_key = SORT_KEYS_FILE.get(args.sort, SORT_KEYS_FILE["code"])
        reverse = args.sort != "name"
        file_stats.sort(key=sort_key, reverse=reverse)

        if args.format == "json":
            output = format_json_by_file(file_stats)
        elif args.format == "csv":
            output = format_csv_by_file(file_stats)
        else:
            output = format_table_by_file(file_stats)
    else:
        summaries = summarize_by_language(file_stats)
        sort_key = SORT_KEYS.get(args.sort, SORT_KEYS["code"])
        reverse = args.sort != "name"
        summaries.sort(key=sort_key, reverse=reverse)
        total = build_total(summaries)

        if args.format == "json":
            output = format_json(summaries, total)
        elif args.format == "csv":
            output = format_csv(summaries, total)
        else:
            output = format_table(summaries, total)

    print(output)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)
