"""Core git analysis logic."""

import os
from typing import Optional, List
from datetime import datetime

from git import Repo, GitError
from git.exc import InvalidGitRepositoryError

from app.models import Repository, Contributor
from app.utils.validators import ValidationError


class GitAnalyzer:
    """Core git repository analyzer."""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self._repo: Optional[Repo] = None

    @property
    def repo(self) -> Repo:
        """Lazy load the git repository."""
        if self._repo is None:
            try:
                self._repo = Repo(self.repo_path)
            except InvalidGitRepositoryError as e:
                raise ValidationError(
                    "Not a valid git repository", "NOT_GIT_REPO", 422, self.repo_path
                )
            except GitError as e:
                raise ValidationError(
                    f"Git error: {str(e)}", "GIT_ERROR", 500, self.repo_path
                )
        return self._repo

    def get_repository_info(self) -> Repository:
        """Get basic repository information."""
        try:
            name = os.path.basename(self.repo_path)
            branch_count = len(self.repo.heads)

            total_commits = sum(1 for _ in self.repo.iter_commits())

            contributors = self._get_contributors()

            commits_list = list(self.repo.iter_commits(max_count=1))
            first_commit_date = None
            last_commit_date = None

            if commits_list:
                last_commit_date = commits_list[0].committed_datetime

            first_commits = list(self.repo.iter_commits(max_count=1, reverse=True))
            if first_commits:
                first_commit_date = first_commits[0].committed_datetime

            return Repository(
                path=self.repo_path,
                name=name,
                is_valid=True,
                branch_count=branch_count,
                total_commits=total_commits,
                contributors=contributors,
                first_commit_date=first_commit_date,
                last_commit_date=last_commit_date,
            )
        except GitError as e:
            raise ValidationError(
                f"Failed to read repository: {str(e)}", "GIT_ERROR", 500, self.repo_path
            )

    def _get_contributors(self) -> List[Contributor]:
        """Get list of contributors."""
        contributors_dict = {}

        for commit in self.repo.iter_commits(max_count=5000):
            author = commit.author
            email = author.email.lower()

            if email not in contributors_dict:
                contributors_dict[email] = {
                    "name": author.name,
                    "email": email,
                    "count": 0,
                    "first_commit": commit.committed_datetime,
                    "last_commit": commit.committed_datetime,
                    "insertions": 0,
                    "deletions": 0,
                }

            contributors_dict[email]["count"] += 1
            if commit.committed_datetime < contributors_dict[email]["first_commit"]:
                contributors_dict[email]["first_commit"] = commit.committed_datetime
            if commit.committed_datetime > contributors_dict[email]["last_commit"]:
                contributors_dict[email]["last_commit"] = commit.committed_datetime

        contributors = [
            Contributor(
                name=data["name"],
                email=data["email"],
                commit_count=data["count"],
                first_commit=data["first_commit"],
                last_commit=data["last_commit"],
                insertions=data["insertions"],
                deletions=data["deletions"],
            )
            for data in contributors_dict.values()
        ]

        contributors.sort(key=lambda c: c.commit_count, reverse=True)
        return contributors

    def is_valid(self) -> bool:
        """Check if the path is a valid git repository."""
        try:
            return self.repo.bare is False
        except GitError:
            return False

    def get_current_branch(self) -> str:
        """Get the current branch name."""
        try:
            return self.repo.active_branch.name
        except TypeError:
            return "detached HEAD"

    def close(self):
        """Close the repository."""
        if self._repo:
            self._repo.close()
            self._repo = None
