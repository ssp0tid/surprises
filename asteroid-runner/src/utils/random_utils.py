"""Random utilities with optional seeding support."""

from __future__ import annotations

import random
from typing import Any, Optional, Sequence, TypeVar

T = TypeVar("T")


class RandomManager:
    """
    Centralized random number generator with optional seeding.

    Usage:
        rng = RandomManager(seed=42)

        # Get random values
        value = rng.randint(1, 10)
        choice = rng.choice(['a', 'b', 'c'])
        shuffled = rng.shuffle([1, 2, 3, 4, 5])
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        """Initialize with optional seed."""
        self._rng = random.Random(seed)
        self._seed = seed

    @property
    def seed(self) -> Optional[int]:
        """Get the current seed."""
        return self._seed

    def seed_instance(self, seed: int) -> None:
        """Re-seed this random instance."""
        self._rng.seed(seed)
        self._seed = seed

    def random(self) -> float:
        """Get random float in [0, 1)."""
        return self._rng.random()

    def randint(self, a: int, b: int) -> int:
        """Get random integer in [a, b] (inclusive)."""
        return self._rng.randint(a, b)

    def randfloat(self, a: float, b: float) -> float:
        """Get random float in [a, b]."""
        return a + self._rng.random() * (b - a)

    def choice(self, seq: Sequence[T]) -> T:
        """Choose random element from sequence."""
        return self._rng.choice(seq)

    def choices(
        self,
        seq: Sequence[T],
        weights: Optional[Sequence[float]] = None,
        k: int = 1,
    ) -> list[T]:
        """Choose random elements with optional weights."""
        return self._rng.choices(seq, weights=weights, k=k)

    def shuffle(self, seq: Sequence[T]) -> list[T]:
        """Return a shuffled copy of the sequence."""
        result = list(seq)
        self._rng.shuffle(result)
        return result

    def sample(
        self, population: Sequence[T], k: int, *, counts: Optional[Sequence[int]] = None
    ) -> list[T]:
        """Choose k unique elements from population."""
        return self._rng.sample(population, k, counts=counts)

    def gauss(self, mu: float = 0.0, sigma: float = 1.0) -> float:
        """Get Gaussian random number."""
        return self._rng.gauss(mu, sigma)

    def triangular(
        self, low: float = 0.0, high: float = 1.0, mode: Optional[float] = None
    ) -> float:
        """Get triangular distribution random number."""
        return self._rng.triangular(low, high, mode)

    def betavariate(self, alpha: float, beta: float) -> float:
        """Get Beta distribution random number."""
        return self._rng.betavariate(alpha, beta)

    def expovariate(self, lambd: float) -> float:
        """Get exponential distribution random number."""
        return self._rng.expovariate(lambd)


# Module-level functions using system random
_system_rng = random.Random()


def seeded_random(seed: int) -> random.Random:
    """
    Create a seeded random instance.

    Useful for reproducible gameplay:
        rng = seeded_random(42)
        value = rng.random()
    """
    return random.Random(seed)


def random_choice(seq: Sequence[T]) -> T:
    """Choose random element using system random."""
    return _system_rng.choice(seq)


def random_randint(a: int, b: int) -> int:
    """Get random integer using system random."""
    return _system_rng.randint(a, b)


def random_float(a: float = 0.0, b: float = 1.0) -> float:
    """Get random float in [a, b] using system random."""
    return a + _system_rng.random() * (b - a)


def random_shuffle(seq: Sequence[T]) -> list[T]:
    """Shuffle sequence using system random."""
    result = list(seq)
    _system_rng.shuffle(result)
    return result
