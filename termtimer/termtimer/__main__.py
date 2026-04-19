"""Main entry point for TermTimer."""

import asyncio
from termtimer.app import TermTimerApp


def main() -> None:
    """Run the TermTimer application."""
    app = TermTimerApp()
    app.run()


if __name__ == "__main__":
    main()