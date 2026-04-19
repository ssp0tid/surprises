"""Collision detection system with spatial partitioning."""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterator
from collections import defaultdict

if TYPE_CHECKING:
    from ..entities.base import Entity, DamageComponent
    from ..state import GameContext


class CollisionGrid:
    """Spatial partitioning grid for efficient collision detection."""

    def __init__(self, cell_size: int = 10) -> None:
        self._cell_size = cell_size
        self._grid: dict[tuple[int, int], set[Entity]] = defaultdict(set)

    def clear(self) -> None:
        """Clear all entities from grid."""
        self._grid.clear()

    def _get_cell(self, x: float, y: float) -> tuple[int, int]:
        """Get cell coordinates for a position."""
        return (int(x) // self._cell_size, int(y) // self._cell_size)

    def insert(self, entity: Entity) -> None:
        """Insert an entity into the grid."""
        if not entity.collision or not entity.active:
            return

        pos = entity.position
        cell = self._get_cell(pos.x, pos.y)
        self._grid[cell].add(entity)

        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                adj_cell = (cell[0] + dx, cell[1] + dy)
                self._grid[adj_cell].add(entity)

    def get_nearby(self, entity: Entity) -> Iterator[Entity]:
        """Get all entities in nearby cells."""
        if not entity.collision:
            return

        pos = entity.position
        cell = self._get_cell(pos.x, pos.y)

        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                adj_cell = (cell[0] + dx, cell[1] + dy)
                yield from self._grid.get(adj_cell, set())


class CollisionSystem:
    """Handles collision detection between entities."""

    COLLISION_RULES: dict[str, set[str]] = {
        "player": {"enemy", "asteroid", "enemy_bullet", "powerup"},
        "enemy": {"player", "bullet"},
        "bullet": {"enemy", "asteroid"},
        "asteroid": {"player", "bullet"},
        "powerup": {"player"},
    }

    def __init__(self) -> None:
        self._grid = CollisionGrid(cell_size=10)
        self._collision_pairs: list[tuple[Entity, Entity, str]] = []
        self._debug_mode = False

    def detect_collisions(self, context: GameContext) -> list[tuple[Entity, Entity]]:
        """Detect all collisions in the current frame."""
        self._collision_pairs.clear()
        self._grid.clear()

        for entity in context.entities.values():
            if entity.active:
                self._grid.insert(entity)

        if context.player and context.player.active:
            self._grid.insert(context.player)

        checked_pairs: set[tuple[str, str]] = set()

        all_entities = list(context.entities.values())
        if context.player and context.player.active:
            all_entities.append(context.player)

        for entity in all_entities:
            if not entity or not entity.active:
                continue

            for other in self._grid.get_nearby(entity):
                if other.id == entity.id or not other.active:
                    continue

                pair_key = tuple(sorted([str(entity.id), str(other.id)]))
                if pair_key in checked_pairs:
                    continue
                checked_pairs.add(pair_key)

                if not self._can_collide(entity, other):
                    continue

                if self._check_collision(entity, other):
                    self._collision_pairs.append((entity, other, "collision"))

        return [(a, b) for a, b, _ in self._collision_pairs]

    def _can_collide(self, entity_a: Entity, entity_b: Entity) -> bool:
        """Check if two entities are allowed to collide based on tags."""
        for tag_a in entity_a._tags:
            for tag_b in entity_b._tags:
                if tag_a in self.COLLISION_RULES:
                    if tag_b in self.COLLISION_RULES[tag_a]:
                        return True
                if tag_b in self.COLLISION_RULES:
                    if tag_a in self.COLLISION_RULES[tag_b]:
                        return True
        return False

    def _check_collision(self, entity_a: Entity, entity_b: Entity) -> bool:
        """Check if two entities are colliding using circle collision."""
        pos_a = entity_a.position
        pos_b = entity_b.position
        col_a = entity_a.collision
        col_b = entity_b.collision

        if not col_a or not col_b:
            return False

        dx = pos_a.x - pos_b.x
        dy = pos_a.y - pos_b.y
        distance_sq = dx * dx + dy * dy

        radius_sum = col_a.radius + col_b.radius

        return distance_sq < radius_sum * radius_sum

    def resolve_collision(self, entity_a: Entity, entity_b: Entity) -> list[str]:
        """Resolve collision between two entities."""
        effects: list[str] = []

        dmg_a = entity_a.get_component(DamageComponent)
        dmg_b = entity_b.get_component(DamageComponent)

        if entity_a.health and dmg_b:
            entity_a.health.current -= dmg_b.amount
            effects.append(f"damage_{entity_a.type.name}")

            if entity_a.health.current <= 0:
                effects.append(f"destroy_{entity_a.type.name}")

        if entity_b.health and dmg_a:
            entity_b.health.current -= dmg_a.amount
            effects.append(f"damage_{entity_b.type.name}")

            if entity_b.health.current <= 0:
                effects.append(f"destroy_{entity_b.type.name}")

        score_a = entity_a.get_component(ScoreComponent)
        score_b = entity_b.get_component(ScoreComponent)

        if entity_b.health and entity_b.health.current <= 0 and score_b:
            effects.append(f"score_{score_b.points}")

        if entity_a.health and entity_a.health.current <= 0 and score_a:
            effects.append(f"score_{score_a.points}")

        return effects

    def enable_debug(self) -> None:
        """Enable collision debug mode."""
        self._debug_mode = True

    def disable_debug(self) -> None:
        """Disable collision debug mode."""
        self._debug_mode = False
