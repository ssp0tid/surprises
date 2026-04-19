"""HUD (Heads-Up Display) component."""

from textual.widgets import Static


class HUD(Static):
    """Heads-up display showing score, level, health, and FPS."""

    def __init__(self) -> None:
        super().__init__()
        self._score = 0
        self._level = 1
        self._health = 100
        self._max_health = 100
        self._fps = 60.0

    def update(
        self,
        score: int,
        level: int,
        health: int,
        max_health: int,
        fps: float,
    ) -> None:
        """Update HUD values."""
        self._score = score
        self._level = level
        self._health = health
        self._max_health = max_health
        self._fps = fps

    def render(self) -> str:
        """Render the HUD."""
        score_str = f"SCORE: {self._score:05d}"
        level_str = f"LEVEL: {self._level:02d}"

        health_ratio = max(0.0, min(1.0, self._health / max(1, self._max_health)))
        filled = int(health_ratio * 10)
        health_bar = "█" * filled + "░" * (10 - filled)
        health_str = f"HEALTH: {health_bar}"

        fps_str = f"FPS: {self._fps:.0f}"

        hud = f"{score_str}   {level_str}   {health_str}   {fps_str}"

        return hud
