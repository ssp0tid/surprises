"""Shared helpers for Algo Theater."""

import random


def generate_random_array(size: int, min_val: int = 1, max_val: int = 100) -> list[int]:
    """Generate a random array of integers."""
    return [random.randint(min_val, max_val) for _ in range(size)]


def generate_sorted_array(size: int) -> list[int]:
    """Generate a sorted array (useful for search demos)."""
    arr = generate_random_array(size)
    arr.sort()
    return arr


def generate_grid(rows: int, cols: int, wall_density: float = 0.25) -> list[list[int]]:
    """Generate a grid with random walls.

    0 = open, 1 = wall.
    Start (0,0) and end (rows-1, cols-1) are always open.

    Args:
        rows: Number of rows (must be >= 2).
        cols: Number of columns (must be >= 2).
        wall_density: Probability of a cell being a wall (0.0 to 1.0).
    """
    if rows < 2 or cols < 2:
        raise ValueError(f"Grid must be at least 2x2, got {rows}x{cols}")
    wall_density = max(0.0, min(1.0, wall_density))
    grid = [
        [1 if random.random() < wall_density else 0 for _ in range(cols)]
        for _ in range(rows)
    ]
    # Ensure start and end are open
    grid[0][0] = 0
    grid[rows - 1][cols - 1] = 0
    return grid
