"""Exception types for GCR."""

from typing import Optional


class GCRException(Exception):
    """Base exception for GCR."""

    code: str = "GCR_ERROR"

    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.details = details


class ParseError(GCRException):
    """Conflict parsing failed."""

    code = "PARSE_ERROR"


class GitError(GCRException):
    """Git operation failed."""

    code = "GIT_ERROR"


class FileError(GCRException):
    """File operation failed."""

    code = "FILE_ERROR"


class NoConflictsError(GCRException):
    """No conflicts found to resolve."""

    code = "NO_CONFLICTS"


class DirtyWorkdirError(GCRException):
    """Working directory has uncommitted changes."""

    code = "DIRTY_WORKDIR"


class ResolutionError(GCRException):
    """Conflict resolution failed."""

    code = "RESOLUTION_ERROR"


class ValidationError(GCRException):
    """Input validation failed."""

    code = "VALIDATION_ERROR"
