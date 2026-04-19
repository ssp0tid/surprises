"""Procedural generation for the game world."""

import random
from typing import Optional


class WorldGenerator:
    """Procedural world generator for the game."""

    def __init__(self, seed: Optional[int] = None) -> None:
        self._rng = random.Random(seed)

    def generate_asteroid_field(
        self,
        width: float,
        height: float,
        density: float = 0.1,
    ) -> list[tuple[float, float, str]]:
        """Generate positions for asteroid field."""
        asteroids = []
        count = int(width * height * density)

        for _ in range(count):
            x = self._rng.uniform(0, width)
            y = self._rng.uniform(0, height)
            size = self._rng.choice(["large", "medium", "small"])
            asteroids.append((x, y, size))

        return asteroids

    def generate_starfield(
        self,
        width: float,
        height: float,
        count: int = 50,
    ) -> list[tuple[float, float, str]]:
        """Generate positions for starfield background."""
        stars = []
        chars = ["*", ".", "·", "•", "°"]

        for _ in range(count):
            x = self._rng.uniform(0, width)
            y = self._rng.uniform(0, height)
            char = self._rng.choice(chars)
            stars.append((x, y, char))

        return stars
