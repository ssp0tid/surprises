"""Detail panel widget for showing commit details."""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from textual.widget import Widget


class DetailPanel(Widget):
    """Panel showing commit details."""

    def __init__(self):
        super().__init__(id="detail-panel")
        self.console = Console()
        self.commit_info: dict = {}

    def set_commit(self, info: dict) -> None:
        """Set commit information to display."""
        self.commit_info = info
        self.refresh()

    def clear(self) -> None:
        """Clear the detail panel."""
        self.commit_info = {}
        self.refresh()

    def render(self) -> Text:
        """Render the detail panel."""
        if not self.commit_info:
            return Text("Select a commit to view details", style="dim italic")

        lines: list[Text] = []

        if "hash" in self.commit_info:
            lines.append(Text(f"Hash: {self.commit_info['hash']}", style="bold cyan"))

        if "author" in self.commit_info:
            lines.append(Text(f"Author: {self.commit_info['author']}"))

        if "date" in self.commit_info:
            lines.append(Text(f"Date: {self.commit_info['date']}"))

        if "branches" in self.commit_info:
            branches = self.commit_info["branches"]
            if branches:
                lines.append(Text(f"Branches: {', '.join(branches)}", style="green"))

        if "tags" in self.commit_info:
            tags = self.commit_info["tags"]
            if tags:
                lines.append(Text(f"Tags: {', '.join(tags)}", style="yellow"))

        if "message" in self.commit_info:
            lines.append(Text(""))
            lines.append(Text("Message:", style="bold"))
            lines.append(Text(self.commit_info["message"]))

        if "parents" in self.commit_info:
            lines.append(Text(""))
            lines.append(Text(f"Parents: {self.commit_info['parents']}"))

        if "is_merge" in self.commit_info and self.commit_info["is_merge"]:
            lines.append(Text("[MERGE COMMIT]", style="bold red"))

        return Text("\n").join(lines)
