"""Graph node representation."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.commit import Commit


@dataclass
class Edge:
    """A line segment in the graph."""

    from_row: int
    from_col: int
    to_row: int
    to_col: int
    color: str = "default"


@dataclass
class GraphNode:
    """Positioned commit for rendering."""

    oid: bytes
    row: int
    column: int
    color: str
    symbol: str
    edges: list[Edge] = field(default_factory=list)
    commit: "Commit | None" = None
    is_head: bool = False
    is_selected: bool = False
    is_on_branch: bool = True

    @property
    def short_oid(self) -> str:
        return self.oid.hex()[:7]

    @property
    def is_merge(self) -> bool:
        if self.commit:
            return self.commit.is_merge
        return False

    @property
    def merge_columns(self) -> list[int]:
        """Get columns of merge parents."""
        return [e.to_col for e in self.edges if e.to_col != self.column]
