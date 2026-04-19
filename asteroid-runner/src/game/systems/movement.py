"""Movement and physics system."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..state import GameContext
    from ..entities.base import Entity, VelocityComponent


class MovementSystem:
    """Handles entity movement and physics."""

    def __init__(
        self,
        world_width: int,
        world_height: int,
        wrap_horizontal: bool = False,
        wrap_vertical: bool = True,
    ) -> None:
        self._world_width = world_width
        self._world_height = world_height
        self._wrap_horizontal = wrap_horizontal
        self._wrap_vertical = wrap_vertical

    def update(self, context: GameContext, dt: float) -> None:
        """Update positions of all entities."""
        all_entities = list(context.entities.values())
        if context.player and context.player.active:
            all_entities.append(context.player)

        for entity in all_entities:
            self._update_entity(entity, dt)

    def _update_entity(self, entity: Entity, dt: float) -> None:
        """Update a single entity's position."""
        if not entity.has_component(VelocityComponent):
            return

        vel = entity.velocity
        pos = entity.position

        new_x = pos.x + vel.vx * dt
        new_y = pos.y + vel.vy * dt

        if self._wrap_horizontal:
            new_x = new_x % self._world_width
        else:
            new_x = max(0, min(self._world_width - 1, new_x))

        if self._wrap_vertical:
            new_y = new_y % self._world_height
        else:
            new_y = max(0, min(self._world_height - 1, new_y))

        pos.x = new_x
        pos.y = new_y

    def apply_acceleration(self, entity: Entity, ax: float, ay: float, dt: float) -> None:
        """Apply acceleration to an entity."""
        if not entity.has_component(VelocityComponent):
            return
        entity.velocity.vx += ax * dt
        entity.velocity.vy += ay * dt

    def set_velocity(self, entity: Entity, vx: float, vy: float) -> None:
        """Set absolute velocity for an entity."""
        if not entity.has_component(VelocityComponent):
            return
        entity.velocity.vx = vx
        entity.velocity.vy = vy

    def stop_entity(self, entity: Entity) -> None:
        """Stop an entity completely."""
        if entity.has_component(VelocityComponent):
            entity.velocity.vx = 0
            entity.velocity.vy = 0

    def clamp_to_bounds(self, entity: Entity) -> None:
        """Clamp entity position to world bounds."""
        pos = entity.position
        pos.x = max(0, min(self._world_width - 1, pos.x))
        pos.y = max(0, min(self._world_height - 1, pos.y))
