"""Layout algorithm for git commit graph."""

from collections import defaultdict
from typing import Iterator

from ..models.commit import Commit
from ..models.repository import Repository
from .node import GraphNode, Edge


class GraphLayout:
    """Computes commit positions for ASCII graph rendering."""

    def __init__(self, repository: Repository):
        self.repo = repository
        self.columns: dict[bytes, int] = {}
        self.next_column = 0
        self.children_map: dict[bytes, list[bytes]] = defaultdict(list)
        self.column_parents: dict[int, bytes] = {}

        self._build_children_map()

    def _build_children_map(self) -> None:
        """Build map of commit -> children."""
        for oid, commit in self.repo.commits.items():
            for parent_oid in commit.parents:
                self.children_map[parent_oid].append(oid)

    def compute_layout(
        self,
        limit: int | None = None,
        start_oid: bytes | None = None,
    ) -> list[GraphNode]:
        """
        Compute 2D layout for all commits.

        Algorithm (pvigier-based):
        1. Topological sort commits (children before parents)
        2. Assign columns to branch lines
        3. Track active columns for branch continuation
        4. Generate GraphNode list with position data

        Returns:
            List of GraphNode sorted by row (top to bottom)
        """
        commits = self._topological_sort(limit, start_oid)
        nodes: list[GraphNode] = []
        active_columns: dict[int, bytes] = {}
        column_edges: list[list[tuple[int, int, int, int]]] = []

        branch_colors = self._compute_branch_colors()

        for row, commit in enumerate(commits):
            col = self._assign_column(commit, active_columns)

            children = self.children_map.get(commit.oid, [])
            needs_new_column = len(children) > 1 and col not in self.column_parents

            if needs_new_column:
                self.column_parents[col] = commit.oid

            edges = []
            for child_oid in children:
                child_col = self.columns.get(child_oid)
                if child_col is not None:
                    edges.append(
                        Edge(
                            from_row=row,
                            from_col=col,
                            to_row=row + 1,
                            to_col=child_col,
                            color=branch_colors.get(col, "default"),
                        )
                    )

            for parent_oid in commit.parents:
                if parent_oid in self.columns:
                    parent_col = self.columns[parent_oid]
                    if parent_col != col:
                        edges.append(
                            Edge(
                                from_row=row,
                                from_col=col,
                                to_row=row - 1,
                                to_col=parent_col,
                                color=branch_colors.get(col, "default"),
                            )
                        )

            is_head = commit.oid == self.repo.head.commit_oid
            is_on_branch = self._is_on_current_branch(commit)

            color = branch_colors.get(col, "default")
            symbol = self._get_symbol(commit, is_head, is_on_branch)

            node = GraphNode(
                oid=commit.oid,
                row=row,
                column=col,
                color=color,
                symbol=symbol,
                edges=edges,
                commit=commit,
                is_head=is_head,
                is_on_branch=is_on_branch,
            )
            nodes.append(node)

            if col not in active_columns:
                active_columns[col] = commit.oid
                while len(column_edges) <= col:
                    column_edges.append([])

        self._process_merge_edges(nodes, active_columns, branch_colors)

        return nodes

    def _compute_branch_colors(self) -> dict[int, str]:
        """Compute colors for each column without recursion."""
        colors: dict[int, str] = {}

        default_colors = [
            "cyan",
            "green",
            "magenta",
            "yellow",
            "blue",
            "bright_red",
            "bright_green",
            "bright_blue",
        ]

        for i, branch in enumerate(self.repo.branches):
            if not branch.is_remote:
                col = i % 10
                branch_name = branch.name
                if branch_name in ("main", "master"):
                    colors[col] = "cyan"
                elif branch_name.startswith("feature/"):
                    colors[col] = "green"
                elif branch_name.startswith("bugfix/"):
                    colors[col] = "magenta"
                elif branch_name.startswith("hotfix/"):
                    colors[col] = "yellow"
                else:
                    colors[col] = default_colors[col % len(default_colors)]

        return colors

    def _topological_sort(
        self,
        limit: int | None = None,
        start_oid: bytes | None = None,
    ) -> list[Commit]:
        """Topologically sort commits."""
        visited: set[bytes] = set()
        result: list[Commit] = []
        oid_stack: list[bytes] = []

        if start_oid and start_oid in self.repo.commits:
            oid_stack.append(start_oid)
        else:
            oid_stack.extend(self.repo.head.commit_oid for _ in [1] if self.repo.head.commit_oid)

        for branch in self.repo.branches:
            if branch.oid not in oid_stack:
                oid_stack.append(branch.oid)

        while oid_stack:
            oid = oid_stack.pop()
            if oid in visited:
                continue
            visited.add(oid)

            if oid in self.repo.commits:
                commit = self.repo.commits[oid]
                oid_stack.append(oid)

                for parent_oid in commit.parents:
                    if parent_oid not in visited:
                        oid_stack.append(parent_oid)

                result.append(commit)

        result.sort(key=lambda c: c.commit_time, reverse=True)

        if limit:
            result = result[:limit]

        return result

    def _assign_column(
        self,
        commit: Commit,
        active_columns: dict[int, bytes],
    ) -> int:
        """Assign column to commit."""
        if commit.oid in self.columns:
            return self.columns[commit.oid]

        children = self.children_map.get(commit.oid, [])
        parent_cols: list[int] = []

        for child_oid in children:
            if child_oid in self.columns:
                parent_cols.append(self.columns[child_oid])

        if parent_cols:
            col = min(parent_cols)
            for pc in parent_cols:
                if pc != col and pc not in parent_cols[:-1]:
                    pass
        else:
            col = self.next_column
            self.next_column += 1

        self.columns[commit.oid] = col
        return col

    def _is_on_current_branch(self, commit: Commit) -> bool:
        """Check if commit is on the current branch."""
        current = self.repo.current_branch
        if not current:
            return True

        if commit.oid == current.oid:
            return True

        reachable = self._get_reachable_from(current.oid)
        return commit.oid in reachable

    def _get_reachable_from(self, start_oid: bytes) -> set[bytes]:
        """Get all commits reachable from start OID."""
        reachable: set[bytes] = {start_oid}
        stack = [start_oid]

        while stack:
            oid = stack.pop()
            if oid in self.repo.commits:
                commit = self.repo.commits[oid]
                for parent_oid in commit.parents:
                    if parent_oid not in reachable:
                        reachable.add(parent_oid)
                        stack.append(parent_oid)

        return reachable

    def _get_symbol(
        self,
        commit: Commit,
        is_head: bool,
        is_on_branch: bool,
    ) -> str:
        """Get symbol for commit."""
        if is_head:
            return "*"
        if is_on_branch:
            return "●"
        return "○"

    def _process_merge_edges(
        self,
        nodes: list[GraphNode],
        active_columns: dict[int, bytes],
        branch_colors: dict[int, str],
    ) -> None:
        """Process edges for merge commits."""
        for i, node in enumerate(nodes):
            if not node.commit:
                continue

            for j, other in enumerate(nodes):
                if other.row == node.row + 1:
                    for edge in node.edges:
                        if edge.to_row == other.row and edge.to_col == other.column:
                            other.edges.append(
                                Edge(
                                    from_row=other.row,
                                    from_col=other.column,
                                    to_row=node.row,
                                    to_col=edge.from_col,
                                    color=branch_colors.get(edge.from_col, "default"),
                                )
                            )
