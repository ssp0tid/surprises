"""Core game loop and engine."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Callable, Optional
from collections import deque

logger = logging.getLogger("asteroid_runner")


@dataclass
class TimingStats:
    """Runtime statistics for performance monitoring."""

    frame_times: deque[float] = field(default_factory=lambda: deque(maxlen=60))
    update_times: deque[float] = field(default_factory=lambda: deque(maxlen=60))
    render_times: deque[float] = field(default_factory=lambda: deque(maxlen=60))
    fps: float = 60.0
    update_rate: float = 60.0
    dropped_frames: int = 0


class GameLoop:
    """Fixed timestep game loop running at 60 FPS."""

    FIXED_DT: float = 1.0 / 60.0
    MAX_FRAME_SKIP: int = 5
    TARGET_FPS: float = 60.0
    TARGET_FRAME_TIME: float = 1.0 / TARGET_FPS

    def __init__(
        self,
        update_callback: Callable[[float], None],
        render_callback: Callable[[float], None],
        input_callback: Callable[[], None],
    ) -> None:
        self._update = update_callback
        self._render = render_callback
        self._process_input = input_callback

        self._running = False
        self._paused = False
        self._accumulator: float = 0.0
        self._last_time: float = 0.0
        self._current_time: float = 0.0

        self._stats = TimingStats()
        self._interpolation_alpha: float = 0.0

    def start(self) -> None:
        """Start the game loop."""
        self._running = True
        self._paused = False
        self._last_time = self._get_time()
        logger.info("Game loop started")

    def stop(self) -> None:
        """Stop the game loop."""
        self._running = False
        logger.info("Game loop stopped")

    def pause(self) -> None:
        """Pause the game loop."""
        self._paused = True
        logger.info("Game loop paused")

    def resume(self) -> None:
        """Resume the game loop."""
        self._paused = False
        self._last_time = self._get_time()
        self._accumulator = 0.0
        logger.info("Game loop resumed")

    def _get_time(self) -> float:
        """Get current time in seconds using high-resolution timer."""
        return time.perf_counter()

    def _calculate_fps(self) -> float:
        """Calculate rolling average FPS from frame times."""
        if not self._stats.frame_times:
            return 0.0
        avg_frame_time = sum(self._stats.frame_times) / len(self._stats.frame_times)
        return 1.0 / avg_frame_time if avg_frame_time > 0 else 0.0

    def tick(self) -> bool:
        """Execute one game loop iteration."""
        if not self._running or self._paused:
            return False

        frame_start = self._get_time()

        self._current_time = self._get_time()
        frame_time = self._current_time - self._last_time
        self._last_time = self._current_time

        if frame_time > 0.25:
            frame_time = 0.25
            logger.warning("Frame time clamped to 250ms")

        self._accumulator += frame_time

        update_count = 0
        while self._accumulator >= self.FIXED_DT:
            update_start = self._get_time()

            self._process_input()
            self._update(self.FIXED_DT)

            update_end = self._get_time()
            self._stats.update_times.append(update_end - update_start)

            self._accumulator -= self.FIXED_DT
            update_count += 1

            if update_count > self.MAX_FRAME_SKIP:
                logger.warning(f"Skipping render: {update_count} updates needed")
                self._stats.dropped_frames += 1
                self._accumulator = 0.0
                break

        self._interpolation_alpha = self._accumulator / self.FIXED_DT

        render_start = self._get_time()
        self._render(self._interpolation_alpha)
        render_end = self._get_time()

        frame_end = self._get_time()
        self._stats.frame_times.append(frame_end - frame_start)
        self._stats.render_times.append(render_end - render_start)
        self._stats.fps = self._calculate_fps()

        return True

    @property
    def stats(self) -> TimingStats:
        """Get current timing statistics."""
        return self._stats

    @property
    def is_running(self) -> bool:
        """Check if game loop is running."""
        return self._running

    @property
    def is_paused(self) -> bool:
        """Check if game loop is paused."""
        return self._paused


class GameLoopDriver:
    """Drives the game loop using Textual's reactive updates."""

    def __init__(self, game_loop: GameLoop) -> None:
        self._game_loop = game_loop
        self._frame_count: int = 0

    def on_update(self) -> None:
        """Called by Textual on each animation frame."""
        self._frame_count += 1
        self._game_loop.tick()


