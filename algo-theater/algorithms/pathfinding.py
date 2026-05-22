"""Pathfinding algorithm generators.

Each yields (grid, visited_set, frontier_set, current_path) per step.
Grid encoding: 0=open, 1=wall.
"""

from collections import deque
from collections.abc import Generator
from dataclasses import dataclass, field
import heapq


@dataclass
class PathState:
    grid: list[list[int]]
    visited: set[tuple[int, int]]
    frontier: set[tuple[int, int]]
    path: list[tuple[int, int]]


def _neighbors(pos: tuple[int, int], rows: int, cols: int) -> list[tuple[int, int]]:
    r, c = pos
    result = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            result.append((nr, nc))
    return result


def _reconstruct_path(came_from: dict, current: tuple[int, int]) -> list[tuple[int, int]]:
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def bfs(grid: list[list[int]], start: tuple[int, int], end: tuple[int, int]) -> Generator[PathState, None, None]:
    if not grid or not grid[0]:
        yield PathState(grid, set(), set(), [])
        return
    rows, cols = len(grid), len(grid[0])
    visited: set[tuple[int, int]] = set()
    frontier: set[tuple[int, int]] = {start}
    queue: deque[tuple[int, int]] = deque([start])
    came_from: dict[tuple[int, int], tuple[int, int]] = {}

    while queue:
        current = queue.popleft()
        if current in visited:
            continue
        visited.add(current)
        frontier.discard(current)

        if current == end:
            path = _reconstruct_path(came_from, current)
            yield PathState(grid, visited, set(), path)
            return

        for neighbor in _neighbors(current, rows, cols):
            if neighbor not in visited and grid[neighbor[0]][neighbor[1]] == 0:
                if neighbor not in frontier:
                    frontier.add(neighbor)
                    queue.append(neighbor)
                    came_from[neighbor] = current

        yield PathState(grid, visited.copy(), frontier.copy(), _reconstruct_path(came_from, current))

    yield PathState(grid, visited, set(), [])


def dfs(grid: list[list[int]], start: tuple[int, int], end: tuple[int, int]) -> Generator[PathState, None, None]:
    if not grid or not grid[0]:
        yield PathState(grid, set(), set(), [])
        return
    rows, cols = len(grid), len(grid[0])
    visited: set[tuple[int, int]] = set()
    frontier: set[tuple[int, int]] = {start}
    stack = [start]
    came_from: dict[tuple[int, int], tuple[int, int]] = {}

    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        frontier.discard(current)

        if current == end:
            path = _reconstruct_path(came_from, current)
            yield PathState(grid, visited, set(), path)
            return

        for neighbor in _neighbors(current, rows, cols):
            if neighbor not in visited and grid[neighbor[0]][neighbor[1]] == 0:
                if neighbor not in frontier:
                    frontier.add(neighbor)
                    stack.append(neighbor)
                    came_from[neighbor] = current

        yield PathState(grid, visited.copy(), frontier.copy(), _reconstruct_path(came_from, current))

    yield PathState(grid, visited, set(), [])


def _manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


@dataclass(order=True)
class _PriorityItem:
    priority: float
    pos: tuple[int, int] = field(compare=False)


def astar(grid: list[list[int]], start: tuple[int, int], end: tuple[int, int]) -> Generator[PathState, None, None]:
    if not grid or not grid[0]:
        yield PathState(grid, set(), set(), [])
        return
    rows, cols = len(grid), len(grid[0])
    visited: set[tuple[int, int]] = set()
    frontier: set[tuple[int, int]] = {start}
    heap: list[_PriorityItem] = [_PriorityItem(0, start)]
    came_from: dict[tuple[int, int], tuple[int, int]] = {}
    g_score: dict[tuple[int, int], float] = {start: 0}

    while heap:
        item = heapq.heappop(heap)
        current = item.pos

        if current in visited:
            continue
        visited.add(current)
        frontier.discard(current)

        if current == end:
            path = _reconstruct_path(came_from, current)
            yield PathState(grid, visited, set(), path)
            return

        for neighbor in _neighbors(current, rows, cols):
            if neighbor in visited or grid[neighbor[0]][neighbor[1]] == 1:
                continue
            tentative_g = g_score[current] + 1
            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score = tentative_g + _manhattan(neighbor, end)
                heapq.heappush(heap, _PriorityItem(f_score, neighbor))
                frontier.add(neighbor)

        yield PathState(grid, visited.copy(), frontier.copy(), _reconstruct_path(came_from, current))

    yield PathState(grid, visited, set(), [])
