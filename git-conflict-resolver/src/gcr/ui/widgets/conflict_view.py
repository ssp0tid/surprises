"""3-way conflict view widget."""

from textual.widget import Widget
from textual.widgets import Static
from textual.containers import Horizontal, Vertical

from ...core.conflict import ConflictHunk


class ConflictView(Widget):
    """Widget displaying a 3-way conflict view."""

    CSS = """
    ConflictView {
        border: solid $primary;
        background: $surface;
        layout: horizontal;
    }

    .conflict-side {
        width: 1fr;
        height: 100%;
        background: $surface;
        border-right: solid $primary;
        padding: 1;
    }

    .conflict-side:last-child {
        border-right: none;
    }

    .side-label {
        text: $accent;
        bold: yes;
        background: $primary-darken-1;
        padding: 0 1;
    }

    .side-content {
        width: 100%;
        height: 100%;
        padding: 1;
        overflow-y: auto;
    }

    .ours { border-left: solid $success 3; }
    .theirs { border-left: solid $warning 3; }
    .base { border-left: solid $text 3; }
    """

    def __init__(self):
        super().__init__()
        self.conflicts: list[ConflictHunk] = []
        self.current_index: int = 0

    def compose(self):
        with Horizontal(id="panels"):
            with Vertical(id="ours-panel", classes="conflict-side ours"):
                yield Static("OURS", classes="side-label")
                yield Static(id="ours-content", classes="side-content")
            with Vertical(id="theirs-panel", classes="conflict-side theirs"):
                yield Static("THEIRS", classes="side-label")
                yield Static(id="theirs-content", classes="side-content")
            with Vertical(id="base-panel", classes="conflict-side base"):
                yield Static("BASE", classes="side-label")
                yield Static(id="base-content", classes="side-content")

    def load_conflicts(self, conflicts: list[ConflictHunk]) -> None:
        self.conflicts = conflicts
        self.current_index = 0

    def show_conflict(self, index: int) -> None:
        if not self.conflicts or index >= len(self.conflicts):
            return

        self.current_index = index
        hunk = self.conflicts[index]

        ours_content = "".join(hunk.ours_content)
        theirs_content = "".join(hunk.theirs_content)
        base_content = "".join(hunk.base_content) if hunk.base_content else "(no base)"

        self.query_one("#ours-content", Static).update(ours_content)
        self.query_one("#theirs-content", Static).update(theirs_content)
        self.query_one("#base-content", Static).update(base_content)
