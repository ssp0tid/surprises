"""Main entry point for Crono application."""

from crono.app import CronoApp


def main() -> None:
    """Run the Crono application."""
    app = CronoApp()
    app.run()


if __name__ == "__main__":
    main()
