"""3-way merge engine using diff3 format."""

from dataclasses import dataclass
from typing import Optional

from .conflict import ConflictHunk, ConflictSide


@dataclass
class Diff3Result:
    """Result of a 3-way merge operation."""

    merged_content: str
    has_conflicts: bool
    conflict_regions: list[tuple[int, int]]


class Diff3Merger:
    """3-way merge algorithm using diff3 format."""

    def __init__(self, conflict_marker_style: str = "merge"):
        self.conflict_marker_style = conflict_marker_style

    def merge(self, base: str, ours: str, theirs: str) -> Diff3Result:
        """Perform 3-way merge.

        Args:
            base: Common ancestor content
            ours: Current branch content
            theirs: Incoming branch content

        Returns:
            Diff3Result with merged content
        """
        base_lines = base.splitlines()
        ours_lines = ours.splitlines()
        theirs_lines = theirs.splitlines()

        ours_diff = self._compute_diff(base_lines, ours_lines)
        theirs_diff = self._compute_diff(base_lines, theirs_lines)

        merged, regions = self._merge_diffs(base_lines, ours_diff, theirs_diff)

        return Diff3Result(
            merged_content="\n".join(merged),
            has_conflicts=len(regions) > 0,
            conflict_regions=regions,
        )

    def _compute_diff(self, base: list[str], changed: list[str]) -> list[tuple[str, str]]:
        """Compute line-by-line diff between base and changed."""
        lcs = self._lcs(base, changed)

        diffs: list[tuple[str, str]] = []
        bi = ci = 0
        li = 0

        while bi < len(base) or ci < len(changed):
            if li < len(lcs) and bi < len(base) and ci < len(changed):
                if base[bi] == lcs[li] and changed[ci] == lcs[li]:
                    diffs.append(("same", base[bi]))
                    bi += 1
                    ci += 1
                    li += 1
                elif base[bi] != changed[ci]:
                    diffs.append(("remove", base[bi]))
                    bi += 1
                else:
                    diffs.append(("add", changed[ci]))
                    ci += 1
            else:
                if bi < len(base):
                    diffs.append(("remove", base[bi]))
                    bi += 1
                if ci < len(changed):
                    diffs.append(("add", changed[ci]))
                    ci += 1

        return diffs

    def _lcs(self, a: list[str], b: list[str]) -> list[str]:
        """Compute longest common subsequence."""
        m, n = len(a), len(b)
        if m == 0 or n == 0:
            return []

        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if a[i - 1] == b[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

        result: list[str] = []
        i, j = m, n
        while i > 0 and j > 0:
            if a[i - 1] == b[j - 1]:
                result.append(a[i - 1])
                i -= 1
                j -= 1
            elif dp[i - 1][j] > dp[i][j - 1]:
                i -= 1
            else:
                j -= 1

        return list(reversed(result))

    def _merge_diffs(
        self,
        base: list[str],
        ours_diff: list[tuple[str, str]],
        theirs_diff: list[tuple[str, str]],
    ) -> tuple[list[str], list[tuple[int, int]]]:
        """Merge two diffs and detect conflicts."""
        merged: list[str] = []
        regions: list[tuple[int, int]] = []

        i = 0
        while i < len(ours_diff) or i < len(theirs_diff):
            ours_op = ours_diff[i][0] if i < len(ours_diff) else None
            theirs_op = theirs_diff[i][0] if i < len(theirs_diff) else None

            if ours_op == "same" and theirs_op == "same":
                merged.append(ours_diff[i][1])
            elif ours_op == "same" and theirs_op == "add":
                merged.append(theirs_diff[i][1])
            elif ours_op == "add" and theirs_op == "same":
                merged.append(ours_diff[i][1])
            elif ours_op == "add" and theirs_op == "add":
                if ours_diff[i][1] == theirs_diff[i][1]:
                    merged.append(ours_diff[i][1])
                else:
                    start = len(merged)
                    merged.append(f"<<<<<<< HEAD")
                    merged.append(ours_diff[i][1])
                    merged.append(f"=======")
                    merged.append(theirs_diff[i][1])
                    merged.append(f">>>>>>> incoming")
                    regions.append((start, start + 6))
            else:
                if ours_op == "add":
                    merged.append(ours_diff[i][1])
                if theirs_op == "add":
                    merged.append(theirs_diff[i][1])

            i += 1

        return merged, regions
