"""Data models for repository analysis."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Contributor:
    name: str
    email: str
    commit_count: int = 0
    first_commit: Optional[datetime] = None
    last_commit: Optional[datetime] = None
    insertions: int = 0
    deletions: int = 0


@dataclass
class CommitInfo:
    sha: str
    short_sha: str
    author: Contributor
    committer: Contributor
    message: str
    message_first_line: str
    date: datetime
    changed_files: int = 0
    insertions: int = 0
    deletions: int = 0
    branches: List[str] = field(default_factory=list)


@dataclass
class Repository:
    path: str
    name: str
    is_valid: bool
    branch_count: int = 0
    total_commits: int = 0
    contributors: List[Contributor] = field(default_factory=list)
    first_commit_date: Optional[datetime] = None
    last_commit_date: Optional[datetime] = None
    error: Optional[str] = None


@dataclass
class ActivityHour:
    hour: int
    day: int
    commit_count: int


@dataclass
class BranchInfo:
    name: str
    is_remote: bool
    is_current: bool
    last_commit_sha: str
    last_commit_date: Optional[datetime]
    commit_count: int = 0


@dataclass
class FileChange:
    path: str
    change_count: int = 0
    insertions: int = 0
    deletions: int = 0
    last_changed: Optional[datetime] = None


@dataclass
class MessageAnalysis:
    category: str
    count: int
    percentage: float
    examples: List[str] = field(default_factory=list)
