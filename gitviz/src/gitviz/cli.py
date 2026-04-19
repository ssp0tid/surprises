"""CLI argument parsing and entry point."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional

from .models.errors import NotAGitRepository
from .parser.repository_loader import RepositoryLoader
from .ui.app import GitVizApp


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="gitviz",
        description="Interactive terminal UI Git history visualizer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=None,
        help="Path to git repository (default: current directory)",
    )

    parser.add_argument(
        "--max-commits",
        type=int,
        default=None,
        help="Maximum number of commits to load",
    )

    parser.add_argument(
        "--branch",
        "-b",
        action="append",
        dest="branches",
        help="Focus on specific branch (can be specified multiple times)",
    )

    parser.add_argument(
        "--since",
        help="Show commits since date (YYYY-MM-DD)",
    )

    parser.add_argument(
        "--until",
        help="Show commits until date (YYYY-MM-DD)",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Include all refs (not just current branch)",
    )

    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colors",
    )

    parser.add_argument(
        "--no-git",
        action="store_true",
        help="Do not use git CLI (use pure Python parser)",
    )

    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version="%(prog)s 1.0.0",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )

    return parser


async def async_main(args: argparse.Namespace) -> int:
    """Async main function."""
    repo_path = args.path or Path.cwd()

    discovered = RepositoryLoader.discover(repo_path)
    if not discovered:
        print(f"Error: Not a git repository: {repo_path}", file=sys.stderr)
        return 1

    repo_git_dir = discovered.parent if discovered.name == ".git" else discovered

    try:
        app = GitVizApp(
            repo_git_dir,
            max_commits=args.max_commits,
        )
        await app.run_async()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.debug:
            import traceback

            traceback.print_exc()
        return 1

    return 0


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    return asyncio.run(async_main(args))


if __name__ == "__main__":
    sys.exit(main())
