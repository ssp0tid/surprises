"""Custom exceptions for gitviz."""


class GitVizError(Exception):
    """Base exception for all gitviz errors."""

    pass


class NotAGitRepository(GitVizError):
    """Path does not contain a .git directory."""

    pass


class ObjectNotFound(GitVizError):
    """Requested git object doesn't exist."""

    pass


class CorruptRepository(GitVizError):
    """Repository data is corrupted."""

    pass


class PackFileError(GitVizError):
    """Error parsing pack file."""

    pass


class InvalidFilter(GitVizError):
    """Filter expression is malformed."""

    pass


class DiffError(GitVizError):
    """Cannot generate diff for commit."""

    pass
