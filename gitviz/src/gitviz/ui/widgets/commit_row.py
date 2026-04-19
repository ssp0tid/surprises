"""Commit row widget for displaying individual commits."""

from datetime import datetime
from typing import TYPE_CHECKING

from rich.text import Text
from textual.widget import Widget
from textual.reactive import reactive

if TYPE_CHECKING:
    from ...graph.node import GraphNode


class CommitRow(Widget):
    """Widget for displaying a single commit row."""

    node: reactive["GraphNode | None"] = reactive(None)
    is_selected: reactive[bool] = reactive(False)

    def __init__(self, node: "GraphNode | None" = None):
        super().__init__()
        self.node = node

    def render(self) -> Text:
        """Render the commit row."""
        if self.node is None or self.node.commit is None:
            return Text(" " * 100)

        commit = self.node.commit
        graph_part = self._render_graph_part()

        parts = [graph_part]

        parts.append(f" {commit.short_oid} ")

        author_name = commit.author.name if commit.author else "Unknown"
        parts.append(f"{author_name:<20}")

        date_str = self._format_date(commit.author_time)
        parts.append(f"{date_str:<12}")

        parts.append(commit.short_message)

        if commit.is_merge:
            parts.append(" [merge]")

        result = Text("".join(parts))

        if self.is_selected:
            return Text(result, style="on #094771")
        elif self.node.is_head:
            return Text(result, style="bold #3794ff")
        elif self.node.is_on_branch:
            return Text(result, style=self.node.color)

        return Text(result, style="dim")

    def _render_graph_part(self) -> str:
        """Render the graph portion."""
        if self.node is None:
            return " " * 15

        col = self.node.column
        if col == 0:
            graph = f"[{self.node.symbol}]"
        else:
            graph = "│ " * col + f"[{self.node.symbol}]"

        return graph

    def _format_date(self, timestamp: int) -> str:
        """Format timestamp to readable date."""
        if timestamp == 0:
            return "unknown"

        dt = datetime.fromtimestamp(timestamp)
        now = datetime.now()
        diff = now - dt

        if diff.days == 0:
            if diff.seconds < 3600:
                return f"{diff.seconds // 60}m ago"
            return f"{diff.seconds // 3600}h ago"
        elif diff.days < 7:
            return f"{diff.days}d ago"
        elif diff.days < 30:
            return f"{diff.days // 7}w ago"
        elif diff.days < 365:
            return f"{diff.days // 30}mo ago"
        else:
            return f"{diff.days // 365}y ago"
