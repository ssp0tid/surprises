"""Sorting algorithm generators.

Each yields (array_copy, highlighted_indices, comparisons, swaps) at each step.
"""

from collections.abc import Generator

SortStep = tuple[list[int], list[int], int, int]


def bubble_sort(arr: list[int]) -> Generator[SortStep, None, None]:
    comparisons = swaps = 0
    arr = arr.copy()
    n = len(arr)
    for i in range(n):
        for j in range(n - 1 - i):
            comparisons += 1
            yield (arr.copy(), [j, j + 1], comparisons, swaps)
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swaps += 1
                yield (arr.copy(), [j, j + 1], comparisons, swaps)
    yield (arr.copy(), [], comparisons, swaps)


def selection_sort(arr: list[int]) -> Generator[SortStep, None, None]:
    comparisons = swaps = 0
    arr = arr.copy()
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            comparisons += 1
            yield (arr.copy(), [min_idx, j], comparisons, swaps)
            if arr[j] < arr[min_idx]:
                min_idx = j
        if min_idx != i:
            arr[i], arr[min_idx] = arr[min_idx], arr[i]
            swaps += 1
            yield (arr.copy(), [i, min_idx], comparisons, swaps)
    yield (arr.copy(), [], comparisons, swaps)


def insertion_sort(arr: list[int]) -> Generator[SortStep, None, None]:
    comparisons = swaps = 0
    arr = arr.copy()
    n = len(arr)
    for i in range(1, n):
        j = i
        while j > 0:
            comparisons += 1
            yield (arr.copy(), [j - 1, j], comparisons, swaps)
            if arr[j - 1] > arr[j]:
                arr[j - 1], arr[j] = arr[j], arr[j - 1]
                swaps += 1
                yield (arr.copy(), [j - 1, j], comparisons, swaps)
                j -= 1
            else:
                break
    yield (arr.copy(), [], comparisons, swaps)


def merge_sort(arr: list[int]) -> Generator[SortStep, None, None]:
    comparisons = 0
    swaps = 0
    arr = arr.copy()

    def _merge_sort(arr: list[int], left: int, right: int) -> Generator[SortStep, None, None]:
        nonlocal comparisons, swaps
        if right - left <= 1:
            return
        mid = (left + right) // 2
        yield from _merge_sort(arr, left, mid)
        yield from _merge_sort(arr, mid, right)

        merged = []
        i, j = left, mid
        while i < mid and j < right:
            comparisons += 1
            yield (arr.copy(), [i, j], comparisons, swaps)
            if arr[i] <= arr[j]:
                merged.append(arr[i])
                i += 1
            else:
                merged.append(arr[j])
                j += 1
        merged.extend(arr[i:mid])
        merged.extend(arr[j:right])

        for k, val in enumerate(merged):
            if arr[left + k] != val:
                swaps += 1
            arr[left + k] = val
        yield (arr.copy(), list(range(left, right)), comparisons, swaps)

    yield from _merge_sort(arr, 0, len(arr))
    yield (arr.copy(), [], comparisons, swaps)


def quick_sort(arr: list[int]) -> Generator[SortStep, None, None]:
    comparisons = 0
    swaps = 0
    arr = arr.copy()

    def _quick_sort(arr: list[int], low: int, high: int) -> Generator[SortStep, None, None]:
        nonlocal comparisons, swaps
        if low >= high:
            return

        pivot = arr[high]
        i = low
        for j in range(low, high):
            comparisons += 1
            yield (arr.copy(), [j, high], comparisons, swaps)
            if arr[j] <= pivot:
                arr[i], arr[j] = arr[j], arr[i]
                swaps += 1
                yield (arr.copy(), [i, j], comparisons, swaps)
                i += 1
        arr[i], arr[high] = arr[high], arr[i]
        swaps += 1
        yield (arr.copy(), [i, high], comparisons, swaps)

        yield from _quick_sort(arr, low, i - 1)
        yield from _quick_sort(arr, i + 1, high)

    yield from _quick_sort(arr, 0, len(arr) - 1)
    yield (arr.copy(), [], comparisons, swaps)
