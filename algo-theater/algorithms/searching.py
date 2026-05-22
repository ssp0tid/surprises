"""Search algorithm generators.

Each yields (array, current_index, low, high, found) per step.
"""

from collections.abc import Generator

SearchStep = tuple[list[int], int, int, int, bool]


def linear_search(arr: list[int], target: int) -> Generator[SearchStep, None, None]:
    if not arr:
        yield (arr, -1, 0, 0, False)
        return
    for i in range(len(arr)):
        if arr[i] == target:
            yield (arr, i, 0, len(arr) - 1, True)
            return
        yield (arr, i, 0, len(arr) - 1, False)
    yield (arr, -1, 0, len(arr) - 1, False)


def binary_search(arr: list[int], target: int) -> Generator[SearchStep, None, None]:
    if not arr:
        yield (arr, -1, 0, 0, False)
        return
    low, high = 0, len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            yield (arr, mid, low, high, True)
            return
        yield (arr, mid, low, high, False)
        if arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    yield (arr, -1, low, high, False)
