"""Main Textual Application class for TermTimer."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer

from termtimer.screens.home import HomeScreen
from termtimer.screens.countdown import CountdownScreen
from termtimer.screens.stopwatch import StopwatchScreen
from termtimer.screens.pomodoro import PomodoroScreen
from termtimer.screens.alarm import AlarmScreen


class TermTimerApp(App):
    """Main TermTimer application."""

    CSS_PATH = "css/styles.tcss"
    TITLE = "TermTimer"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("1", "switch_mode('countdown')", "Countdown"),
        Binding("2", "switch_mode('stopwatch')", "Stopwatch"),
        Binding("3", "switch_mode('pomodoro')", "Pomodoro"),
        Binding("4", "switch_mode('alarm')", "Alarm"),
        Binding("escape", "show_home", "Home"),
        Binding("?", "show_help", "Help"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.current_mode = "home"

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header()
        yield Footer()

    def on_mount(self) -> None:
        """Handle app mount."""
        self.install_screen(HomeScreen(), name="home")
        self.install_screen(CountdownScreen(), name="countdown")
        self.install_screen(StopwatchScreen(), name="stopwatch")
        self.install_screen(PomodoroScreen(), name="pomodoro")
        self.install_screen(AlarmScreen(), name="alarm")
        self.push_screen("home")

    def action_switch_mode(self, mode: str) -> None:
        """Switch to a specific mode screen."""
        self.current_mode = mode
        self.push_screen(mode)

    def action_show_home(self) -> None:
        """Return to home screen."""
        self.current_mode = "home"
        self.push_screen("home")

    def action_show_help(self) -> None:
        """Show help overlay."""
        self.push_screen("home")

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()


# Entry point for python -m termtimer
if __name__ == "__main__":
    from termtimer.__main__ import main
    main()