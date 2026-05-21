"""Main editor screen for resolving conflicts."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static
from textual.containers import Horizontal, Vertical
from textual.binding import Binding

from ..widgets.conflict_view import ConflictView
from ..widgets.hint_panel import HintPanel
from ..widgets.status_bar import StatusBar
from ...core.conflict import ConflictFile, ResolutionChoice
from ...core.hints import HintEngine


class EditorScreen(Screen):
    """Main conflict editor screen."""

    BINDINGS = [
        Binding("j", "next_conflict", "Next"),
        Binding("k", "prev_conflict", "Prev"),
        Binding("o", "accept_ours", "Ours"),
        Binding("i", "accept_theirs", "Theirs"),
        Binding("e", "edit_manual", "Edit"),
        Binding("h", "toggle_hints", "Hints"),
        Binding("w", "write_file", "Write"),
        Binding("ctrl+w", "write_file", "Write"),
        Binding("u", "undo", "Undo"),
        Binding("b", "go_back", "Back"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.current_conflict_index: int = 0
        self.undo_stack: list[tuple[int, ResolutionChoice]] = []
        self.redo_stack: list[tuple[int, ResolutionChoice]] = []
        self.hint_engine = HintEngine()
        self.show_hints = True

    def compose(self) -> ComposeResult:
        yield Header("Resolve Conflicts")
        with Horizontal():
            with Vertical(size=60):
                yield Static("CONFLICTS", classes="section-title")
                yield ConflictView(id="conflict-view")
            with Vertical(size=40):
                yield Static("HINTS", classes="section-title")
                yield HintPanel(id="hint-panel")
        with Horizontal(id="action-bar"):
            yield Button("Ours (o)", id="btn-ours", variant="primary")
            yield Button("Theirs (i)", id="btn-theirs", variant="primary")
            yield Button("Edit (e)", id="btn-edit", variant="default")
            yield Button("Write (w)", id="btn-write", variant="success")
        yield StatusBar(id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        self.load_conflicts()

    def load_conflicts(self) -> None:
        app = self.app
        if not app.conflict_files:
            self.notify("No file loaded", severity="error")
            return

        conflict_file = app.get_current_file()
        if not conflict_file:
            return

        view = self.query_one("#conflict-view", ConflictView)
        view.load_conflicts(conflict_file.conflicts)

        if conflict_file.conflicts:
            view.show_conflict(0)
            self._update_hint()
            self._update_status()

    def get_current_conflict(self):
        app = self.app
        conflict_file = app.get_current_file()
        if not conflict_file:
            return None
        return conflict_file.get_conflict_at(self.current_conflict_index)

    def _update_hint(self) -> None:
        if not self.show_hints:
            return
        hunk = self.get_current_conflict()
        if not hunk:
            return
        hint = self.hint_engine.analyze(hunk)
        panel = self.query_one("#hint-panel", HintPanel)
        panel.set_hint(hint)

    def _update_status(self) -> None:
        app = self.app
        conflict_file = app.get_current_file()
        if not conflict_file:
            return
        status = self.query_one("#status-bar", StatusBar)
        status.update(
            file=conflict_file.path,
            index=self.current_conflict_index,
            total=len(conflict_file.conflicts),
            resolved=conflict_file.resolved_count,
        )

    def action_next_conflict(self) -> None:
        app = self.app
        conflict_file = app.get_current_file()
        if not conflict_file:
            return
        if self.current_conflict_index < len(conflict_file.conflicts) - 1:
            self.current_conflict_index += 1
            view = self.query_one("#conflict-view", ConflictView)
            view.show_conflict(self.current_conflict_index)
            self._update_hint()
            self._update_status()

    def action_prev_conflict(self) -> None:
        if self.current_conflict_index > 0:
            self.current_conflict_index -= 1
            view = self.query_one("#conflict-view", ConflictView)
            view.show_conflict(self.current_conflict_index)
            self._update_hint()
            self._update_status()

    def action_accept_ours(self) -> None:
        self._resolve_conflict(ResolutionChoice.OURS)

    def action_accept_theirs(self) -> None:
        self._resolve_conflict(ResolutionChoice.THEIRS)

    def _resolve_conflict(self, choice: ResolutionChoice) -> None:
        app = self.app
        conflict_file = app.get_current_file()
        if not conflict_file:
            return
        conflict_file.update_conflict(self.current_conflict_index, choice)
        self._update_status()
        self.notify(f"Resolved with {choice.name}")
        if self.current_conflict_index < len(conflict_file.conflicts) - 1:
            self.action_next_conflict()

    def action_edit_manual(self) -> None:
        self.notify("Edit mode - not yet implemented", severity="warning")

    def action_toggle_hints(self) -> None:
        self.show_hints = not self.show_hints
        panel = self.query_one("#hint-panel", HintPanel)
        panel.display = "block" if self.show_hints else "none"

    def action_write_file(self) -> None:
        app = self.app
        conflict_file = app.get_current_file()
        if not conflict_file:
            return
        if conflict_file.unresolved_count > 0:
            self.notify(f"{conflict_file.unresolved_count} conflicts remain", severity="warning")
            return

        content = conflict_file.rebuild_content()
        try:
            with open(conflict_file.path, "w") as f:
                f.write(content)
            self.notify("File saved successfully", severity="success")
        except OSError as e:
            self.notify(f"Cannot write file: {e}", severity="error")

    def action_undo(self) -> None:
        self.notify("Undo not yet implemented", severity="warning")

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-ours":
            self.action_accept_ours()
        elif event.button.id == "btn-theirs":
            self.action_accept_theirs()
        elif event.button.id == "btn-edit":
            self.action_edit_manual()
        elif event.button.id == "btn-write":
            self.action_write_file()
