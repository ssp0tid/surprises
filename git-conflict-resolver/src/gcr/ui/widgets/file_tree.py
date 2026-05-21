"""File tree widget for browsing conflicted files."""

from pathlib import Path
from typing import Optional

from textual.widget import Widget
from textual.widgets import Tree


class FileTree(Widget):
    """Widget displaying a tree of conflicted files."""

    def __init__(self):
        super().__init__()
        self.files: list[Path] = []
        self.selected_index: int = 0

    def set_files(self, files: list[Path]) -> None:
        self.files = files
        self.refresh()

    def get_selected(self) -> Optional[Path]:
        if 0 <= self.selected_index < len(self.files):
            return self.files[self.selected_index]
        return None

    def select_next(self) -> None:
        if self.selected_index < len(self.files) - 1:
            self.selected_index += 1
            self.refresh()

    def select_prev(self) -> None:
        if self.selected_index > 0:
            self.selected_index -= 1
            self.refresh()
