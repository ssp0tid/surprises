"""Status bar widget for displaying file and conflict information."""

from textual.widget import Widget
from textual.widgets import Static


class StatusBar(Widget):
    """Widget displaying status information."""

    CSS = """
    StatusBar {
        height: 3;
        background: $primary-darken-1;
        padding: 1 2;
        layout: horizontal;
    }

    #file-info {
        width: 50;
    }

    #conflict-info {
        width: 30;
    }

    #resolved-info {
        width: 20;
        text: $success;
    }
    """

    def __init__(self):
        super().__init__()
        self.current_file: str = ""
        self.conflict_index: int = 0
        self.total_conflicts: int = 0
        self.resolved_count: int = 0

    def compose(self):
        yield Static("No file loaded", id="file-info")
        yield Static("Conflicts: 0/0", id="conflict-info")
        yield Static("Resolved: 0", id="resolved-info")

    def update(
        self,
        file: str = "",
        index: int = 0,
        total: int = 0,
        resolved: int = 0,
    ) -> None:
        self.current_file = file
        self.conflict_index = index
        self.total_conflicts = total
        self.resolved_count = resolved

        file_info = f"File: {file}" if file else "No file loaded"
        conflict_info = f"Conflict: {index + 1}/{total}" if total > 0 else "No conflicts"
        resolved_info = f"Resolved: {resolved}/{total}" if total > 0 else ""

        self.query_one("#file-info", Static).update(file_info)
        self.query_one("#conflict-info", Static).update(conflict_info)
        self.query_one("#resolved-info", Static).update(resolved_info)
