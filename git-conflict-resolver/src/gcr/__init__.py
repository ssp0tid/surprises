"""Git Conflict Resolver - A visual Terminal UI for resolving git merge conflicts."""

__version__ = "0.1.0"
__author__ = "GCR Contributors"

from .core.conflict import ConflictFile, ConflictHunk, ConflictSide, ResolutionChoice

__all__ = [
    "__version__",
    "ConflictFile",
    "ConflictHunk",
    "ConflictSide",
    "ResolutionChoice",
]
