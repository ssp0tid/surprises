"""Automated conflict resolution hints engine."""

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from .conflict import ConflictHunk


class HintType(Enum):
    """Types of automated hints."""

    SAME_AS_BASE = auto()
    SAME_AS_THEIRS = auto()
    IDENTICAL = auto()
    SIMPLE_REORDER = auto()
    SYNTAX_CHANGE = auto()
    SEMANTIC_CHANGE = auto()


@dataclass
class ConflictHint:
    """Automated hint for resolving a conflict."""

    hint_type: HintType
    confidence: float
    suggested_choice: Optional[str]
    explanation: str


class HintEngine:
    """Analyzes conflicts and provides resolution hints."""

    MINOR_PATTERNS = {
        "whitespace": r"^\s*$",
        "comment": r"^\s*#",
        "docstring": r'^\s*"""',
    }

    def analyze(self, hunk: ConflictHunk) -> ConflictHint:
        """Analyze a conflict hunk and provide a resolution hint."""
        ours = hunk.ours_content
        theirs = hunk.theirs_content
        base = hunk.base_content

        if self._lines_match(ours, theirs):
            return ConflictHint(
                hint_type=HintType.IDENTICAL,
                confidence=1.0,
                suggested_choice="auto",
                explanation="Both sides are identical - auto-resolving",
            )

        if base and self._lines_match(ours, base):
            return ConflictHint(
                hint_type=HintType.SAME_AS_BASE,
                confidence=0.95,
                suggested_choice="theirs",
                explanation="OURS matches BASE - THEIRS has changes",
            )

        if base and self._lines_match(theirs, base):
            return ConflictHint(
                hint_type=HintType.SAME_AS_THEIRS,
                confidence=0.95,
                suggested_choice="ours",
                explanation="THEIRS matches BASE - OURS has changes",
            )

        minor_score = self._check_minor_changes(ours, theirs)
        if minor_score > 0.8:
            return ConflictHint(
                hint_type=HintType.SYNTAX_CHANGE,
                confidence=minor_score,
                suggested_choice="ours+theirs",
                explanation=f"Minor changes detected ({minor_score:.0%}) - recommend manual merge",
            )

        return ConflictHint(
            hint_type=HintType.SEMANTIC_CHANGE,
            confidence=0.0,
            suggested_choice=None,
            explanation="No automated resolution possible",
        )

    def _lines_match(self, a: tuple[str, ...], b: tuple[str, ...]) -> bool:
        """Check if two line sets match."""
        if len(a) != len(b):
            return False
        return all(ai.strip() == bi.strip() for ai, bi in zip(a, b))

    def _check_minor_changes(self, ours: tuple[str, ...], theirs: tuple[str, ...]) -> float:
        """Score how 'minor' the changes are."""
        content_lines = lambda lines: [
            l for l in lines if l.strip() and not re.match(r"^\s*(#|\"\"\")", l)
        ]

        ours_content = content_lines(ours)
        theirs_content = content_lines(theirs)

        if not ours_content or not theirs_content:
            return 0.0

        ours_struct = [re.sub(r"[0-9]+", "N", l) for l in ours_content]
        theirs_struct = [re.sub(r"[0-9]+", "N", l) for l in theirs_content]

        if ours_struct == theirs_struct:
            return 0.9

        return 0.0
