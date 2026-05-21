"""File picker screen for selecting conflicted files."""

import os
from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static, Tree
from textual.containers import Horizontal, Vertical
from textual import work

from ...core.parser import ConflictParser
from ...core.conflict import ConflictFile
from ...exceptions import NoConflictsError, FileError


def find_conflicted_files() -> list[Path]:
    """Find files with git conflict markers."""
    conflicted = []
    try:
        for root, dirs, files in os.walk("."):
            for f in files:
                path = Path(root) / f
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        content = fh.read()
                        if "<<<<<<<" in content and "=======" in content and ">>>>>>>" in content:
                            conflicted.append(path)
                except (UnicodeDecodeError, OSError):
                    continue
    except OSError:
        pass
    return sorted(conflicted, key=lambda p: str(p))


class FilePickerScreen(Screen):
    """Screen for selecting a file with conflicts to resolve."""

    CSS = """
    FilePickerScreen {
        align: center middle;
    }

    #container {
        width: 70;
        height: 80%;
        border: solid $primary;
        background: $surface;
    }

    #header {
        height: 3;
        background: $accent;
        color: $text;
        content-align: center middle;
    }

    #file-tree {
        height: 1fr;
        width: 100%;
        border: none;
    }

    #actions {
        height: 3;
        layout: horizontal;
        align: center middle;
    }
    """

    BINDINGS = [
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("enter", "select_file", "Select"),
        ("b", "go_back", "Back"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.conflicted_files: list[Path] = []
        self.selected_index: int = 0

    def compose(self) -> ComposeResult:
        yield Header("Select File to Resolve")
        with Horizontal(id="container"):
            with Vertical(id="file-tree"):
                yield Tree("Conflicted Files", id="tree")
            with Vertical(id="actions"):
                yield Button("Select", id="btn-select", variant="primary")
                yield Button("Back", id="btn-back", variant="default")
                yield Button("Quit", id="btn-quit", variant="error")
        yield Footer()

    def on_mount(self) -> None:
        self.load_files()

    def load_files(self) -> None:
        self.conflicted_files = find_conflicted_files()
        tree = self.query_one("#tree", Tree)
        tree.clear()
        if not self.conflicted_files:
            tree.root.label = "No conflicted files found"
            return
        for path in self.conflicted_files:
            tree.root.add(path.name)

    def action_cursor_down(self) -> None:
        if self.selected_index < len(self.conflicted_files) - 1:
            self.selected_index += 1
            self._update_selection()

    def action_cursor_up(self) -> None:
        if self.selected_index > 0:
            self.selected_index -= 1
            self._update_selection()

    def _update_selection(self) -> None:
        tree = self.query_one("#tree", Tree)
        tree.index = self.selected_index

    def action_select_file(self) -> None:
        if not self.conflicted_files:
            self.notify("No files to select", severity="warning")
            return
        self._open_editor(self.conflicted_files[self.selected_index])

    def _open_editor(self, path: Path) -> None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            self.notify(f"Cannot read file: {e}", severity="error")
            return

        parser = ConflictParser()
        result = parser.parse(content, str(path))

        if result.file.is_binary:
            self.notify("Cannot resolve binary files", severity="error")
            return

        if not result.file.conflicts:
            self.notify("No conflicts found in file", severity="warning")
            return

        app = self.app
        app.conflict_files = [result.file]
        app.current_file_index = 0
        app.push_screen("editor")

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-select":
            self.action_select_file()
        elif event.button.id == "btn-back":
            self.action_go_back()
        elif event.button.id == "btn-quit":
            self.app.exit()
