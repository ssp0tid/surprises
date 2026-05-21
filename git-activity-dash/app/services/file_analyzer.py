"""File change analysis."""

import logging
import re
from typing import List, Dict, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)

from git import Repo
from git.exc import GitError

from app.models import FileChange, BranchInfo, MessageAnalysis
from app.utils.validators import ValidationError
from app.services.contributor_analyzer import ContributorAnalyzer as ContribAnalyzerBase


class FileAnalyzer:
    """Analyzer for file changes."""

    MESSAGE_PATTERNS = {
        "feature": r"\b(feat|feature|add|new)\b",
        "fix": r"\b(fix|bugfix|hotfix|patch)\b",
        "docs": r"\b(doc|docs|documentation)\b",
        "refactor": r"\b(refactor|cleanup|reformat)\b",
        "test": r"\b(test|spec|unittest)\b",
        "chore": r"\b(chore|maintain|build|deps)\b",
    }

    def __init__(self, repo: Repo):
        self.repo = repo

    def get_file_changes(self, limit: int = 50) -> List[FileChange]:
        """Get file change statistics.

        Args:
            limit: Maximum number of files to return

        Returns:
            List of FileChange objects sorted by change count
        """
        file_stats: Dict[str, Dict] = defaultdict(
            lambda: {
                "change_count": 0,
                "insertions": 0,
                "deletions": 0,
                "last_changed": None,
            }
        )

        try:
            for commit in self.repo.iter_commits(max_count=1000):
                for file_path, stats in commit.stats.files.items():
                    file_stats[file_path]["change_count"] += 1
                    file_stats[file_path]["insertions"] += stats.get("insertions", 0)
                    file_stats[file_path]["deletions"] += stats.get("deletions", 0)

                    commit_date = commit.committed_datetime
                    if (
                        file_stats[file_path]["last_changed"] is None
                        or commit_date > file_stats[file_path]["last_changed"]
                    ):
                        file_stats[file_path]["last_changed"] = commit_date

        except GitError as e:
            logger.warning(f"Failed to get file changes: {e}")

        changes = [
            FileChange(
                path=path,
                change_count=data["change_count"],
                insertions=data["insertions"],
                deletions=data["deletions"],
                last_changed=data["last_changed"],
            )
            for path, data in file_stats.items()
        ]

        changes.sort(key=lambda f: f.change_count, reverse=True)
        return changes[:limit]

    def get_branches(self) -> List[BranchInfo]:
        """Get branch information."""
        branches = []
        current_branch = None

        try:
            current_branch = self.repo.active_branch.name
        except TypeError:
            current_branch = "detached HEAD"

        all_branches = (
            list(self.repo.branches) + list(self.repo.remote().refs)
            if self.repo.remote()
            else []
        )

        for branch in all_branches:
            is_remote = "origin/" in branch.name or "/" in branch.name

            try:
                last_commit = branch.commit
                last_commit_date = last_commit.committed_datetime
                last_commit_sha = last_commit.hexsha[:7]
            except GitError:
                last_commit_date = None
                last_commit_sha = "unknown"

            branch_info = BranchInfo(
                name=branch.name,
                is_remote=is_remote,
                is_current=(branch.name == current_branch),
                last_commit_sha=last_commit_sha,
                last_commit_date=last_commit_date,
                commit_count=0,
            )
            branches.append(branch_info)

        branches.sort(key=lambda b: (b.is_remote, b.name))
        return branches

    def analyze_messages(self) -> List[MessageAnalysis]:
        """Analyze commit messages."""
        category_counts: Dict[str, int] = defaultdict(int)
        category_examples: Dict[str, List[str]] = defaultdict(list)
        word_freq: Dict[str, int] = defaultdict(int)

        try:
            for commit in self.repo.iter_commits(max_count=1000):
                message = commit.message
                first_line = message.split("\n")[0].lower()

                categorized = False
                for category, pattern in self.MESSAGE_PATTERNS.items():
                    if re.search(pattern, first_line):
                        category_counts[category] += 1
                        if len(category_examples[category]) < 3:
                            category_examples[category].append(first_line[:100])
                        categorized = True
                        break

                if not categorized:
                    category_counts["other"] += 1
                    if len(category_examples["other"]) < 3:
                        category_examples["other"].append(first_line[:100])

                words = re.findall(r"\b[a-z]{3,}\b", first_line)
                for word in words:
                    if word not in ContribAnalyzerBase.STOP_WORDS:
                        word_freq[word] += 1

        except GitError as e:
            logger.warning(f"Failed to analyze messages: {e}")

        total = sum(category_counts.values())
        if total == 0:
            total = 1

        analyses = []
        for category, count in sorted(
            category_counts.items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (count / total) * 100
            analyses.append(
                MessageAnalysis(
                    category=category,
                    count=count,
                    percentage=round(percentage, 1),
                    examples=category_examples[category],
                )
            )

        return analyses
