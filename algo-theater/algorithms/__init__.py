from .sorting import bubble_sort, selection_sort, insertion_sort, merge_sort, quick_sort
from .searching import linear_search, binary_search
from .pathfinding import bfs, dfs, astar

SORTING_ALGORITHMS = {
    "Bubble Sort": bubble_sort,
    "Selection Sort": selection_sort,
    "Insertion Sort": insertion_sort,
    "Merge Sort": merge_sort,
    "Quick Sort": quick_sort,
}

SEARCHING_ALGORITHMS = {
    "Linear Search": linear_search,
    "Binary Search": binary_search,
}

PATHFINDING_ALGORITHMS = {
    "BFS": bfs,
    "DFS": dfs,
    "A*": astar,
}