class GameEngine:
    """Main game engine coordinating all game systems."""

    def __init__(self, context: "GameContext") -> None:  # type: ignore[name-defined]
        from .config import CONFIG
        from .entities.base import EntityFactory
        from .systems import (
            CollisionSystem,
            MovementSystem,
            SpawnerSystem,
            SpawnConfig,
            DifficultySystem,
            ScoringSystem,
        )
        from .state import GameState

        self._context = context
        self._config = CONFIG

        self._collision_system = CollisionSystem()
        self._movement_system = MovementSystem(
            world_width=CONFIG.DEFAULT_WIDTH,
            world_height=CONFIG.DEFAULT_HEIGHT,
        )
        self._spawner_system = SpawnerSystem(
            config=SpawnConfig(),
            world_width=CONFIG.DEFAULT_WIDTH,
            world_height=CONFIG.DEFAULT_HEIGHT,
        )
        self._difficulty_system = DifficultySystem()
        self._scoring_system = ScoringSystem(self._difficulty_system)

        self._spawner_system.register_factory("asteroid", EntityFactory.create_asteroid)
        self._spawner_system.register_factory("enemy", EntityFactory.create_enemy)

        self._game_loop: GameLoop | None = None
        self._running = False
        self._paused = False

    @property
    def context(self):
        """Get the game context."""
        return self._context

    @property
    def is_running(self) -> bool:
        """Check if game is running."""
        return self._running

    @property
    def is_paused(self) -> bool:
        """Check if game is paused."""
        return self._paused

    def start(self) -> None:
        """Start the game engine."""
        self._running = True
        self._paused = False

        player = EntityFactory.create_player()
        player.position.x = self._context.world_width // 2
        player.position.y = self._context.world_height - 5
        self._context.player = player

        self._spawner_system.reset_timers()
        self._scoring_system = ScoringSystem(self._difficulty_system)

        self._game_loop = GameLoop(
            update_callback=self._update,
            render_callback=self._render,
            input_callback=self._process_input,
        )
        self._game_loop.start()

    def stop(self) -> None:
        """Stop the game engine."""
        self._running = False
        if self._game_loop:
            self._game_loop.stop()

    def pause(self) -> None:
        """Pause the game."""
        self._paused = True
        if self._game_loop:
            self._game_loop.pause()

    def resume(self) -> None:
        """Resume the game."""
        self._paused = False
        if self._game_loop:
            self._game_loop.resume()

    def reset(self) -> None:
        """Reset the engine for a new game."""
        self._context.reset_session()
        if self._game_loop:
            self._game_loop.stop()
        self._game_loop = None
        self._running = False
        self._paused = False

    def tick(self) -> bool:
        """Execute one frame. Returns True if game should continue."""
        if self._game_loop and self._running and not self._paused:
            return self._game_loop.tick()
        return False

    def _process_input(self) -> None:
        """Process input - placeholder for input integration."""
        pass

    def _update(self, dt: float) -> None:
        """Update game state."""
        self._spawner_system.update(self._context, dt)
        self._movement_system.update(self._context, dt)

        collisions = self._collision_system.detect_collisions(self._context)
        self._handle_collisions(collisions)

        self._cleanup_dead_entities()

        self._context.session.play_time += dt

    def _handle_collisions(self, collisions: list) -> None:
        """Process collision results."""
        for entity_a, entity_b in collisions:
            effects = self._collision_system.resolve_collision(entity_a, entity_b)

            for effect in effects:
                if effect.startswith("score_"):
                    points = int(effect.split("_")[1])
                    final_points = self._scoring_system.add_kill(points)
                    self._context.add_score(final_points)
                    self._context.session.enemies_killed += 1
                elif effect.startswith("destroy_"):
                    entity_a.active = False
                    entity_b.active = False

    def _cleanup_dead_entities(self) -> None:
        """Remove dead entities."""
        self._context.entities = {
            eid: entity for eid, entity in self._context.entities.items() if entity.active
        }

    def _render(self, alpha: float) -> None:
        """Render - placeholder for rendering integration."""
        pass
