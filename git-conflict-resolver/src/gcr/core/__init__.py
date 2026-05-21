"""Core domain logic for conflict resolution."""

from .conflict import ConflictFile, ConflictHunk, ConflictSide, ResolutionChoice
from .parser import ConflictParser, ParseResult
from .diff3 import Diff3Merger, Diff3Result
from .hints import HintEngine, ConflictHint, HintType
from .resolver import Resolver, ResolutionResult

__all__ = [
    "ConflictFile",
    "ConflictHunk",
    "ConflictSide",
    "ResolutionChoice",
    "ConflictParser",
    "ParseResult",
    "Diff3Merger",
    "Diff3Result",
    "HintEngine",
    "ConflictHint",
    "HintType",
    "Resolver",
    "ResolutionResult",
]
