"""Commit-specific analysis."""

from typing import List, Optional, Tuple
from datetime import datetime

from git import Repo
from git.exc import GitError

from app.models import CommitInfo, Contributor
from app.utils.validators import ValidationError


class CommitAnalyzer:
    """Analyzer for commit history."""

    def __init__(self, repo: Repo):
        self.repo = repo

    def get_commits(
        self,
        page: int = 1,
        per_page: int = 50,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Tuple[List[CommitInfo], int]:
        """Get paginated commit history.

        Args:
            page: Page number (1-indexed)
            per_page: Items per page
            start_date: Filter commits after this date
            end_date: Filter commits before this date

        Returns:
            Tuple of (commits list, total count)
        """
        try:
            all_commits = list(self.repo.iter_commits())

            filtered_commits = all_commits
            if start_date or end_date:
                filtered_commits = []
                for commit in all_commits:
                    commit_date = commit.committed_datetime
                    if start_date and commit_date < start_date:
                        continue
                    if end_date and commit_date > end_date:
                        continue
                    filtered_commits.append(commit)

            total = len(filtered_commits)

            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            page_commits = filtered_commits[start_idx:end_idx]

            commits = []
            for commit in page_commits:
                commit_info = self._create_commit_info(commit)
                commits.append(commit_info)

            return commits, total

        except GitError as e:
            raise ValidationError(f"Failed to read commits: {str(e)}", "GIT_ERROR", 500)

    def _create_commit_info(self, commit) -> CommitInfo:
        """Create CommitInfo from a git commit object."""
        author = commit.author
        committer = commit.committer

        author_contrib = Contributor(
            name=author.name, email=author.email, commit_count=1
        )

        committer_contrib = Contributor(
            name=committer.name, email=committer.email, commit_count=1
        )

        message = commit.message
        first_line = message.split("\n")[0] if message else ""

        stats = commit.stats
        total_insertions = stats.total.get("insertions", 0)
        total_deletions = stats.total.get("deletions", 0)
        changed_files = len(stats.files)

        return CommitInfo(
            sha=commit.hexsha,
            short_sha=commit.hexsha[:7],
            author=author_contrib,
            committer=committer_contrib,
            message=message,
            message_first_line=first_line,
            date=commit.committed_datetime,
            changed_files=changed_files,
            insertions=total_insertions,
            deletions=total_deletions,
            branches=[],
        )

    def get_commit_count(self) -> int:
        """Get total commit count."""
        try:
            return sum(1 for _ in self.repo.iter_commits())
        except GitError:
            return 0
