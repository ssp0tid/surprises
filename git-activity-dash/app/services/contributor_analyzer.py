"""Contributor statistics analysis."""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)
from datetime import datetime

from git import Repo
from git.exc import GitError

from app.models import Contributor, ActivityHour
from app.utils.validators import ValidationError


class ContributorAnalyzer:
    """Analyzer for contributor statistics."""

    STOP_WORDS = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "as",
        "is",
        "was",
        "are",
        "were",
        "been",
        "be",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "can",
        "this",
        "that",
        "these",
        "those",
        "i",
        "you",
        "he",
        "she",
        "it",
        "we",
        "they",
        "what",
        "which",
        "who",
        "whom",
        "whose",
        "where",
        "when",
        "why",
        "how",
        "all",
        "each",
        "every",
        "both",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "not",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "just",
        "also",
        "now",
        "here",
        "there",
        "then",
    }

    def __init__(self, repo: Repo):
        self.repo = repo

    def get_contributors(self) -> List[Contributor]:
        """Get contributor statistics."""
        try:
            contributors_dict: Dict[str, Dict] = {}

            for commit in self.repo.iter_commits(max_count=10000):
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

            contributors = []
            for data in contributors_dict.values():
                contributor = Contributor(
                    name=data["name"],
                    email=data["email"],
                    commit_count=data["count"],
                    first_commit=data["first_commit"],
                    last_commit=data["last_commit"],
                    insertions=data["insertions"],
                    deletions=data["deletions"],
                )
                contributors.append(contributor)

            contributors.sort(key=lambda c: c.commit_count, reverse=True)
            return contributors

        except GitError as e:
            raise ValidationError(
                f"Failed to analyze contributors: {str(e)}", "GIT_ERROR", 500
            )

    def get_activity_heatmap(self) -> List[ActivityHour]:
        """Get activity data for heatmap (day x hour).

        Returns:
            List of ActivityHour with day (0-6, Mon-Sun) and hour (0-23)
        """
        activity_matrix = {}

        for day in range(7):
            for hour in range(24):
                activity_matrix[(day, hour)] = 0

        try:
            for commit in self.repo.iter_commits(max_count=5000):
                commit_datetime = commit.committed_datetime
                day = commit_datetime.weekday()
                hour = commit_datetime.hour
                activity_matrix[(day, hour)] += 1

        except GitError as e:
            logger.warning(f"Failed to get activity heatmap: {e}")

        activity = []
        for (day, hour), count in activity_matrix.items():
            activity.append(ActivityHour(hour=hour, day=day, commit_count=count))

        return activity
