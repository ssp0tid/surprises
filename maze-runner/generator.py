"""Maze generation algorithms.

Maze representation: 2D grid where each cell is a bitmask:
- bit 0 (1): wall north
- bit 1 (2): wall east
- bit 2 (4): wall south
- bit 3 (8): wall west

All walls present = 15 (0b1111).
"""

import random

# Direction constants
N, E, S, W = 1, 2, 4, 8

# Opposite walls
OPPOSITE = {N: S, E: W, S: N, W: E}

# Direction deltas: (row_delta, col_delta)
DX = {N: -1, E: 0, S: 1, W: 0}
DY = {N: 0, E: 1, S: 0, W: -1}


def generate_recursive_backtracker(width: int, height: int, seed: int | None = None) -> list[list[int]]:
    """DFS-based maze generation. Produces long winding corridors."""
    rng = random.Random(seed)
    maze = [[N | E | S | W] * width for _ in range(height)]

    visited = [[False] * width for _ in range(height)]
    stack = [(0, 0)]
    visited[0][0] = True

    while stack:
        row, col = stack[-1]
        neighbors = []
        for direction in (N, E, S, W):
            nr, nc = row + DX[direction], col + DY[direction]
            if 0 <= nr < height and 0 <= nc < width and not visited[nr][nc]:
                neighbors.append((nr, nc, direction))

        if neighbors:
            nr, nc, direction = rng.choice(neighbors)
            maze[row][col] &= ~direction
            maze[nr][nc] &= ~OPPOSITE[direction]
            visited[nr][nc] = True
            stack.append((nr, nc))
        else:
            stack.pop()

    return maze


def generate_kruskals(width: int, height: int, seed: int | None = None) -> list[list[int]]:
    """Kruskal's algorithm. Produces more branching paths."""
    rng = random.Random(seed)
    maze = [[N | E | S | W] * width for _ in range(height)]

    # Union-Find
    parent = {}
    rank = {}

    def find(cell):
        while parent[cell] != cell:
            parent[cell] = parent[parent[cell]]
            cell = parent[cell]
        return cell

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra == rb:
            return False
        if rank[ra] < rank[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        if rank[ra] == rank[rb]:
            rank[ra] += 1
        return True

    # Initialize sets
    for r in range(height):
        for c in range(width):
            parent[(r, c)] = (r, c)
            rank[(r, c)] = 0

    # Collect all edges
    edges = []
    for r in range(height):
        for c in range(width):
            if c + 1 < width:
                edges.append((r, c, E))
            if r + 1 < height:
                edges.append((r, c, S))

    rng.shuffle(edges)

    for r, c, direction in edges:
        nr, nc = r + DX[direction], c + DY[direction]
        if union((r, c), (nr, nc)):
            maze[r][c] &= ~direction
            maze[nr][nc] &= ~OPPOSITE[direction]

    return maze


def generate_prims(width: int, height: int, seed: int | None = None) -> list[list[int]]:
    """Prim's algorithm. Produces organic-looking mazes."""
    rng = random.Random(seed)
    maze = [[N | E | S | W] * width for _ in range(height)]

    in_maze = [[False] * width for _ in range(height)]
    frontier = []

    # Start from random cell
    start_r, start_c = rng.randint(0, height - 1), rng.randint(0, width - 1)
    in_maze[start_r][start_c] = True

    # Add neighbors to frontier
    for direction in (N, E, S, W):
        nr, nc = start_r + DX[direction], start_c + DY[direction]
        if 0 <= nr < height and 0 <= nc < width:
            frontier.append((nr, nc, start_r, start_c, OPPOSITE[direction]))

    while frontier:
        idx = rng.randint(0, len(frontier) - 1)
        # Swap with last for O(1) removal
        frontier[idx], frontier[-1] = frontier[-1], frontier[idx]
        nr, nc, fr, fc, from_dir = frontier.pop()

        if in_maze[nr][nc]:
            continue

        in_maze[nr][nc] = True
        # Carve passage
        maze[nr][nc] &= ~from_dir
        maze[fr][fc] &= ~OPPOSITE[from_dir]

        # Add new frontier cells
        for direction in (N, E, S, W):
            nnr, nnc = nr + DX[direction], nc + DY[direction]
            if 0 <= nnr < height and 0 <= nnc < width and not in_maze[nnr][nnc]:
                frontier.append((nnr, nnc, nr, nc, OPPOSITE[direction]))

    return maze


ALGORITHMS = {
    "recursive": generate_recursive_backtracker,
    "kruskals": generate_kruskals,
    "prims": generate_prims,
}
