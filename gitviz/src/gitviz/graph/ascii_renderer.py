"""ASCII character mapping for graph rendering."""

from dataclasses import dataclass
from typing import Literal

from .node import GraphNode


GRAPH_CHARS = {
    "pipe": "│",
    "dash": "-",
    "corner_down": "┌",
    "corner_up": "└",
    "merge_left": "┐",
    "merge_right": "┘",
    "split_left": "├",
    "split_right": "┤",
    "cross": "┼",
    "dot": "●",
    "empty": "○",
    "head": "*",
    "space": " ",
    "vertical_right": "├",
    "vertical_left": "┤",
    "down_left": "┌",
    "down_right": "┐",
    "up_left": "└",
    "up_right": "┘",
    "horizontal": "─",
}


@dataclass
class ColumnState:
    """State of a column at a given row."""

    char: str = " "
    color: str = "default"
    is_continuing: bool = False


class ASCIIRenderer:
    """Renders graph nodes as ASCII art."""

    def __init__(self, graph_width: int = 50):
        self.graph_width = graph_width

    def render_commit_row(
        self,
        node: GraphNode,
        prev_columns: list[ColumnState],
        max_col: int,
    ) -> tuple[str, list[ColumnState]]:
        """
        Render a single commit row.

        Returns:
            Tuple of (rendered_string, new_column_states)
        """
        num_cols = max(max_col + 1, len(prev_columns), node.column + 1)
        columns: list[ColumnState] = [ColumnState() for _ in range(num_cols)]

        for i, state in enumerate(prev_columns):
            if i < num_cols:
                columns[i] = state

        edges = self._compute_edges(node, num_cols)

        for edge in edges:
            if 0 <= edge.to_col < num_cols:
                char, edge_char = self._get_edge_chars(edge, node, num_cols)
                if edge_char != " ":
                    columns[edge.to_col] = ColumnState(
                        char=edge_char,
                        color=edge.color,
                        is_continuing=True,
                    )

        if 0 <= node.column < num_cols:
            columns[node.column] = ColumnState(
                char=node.symbol,
                color=node.color,
                is_continuing=False,
            )

        graph_part = self._render_graph(columns, node)

        return graph_part, columns

    def _compute_edges(
        self,
        node: GraphNode,
        num_cols: int,
    ) -> list:
        """Compute edge positions for node."""
        edges = []

        for edge in node.edges:
            edges.append(edge)

        return edges

    def _get_edge_chars(
        self,
        edge,
        node: GraphNode,
        num_cols: int,
    ) -> tuple[str, str]:
        """Get character for edge."""
        if edge.to_row > edge.from_row:
            if edge.to_col == edge.from_col:
                return "vertical", GRAPH_CHARS["pipe"]
            elif edge.to_col > edge.from_col:
                return "down_right", GRAPH_CHARS["down_right"]
            else:
                return "down_left", GRAPH_CHARS["down_left"]
        else:
            if edge.to_col == edge.from_col:
                return "vertical", GRAPH_CHARS["pipe"]
            elif edge.to_col > edge.from_col:
                return "up_right", GRAPH_CHARS["up_right"]
            else:
                return "up_left", GRAPH_CHARS["up_left"]

    def _render_graph(
        self,
        columns: list[ColumnState],
        node: GraphNode,
    ) -> str:
        """Render the graph portion of a commit row."""
        parts: list[str] = []
        spaces_since_last = 0

        for i, col in enumerate(columns):
            if i > node.column + 5:
                break

            if col.char != " " and col.is_continuing:
                parts.append(col.char)
                spaces_since_last = 0
            elif i == node.column:
                parts.append(node.symbol)
                spaces_since_last = 0
            else:
                parts.append(" ")
                spaces_since_last += 1

        return "".join(parts) + " "

    def render(
        self,
        nodes: list[GraphNode],
        max_cols: int | None = None,
    ) -> list[str]:
        """Render all nodes to strings."""
        if not nodes:
            return []

        result: list[str] = []
        prev_columns: list[ColumnState] = []

        max_col = max((n.column for n in nodes), default=0) + 1

        for node in nodes:
            graph_part, prev_columns = self.render_commit_row(node, prev_columns, max_col)
            result.append(graph_part)

        return result
