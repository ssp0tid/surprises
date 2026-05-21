"""Maze solving algorithms as generators for step-by-step animation."""

import heapq
from collections import deque

N, E, S, W = 1, 2, 4, 8
DX = {N: -1, E: 0, S: 1, W: 0}
DY = {N: 0, E: 1, S: 0, W: -1}


def _neighbors(maze, row, col):
    """Yield reachable neighbors from (row, col)."""
    height, width = len(maze), len(maze[0])
    for direction in (N, E, S, W):
        if not (maze[row][col] & direction):
            nr, nc = row + DX[direction], col + DY[direction]
            if 0 <= nr < height and 0 <= nc < width:
                yield nr, nc


def solve_bfs(maze, start, end):
    """BFS solver. Yields (visited_cells, current_path) at each step."""
    visited = set()
    visited.add(start)
    parent = {start: None}
    queue = deque([start])
    visited_list = [start]

    while queue:
        row, col = queue.popleft()

        if (row, col) == end:
            path = _reconstruct_path(parent, end)
            yield visited_list, path
            return

        for nr, nc in _neighbors(maze, row, col):
            if (nr, nc) not in visited:
                visited.add((nr, nc))
                parent[(nr, nc)] = (row, col)
                queue.append((nr, nc))
                visited_list.append((nr, nc))
                yield visited_list, _reconstruct_path(parent, (nr, nc))

    yield visited_list, []


def solve_dfs(maze, start, end):
    """DFS solver. Yields (visited_cells, current_path) at each step."""
    visited = set()
    visited.add(start)
    parent = {start: None}
    stack = [start]
    visited_list = [start]

    while stack:
        row, col = stack.pop()

        if (row, col) == end:
            path = _reconstruct_path(parent, end)
            yield visited_list, path
            return

        for nr, nc in _neighbors(maze, row, col):
            if (nr, nc) not in visited:
                visited.add((nr, nc))
                parent[(nr, nc)] = (row, col)
                stack.append((nr, nc))
                visited_list.append((nr, nc))
                yield visited_list, _reconstruct_path(parent, (nr, nc))

    yield visited_list, []


def solve_astar(maze, start, end):
    """A* solver with Manhattan distance heuristic. Yields (visited_cells, current_path) at each step."""
    def heuristic(cell):
        return abs(cell[0] - end[0]) + abs(cell[1] - end[1])

    visited = set()
    parent = {start: None}
    g_score = {start: 0}
    counter = 0
    open_set = [(heuristic(start), counter, start)]
    visited_list = []

    while open_set:
        _, _, current = heapq.heappop(open_set)

        if current in visited:
            continue

        visited.add(current)
        visited_list.append(current)

        if current == end:
            path = _reconstruct_path(parent, end)
            yield visited_list, path
            return

        yield visited_list, _reconstruct_path(parent, current)

        row, col = current
        for nr, nc in _neighbors(maze, row, col):
            if (nr, nc) in visited:
                continue
            tentative_g = g_score[current] + 1
            if tentative_g < g_score.get((nr, nc), float("inf")):
                g_score[(nr, nc)] = tentative_g
                parent[(nr, nc)] = current
                counter += 1
                heapq.heappush(open_set, (tentative_g + heuristic((nr, nc)), counter, (nr, nc)))

    yield visited_list, []


def _reconstruct_path(parent, end):
    path = []
    current = end
    while current is not None:
        path.append(current)
        current = parent[current]
    path.reverse()
    return path


SOLVERS = {
    "bfs": solve_bfs,
    "dfs": solve_dfs,
    "astar": solve_astar,
}
