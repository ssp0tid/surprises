"""Spatial grid for world optimization."""

from __future__ import annotations

from typing import Iterator, Optional
from collections import defaultdict


class SpatialGrid:
    """Grid-based spatial partitioning for entities."""

    def __init__(self, cell_size: float = 10.0) -> None:
        self._cell_size = cell_size
        self._cells: dict[tuple[int, int], set[int]] = defaultdict(set)
        self._entity_positions: dict[int, tuple[float, float]] = {}

    def clear(self) -> None:
        """Clear all entries from the grid."""
        self._cells.clear()
        self._entity_positions.clear()

    def _get_cell(self, x: float, y: float) -> tuple[int, int]:
        """Get cell coordinates for a position."""
        return (int(x // self._cell_size), int(y // self._cell_size))

    def insert(self, entity_id: int, x: float, y: float) -> None:
        """Insert an entity into the grid."""
        self._entity_positions[entity_id] = (x, y)
        cell = self._get_cell(x, y)
        self._cells[cell].add(entity_id)

    def remove(self, entity_id: int) -> None:
        """Remove an entity from the grid."""
        if entity_id in self._entity_positions:
            x, y = self._entity_positions.pop(entity_id)
            cell = self._get_cell(x, y)
            self._cells[cell].discard(entity_id)

    def update(self, entity_id: int, x: float, y: float) -> None:
        """Update an entity's position in the grid."""
        if entity_id in self._entity_positions:
            old_x, old_y = self._entity_positions[entity_id]
            old_cell = self._get_cell(old_x, old_y)
            self._cells[old_cell].discard(entity_id)

        self._entity_positions[entity_id] = (x, y)
        new_cell = self._get_cell(x, y)
        self._cells[new_cell].add(entity_id)

    def get_nearby(self, x: float, y: float, radius: float = 1) -> Iterator[int]:
        """Get all entity IDs within radius cells of position."""
        cell = self._get_cell(x, y)
        cells_to_check = int(radius) + 1

        for dx in range(-cells_to_check, cells_to_check + 1):
            for dy in range(-cells_to_check, cells_to_check + 1):
                check_cell = (cell[0] + dx, cell[1] + dy)
                yield from self._cells.get(check_cell, set())

    def get_in_rect(self, x1: float, y1: float, x2: float, y2: float) -> Iterator[int]:
        """Get all entity IDs within a rectangular region."""
        cell_min = self._get_cell(min(x1, x2), min(y1, y2))
        cell_max = self._get_cell(max(x1, x2), max(y1, y2))

        for cx in range(cell_min[0], cell_max[0] + 1):
            for cy in range(cell_min[1], cell_max[1] + 1):
                yield from self._cells.get((cx, cy), set())
