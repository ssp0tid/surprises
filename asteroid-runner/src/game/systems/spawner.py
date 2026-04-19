"""Entity spawning system."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from ..state import GameContext
    from ..entities.base import Entity


class SpawnConfig:
    """Configuration for entity spawning."""

    def __init__(
        self,
        min_distance_from_player: float = 20.0,
        spawn_margin: float = 5.0,
        max_attempts: int = 10,
    ) -> None:
        self.min_distance_from_player = min_distance_from_player
        self.spawn_margin = spawn_margin
        self.max_attempts = max_attempts


class SpawnerSystem:
    """Handles entity spawning with procedural generation."""

    def __init__(
        self,
        config: SpawnConfig,
        world_width: int,
        world_height: int,
    ) -> None:
        self._config = config
        self._world_width = world_width
        self._world_height = world_height

        self._asteroid_timer: float = 0.0
        self._enemy_timer: float = 0.0

        self._factories: dict[str, Callable[..., Entity]] = {}

    def register_factory(self, name: str, factory: Callable[..., Entity]) -> None:
        """Register an entity factory."""
        self._factories[name] = factory

    def update(self, context: GameContext, dt: float) -> None:
        """Update spawn timers and spawn entities."""
        difficulty = context.session.difficulty

        self._asteroid_timer += dt
        self._enemy_timer += dt

        asteroid_interval = 2.0 / difficulty
        if self._asteroid_timer >= asteroid_interval:
            self._spawn_asteroid(context)
            self._asteroid_timer = 0.0

        enemy_interval = 4.0 / difficulty
        if self._enemy_timer >= enemy_interval:
            self._spawn_enemy(context)
            self._enemy_timer = 0.0

        if context.session.level % 5 == 0 and context.session.level > 0:
            if not self._has_boss(context):
                self._spawn_boss(context)

    def _spawn_asteroid(self, context: GameContext) -> None:
        """Spawn an asteroid at a random position."""
        sizes = ["large", "medium", "small"]
        weights = [0.2, 0.4, 0.4]
        size = random.choices(sizes, weights)[0]

        x, y = self._find_spawn_position(context, margin_top=5)

        asteroid_factory = self._factories.get("asteroid")
        if asteroid_factory:
            asteroid = asteroid_factory(size=size, x=x, y=y)
            asteroid.velocity.vy = random.uniform(2.0, 4.0) * context.session.difficulty
            asteroid.velocity.vx = random.uniform(-1.0, 1.0)
            context.entities[asteroid.id] = asteroid

    def _spawn_enemy(self, context: GameContext) -> None:
        """Spawn an enemy based on current level."""
        level = context.session.level
        if level < 3:
            enemy_type = "basic"
        elif level < 7:
            enemy_type = random.choice(["basic", "advanced"])
        else:
            enemy_type = random.choice(["basic", "advanced", "advanced"])

        spawn_type = random.choice(["top", "left", "right"])
        if spawn_type == "top":
            x = random.uniform(5, self._world_width - 5)
            y = -5
        elif spawn_type == "left":
            x = -5
            y = random.uniform(5, self._world_height // 2)
        else:
            x = self._world_width + 5
            y = random.uniform(5, self._world_height // 2)

        enemy_factory = self._factories.get("enemy")
        if enemy_factory:
            enemy = enemy_factory(enemy_type=enemy_type, x=x, y=y)
            context.entities[enemy.id] = enemy

    def _spawn_boss(self, context: GameContext) -> None:
        """Spawn a boss enemy."""
        x = self._world_width // 2
        y = -10

        enemy_factory = self._factories.get("enemy")
        if enemy_factory:
            boss = enemy_factory(enemy_type="boss", x=x, y=y)
            context.entities[boss.id] = boss

    def _find_spawn_position(
        self, context: GameContext, margin_top: float = 0
    ) -> tuple[float, float]:
        """Find a valid spawn position away from player."""
        player = context.player

        for _ in range(self._config.max_attempts):
            x = random.uniform(
                self._config.spawn_margin, self._world_width - self._config.spawn_margin
            )
            y = random.uniform(margin_top, self._world_height // 3)

            if player and player.active:
                dx = x - player.position.x
                dy = y - player.position.y
                distance = (dx * dx + dy * dy) ** 0.5

                if distance >= self._config.min_distance_from_player:
                    return (x, y)

        return (
            random.uniform(5, self._world_width - 5),
            random.uniform(margin_top, self._world_height // 3),
        )

    def _has_boss(self, context: GameContext) -> bool:
        """Check if there's already a boss in the game."""
        for entity in context.entities.values():
            if entity.type.name == "ENEMY_BOSS" and entity.active:
                return True
        return False

    def reset_timers(self) -> None:
        """Reset all spawn timers."""
        self._asteroid_timer = 0.0
        self._enemy_timer = 0.0
