"""Game configuration constants."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GameConfig:
    """Immutable game configuration constants."""

    DEFAULT_WIDTH: int = 80
    DEFAULT_HEIGHT: int = 40
    MIN_WIDTH: int = 60
    MIN_HEIGHT: int = 24

    TARGET_FPS: int = 60
    FIXED_DT: float = 1.0 / 60.0
    MAX_FRAME_SKIP: int = 5

    PLAYER_SPEED: float = 300.0
    PLAYER_MAX_HEALTH: int = 100
    PLAYER_SHOOT_COOLDOWN: float = 0.15
    PLAYER_BULLET_SPEED: float = 600.0

    ENEMY_BASE_SPEED: float = 100.0
    ENEMY_SPAWN_INTERVAL: float = 4.0
    ENEMY_BULLET_SPEED: float = 300.0

    ASTEROID_SPAWN_INTERVAL: float = 2.0
    ASTEROID_BASE_SPEED: float = 80.0
    ASTEROID_SPEED_VARIANCE: float = 40.0

    SCORE_ASTEROID_SMALL: int = 10
    SCORE_ASTEROID_MEDIUM: int = 25
    SCORE_ASTEROID_LARGE: int = 50
    SCORE_ENEMY_BASIC: int = 20
    SCORE_ENEMY_ADVANCED: int = 50
    SCORE_BOSS: int = 500

    DIFFICULTY_SCALE_PER_LEVEL: float = 0.15
    LEVEL_SCORE_THRESHOLDS: tuple[int, ...] = (
        0,
        500,
        1500,
        3000,
        5000,
        8000,
        12000,
        17000,
        23000,
        30000,
    )

    HIGH_SCORES_FILE: str = "assets/high_scores.json"
    MAX_HIGH_SCORES: int = 10

    COMBO_TIMEOUT: float = 3.0
    COMBO_INCREMENT: float = 0.1
    MAX_COMBO: float = 2.0

    BOSS_LEVEL_INTERVAL: int = 5

    PLAYER_COLLISION_RADIUS: float = 2.0
    ASTEROID_LARGE_RADIUS: float = 5.0
    ASTEROID_MEDIUM_RADIUS: float = 3.0
    ASTEROID_SMALL_RADIUS: float = 1.5
    ENEMY_BASIC_RADIUS: float = 1.5
    ENEMY_ADVANCED_RADIUS: float = 2.0
    ENEMY_BOSS_RADIUS: float = 5.0
    BULLET_RADIUS: float = 0.5


CONFIG = GameConfig()


def get_asset_path(filename: str) -> Path:
    """Get the full path to an asset file."""
    return Path(__file__).parent.parent.parent / "assets" / filename
