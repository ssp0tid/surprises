"""Hint panel widget for displaying resolution suggestions."""

from textual.widget import Widget
from textual.widgets import Static

from ...core.hints import ConflictHint, HintType


class HintPanel(Widget):
    """Widget displaying automated hints for conflict resolution."""

    CSS = """
    HintPanel {
        border: solid $primary;
        background: $surface;
        padding: 1;
    }

    #hint-type {
        text: $accent;
        bold: yes;
        margin-bottom: 1;
    }

    #confidence {
        margin-bottom: 1;
    }

    #explanation {
        width: 100%;
    }

    .high-confidence {
        color: $success;
    }

    .medium-confidence {
        color: $warning;
    }

    .low-confidence {
        color: $text-muted;
    }
    """

    def __init__(self):
        super().__init__()
        self.current_hint: ConflictHint | None = None

    def compose(self):
        yield Static("No hint available", id="hint-content")

    def set_hint(self, hint: ConflictHint) -> None:
        self.current_hint = hint

        if hint.confidence >= 0.9:
            conf_class = "high-confidence"
        elif hint.confidence >= 0.5:
            conf_class = "medium-confidence"
        else:
            conf_class = "low-confidence"

        content = f"[{hint.hint_type.name}]\n\n"
        content += f"Confidence: {hint.confidence:.0%}\n\n"
        if hint.suggested_choice:
            content += f"Suggested: {hint.suggested_choice}\n\n"
        content += hint.explanation

        self.query_one("#hint-content", Static).update(content)
