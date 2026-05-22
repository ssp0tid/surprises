import random


def compute_clues(line: list[int]) -> list[int]:
    """Compute consecutive-filled-cell counts for a single row/column.

    Example: [1,1,0,1,1,1,0,1] → [2, 3, 1]
    """
    clues = []
    count = 0
    for cell in line:
        if cell == 1:
            count += 1
        else:
            if count > 0:
                clues.append(count)
            count = 0
    if count > 0:
        clues.append(count)
    return clues if clues else [0]


def _is_trivial_puzzle(solution: list[list[int]]) -> bool:
    """Reject puzzles that are all-empty or all-filled (no logic required)."""
    flat = [cell for row in solution for cell in row]
    return all(c == 0 for c in flat) or all(c == 1 for c in flat)


def generate_puzzle(rows: int, cols: int, density: float, max_attempts: int = 20) -> dict:
    """Create a random nonogram puzzle.

    Args:
        rows: Number of rows in the grid.
        cols: Number of columns in the grid.
        density: Fill ratio (0.0–1.0). Higher = more filled cells.
        max_attempts: Maximum regeneration attempts to avoid trivial puzzles.

    Returns:
        Dict with keys: solution, row_clues, col_clues.

    Raises:
        ValueError: If rows, cols, or density are out of valid range.
    """
    if rows <= 0 or cols <= 0:
        raise ValueError("rows and cols must be positive integers")
    if not (0.0 < density < 1.0):
        raise ValueError("density must be between 0.0 and 1.0 (exclusive)")

    for _ in range(max_attempts):
        solution = [
            [1 if random.random() < density else 0 for _ in range(cols)]
            for _ in range(rows)
        ]
        if not _is_trivial_puzzle(solution):
            break
    # If all attempts produced trivial puzzles (extremely unlikely), use the last one anyway.

    row_clues = [compute_clues(row) for row in solution]
    col_clues = [compute_clues([solution[r][c] for r in range(rows)]) for c in range(cols)]

    return {
        "solution": solution,
        "row_clues": row_clues,
        "col_clues": col_clues,
    }


def validate_solution(
    grid: list[list[int]], row_clues: list[list[int]], col_clues: list[list[int]]
) -> bool:
    """Check if player's grid matches the clues.

    The player grid uses: 0=empty, 1=filled, 2=marked-X (treated as empty).
    Multiple valid solutions may exist — we validate against clues, not the original solution.
    """
    rows = len(grid)
    if rows == 0:
        return False
    cols = len(grid[0])

    if rows != len(row_clues) or cols != len(col_clues):
        return False

    if any(len(row) != cols for row in grid):
        return False

    binary_grid = [[1 if cell == 1 else 0 for cell in row] for row in grid]

    for i, row in enumerate(binary_grid):
        if compute_clues(row) != row_clues[i]:
            return False

    for c in range(cols):
        col = [binary_grid[r][c] for r in range(rows)]
        if compute_clues(col) != col_clues[c]:
            return False

    return True
