"""Difficulty and scoring systems."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DifficultyParams:
    """Parameters affected by difficulty scaling."""

    enemy_speed_multiplier: float = 1.0
    enemy_health_multiplier: float = 1.0
    enemy_spawn_rate_multiplier: float = 1.0
    asteroid_density_multiplier: float = 1.0
    asteroid_speed_multiplier: float = 1.0
    score_multiplier: float = 1.0
    special_enemy_chance: float = 0.0


class DifficultySystem:
    """Manages difficulty progression based on level and performance."""

    BOSS_LEVELS = {5, 10, 15, 20}
    HARDMODE_LEVEL = 15

    def __init__(self) -> None:
        self._current_params = DifficultyParams()

    def get_params_for_level(self, level: int) -> DifficultyParams:
        """Get interpolated difficulty parameters for a level."""
        base = DifficultyParams()

        level_factor = min(level, 20) / 10.0

        return DifficultyParams(
            enemy_speed_multiplier=base.enemy_speed_multiplier * (1.0 + 0.1 * level_factor),
            enemy_health_multiplier=base.enemy_health_multiplier * (1.0 + 0.15 * level_factor),
            enemy_spawn_rate_multiplier=base.enemy_spawn_rate_multiplier
            * (1.0 + 0.2 * level_factor),
            asteroid_density_multiplier=base.asteroid_density_multiplier
            * (1.0 + 0.1 * level_factor),
            asteroid_speed_multiplier=base.asteroid_speed_multiplier * (1.0 + 0.1 * level_factor),
            score_multiplier=base.score_multiplier * (1.0 + 0.05 * level_factor),
            special_enemy_chance=min(0.3, 0.05 * level_factor),
        )

    def update(self, level: int) -> DifficultyParams:
        """Update current difficulty parameters."""
        self._current_params = self.get_params_for_level(level)
        return self._current_params

    def is_boss_level(self, level: int) -> bool:
        """Check if current level should have a boss."""
        return level in self.BOSS_LEVELS

    def is_hardmode(self, level: int) -> bool:
        """Check if hardmode is active."""
        return level >= self.HARDMODE_LEVEL

    @property
    def current(self) -> DifficultyParams:
        """Get current difficulty parameters."""
        return self._current_params


class ScoringSystem:
    """Handles score calculation and tracking."""

    COMBO_TIMEOUT = 3.0
    COMBO_INCREMENT = 0.1
    MAX_COMBO = 2.0

    def __init__(self, difficulty: DifficultySystem) -> None:
        self._difficulty = difficulty
        self._combo: float = 1.0
        self._combo_timer: float = 0.0
        self._kills_since_damage: int = 0

    def add_kill(self, base_score: int) -> int:
        """Add a kill and return the calculated score with multipliers."""
        self._combo = min(self.MAX_COMBO, self._combo + self.COMBO_INCREMENT)
        self._combo_timer = self.COMBO_TIMEOUT
        self._kills_since_damage += 1

        difficulty_mult = self._difficulty.current.score_multiplier
        final_score = int(base_score * self._combo * difficulty_mult)

        return final_score

    def add_survival_points(self, seconds: float, level: int) -> int:
        """Add points for surviving."""
        return int(seconds * level * 0.5)

    def take_damage(self) -> None:
        """Reset combo when player takes damage."""
        self._combo = 1.0
        self._kills_since_damage = 0

    def update(self, dt: float) -> None:
        """Update combo timer."""
        if self._combo_timer > 0:
            self._combo_timer -= dt
            if self._combo_timer <= 0:
                self._combo = 1.0

    @property
    def combo_multiplier(self) -> float:
        """Get current combo multiplier."""
        return self._combo

    @property
    def is_no_damage_bonus_active(self) -> bool:
        """Check if no-damage bonus is active (50+ kills without damage)."""
        return self._kills_since_damage >= 50
