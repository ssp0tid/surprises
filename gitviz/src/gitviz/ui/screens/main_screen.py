"""Main screen for graph visualization."""

from datetime import datetime
from typing import TYPE_CHECKING

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Header, Footer

from ..widgets.graph_widget import GraphWidget
from ..widgets.detail_panel import DetailPanel
from ..widgets.search_bar import SearchBar
from ..widgets.status_bar import StatusBar
from ...graph.node import GraphNode
from ...graph.layout import GraphLayout
from ...graph.ascii_renderer import ASCIIRenderer
from ...models.commit import Commit

if TYPE_CHECKING:
    from ..app import GitVizApp


class MainScreen(Screen):
    """Main graph visualization screen."""

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("j", "cursor_down", "Down"),
        Binding("k", "cursor_up", "Up"),
        Binding("g", "go_top", "Top"),
        Binding("G", "go_bottom", "Bottom"),
        Binding("/", "focus_search", "Search"),
        Binding("d", "show_diff", "Diff"),
        Binding("c", "copy_hash", "Copy"),
        Binding("h", "scroll_left", "Left"),
        Binding("l", "scroll_right", "Right"),
        Binding("left", "scroll_left", ""),
        Binding("right", "scroll_right", ""),
        Binding("up", "cursor_up", ""),
        Binding("down", "cursor_down", ""),
        Binding("pageup", "page_up", ""),
        Binding("pagedown", "page_down", ""),
        Binding("escape", "clear_search", ""),
        Binding("ctrl+c", "quit", ""),
    ]

    def __init__(self, app: "GitVizApp"):
        super().__init__()
        self.gitviz_app = app
        self.graph_widget: GraphWidget | None = None
        self.detail_panel: DetailPanel | None = None
        self.search_bar: SearchBar | None = None
        self.status_bar: StatusBar | None = None
        self.graph_nodes: list[GraphNode] = []
        self.selected_index: int = 0
        self._search_active: bool = False

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        yield Header()
        yield SearchBar()
        yield GraphWidget()
        yield DetailPanel()
        yield StatusBar()

    def on_mount(self) -> None:
        """Initialize screen after mount."""
        self.graph_widget = self.query_one("#graph-panel", GraphWidget)
        self.detail_panel = self.query_one("#detail-panel", DetailPanel)
        self.search_bar = self.query_one("#search-bar", SearchBar)
        self.status_bar = self.query_one("#status-bar", StatusBar)

        self.graph_widget.focus()
        self._load_commits()

    def _load_commits(self) -> None:
        """Load and display commits."""
        if not self.gitviz_app.repository:
            return

        layout = GraphLayout(self.gitviz_app.repository)
        self.graph_nodes = layout.compute_layout(limit=self.gitviz_app.max_commits)

        renderer = ASCIIRenderer()
        rows = self._render_nodes(renderer)
        self.graph_widget.set_rows(rows)

        self.status_bar.set_repo_info(
            str(self.gitviz_app.repo_path),
            len(self.graph_nodes),
            len(self.gitviz_app.repository.branches),
        )

        if self.graph_nodes:
            self._update_detail_panel(0)

    def _render_nodes(self, renderer: ASCIIRenderer) -> list:
        """Render graph nodes to text rows."""
        rows = []

        for i, node in enumerate(self.graph_nodes):
            commit = node.commit
            if not commit:
                continue

            graph_col = "│ " * node.column
            symbol = node.symbol

            if node.is_head:
                graph_str = f"{graph_col}[{symbol}]"
            else:
                graph_str = f"{graph_col}[{symbol}]"

            author = commit.author.name if commit.author else "Unknown"
            date = self._format_date(commit.author_time)

            branch_info = ""
            branches = self.gitviz_app.repository.get_branches_for_commit(node.oid)
            if branches:
                branch_names = [b.full_name for b in branches[:2]]
                branch_info = f" ({', '.join(branch_names)})"

            row_text = f"{graph_str} {commit.short_oid} {author:<20} {date:<12} {commit.short_message}{branch_info}"
            rows.append(row_text)

        return rows

    def _format_date(self, timestamp: int) -> str:
        """Format timestamp to readable date."""
        if timestamp == 0:
            return "unknown"
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d")

    def _update_detail_panel(self, index: int) -> None:
        """Update detail panel for selected commit."""
        if 0 <= index < len(self.graph_nodes):
            node = self.graph_nodes[index]
            commit = node.commit
            if not commit:
                return

            branches = self.gitviz_app.repository.get_branches_for_commit(node.oid)
            tags = self.gitviz_app.repository.get_tags_for_commit(node.oid)

            info = {
                "hash": f"{commit.short_oid} ({commit.full_oid})",
                "author": str(commit.author) if commit.author else "Unknown",
                "date": datetime.fromtimestamp(commit.author_time).strftime("%Y-%m-%d %H:%M:%S"),
                "message": commit.message,
                "branches": [b.full_name for b in branches],
                "tags": [t.name for t in tags],
                "parents": [p[:7].hex() for p in commit.parents],
                "is_merge": commit.is_merge,
            }

            self.detail_panel.set_commit(info)

    def cursor_up(self) -> None:
        """Move selection up."""
        if self.graph_widget:
            self.graph_widget.cursor_up()

    def cursor_down(self) -> None:
        """Move selection down."""
        if self.graph_widget:
            self.graph_widget.cursor_down()

    def go_top(self) -> None:
        """Go to first commit."""
        if self.graph_widget:
            self.graph_widget.go_top()

    def go_bottom(self) -> None:
        """Go to last commit."""
        if self.graph_widget:
            self.graph_widget.go_bottom()

    def page_up(self) -> None:
        """Page up."""
        if self.graph_widget:
            self.graph_widget.page_up()

    def page_down(self) -> None:
        """Page down."""
        if self.graph_widget:
            self.graph_widget.page_down()

    def focus_search(self) -> None:
        """Focus search bar."""
        if self.search_bar:
            self.search_bar.focus()
            self._search_active = True

    def clear_search(self) -> None:
        """Clear search and return to graph."""
        if self._search_active and self.search_bar:
            self.search_bar.blur()
            self._search_active = False
        if self.graph_widget:
            self.graph_widget.focus()

    def show_diff(self) -> None:
        """Show diff for selected commit."""
        if 0 <= self.selected_index < len(self.graph_nodes):
            node = self.graph_nodes[self.selected_index]
            self.app.push_screen("diff")

    def copy_hash(self) -> None:
        """Copy commit hash to clipboard."""
        if 0 <= self.selected_index < len(self.graph_nodes):
            node = self.graph_nodes[self.selected_index]
            commit = node.commit
            if commit:
                self.app.clipboard.copy(commit.short_oid)

    def scroll_left(self) -> None:
        """Scroll graph left."""
        pass

    def scroll_right(self) -> None:
        """Scroll graph right."""
        pass

    def on_graph_widget_row_selected(self, event) -> None:
        """Handle row selection."""
        self.selected_index = event.row_index
        self._update_detail_panel(event.row_index)

    def on_search_bar_search_submit(self, event) -> None:
        """Handle search submission."""
        query = event.query.lower()
        if not query:
            return

        for i, node in enumerate(self.graph_nodes):
            if not node.commit:
                continue
            commit = node.commit
            if query in commit.short_oid.lower():
                self.selected_index = i
                if self.graph_widget:
                    self.graph_widget.set_selected(i)
                self._update_detail_panel(i)
                break
            if commit.author and query in commit.author.name.lower():
                self.selected_index = i
                if self.graph_widget:
                    self.graph_widget.set_selected(i)
                self._update_detail_panel(i)
                break
            if query in commit.message.lower():
                self.selected_index = i
                if self.graph_widget:
                    self.graph_widget.set_selected(i)
                self._update_detail_panel(i)
                break

    def on_search_bar_search_clear(self) -> None:
        """Handle search clear."""
        self._load_commits()
