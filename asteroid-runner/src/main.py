"""Entry point for Asteroid Runner."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app import AsteroidRunnerApp


def main() -> None:
    """Run the game."""
    app = AsteroidRunnerApp()
    app.run()


if __name__ == "__main__":
    main()
