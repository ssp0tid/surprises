"""Filter engine for commit filtering."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Iterator

from ..models.commit import Commit
from ..models.errors import InvalidFilter


@dataclass
class Filter:
    """Compiled filter for commits."""

    predicates: list[Callable[[Commit], bool]]
    negate: bool = False


class FilterEngine:
    """Compiles and evaluates commit filters."""

    FILTER_PATTERNS = {
        r"author:(\S+)": "author",
        r"author-email:(\S+)": "author_email",
        r"date:(\d{4}-\d{2}(?:-\d{2})?)": "date",
        r"date:>(\d{4}-\d{2}-\d{2})": "date_after",
        r"date:<(\d{4}-\d{2}-\d{2})": "date_before",
        r"branch:(\S+)": "branch",
        r"message:(\S+)": "message",
        r"hash:(\S+)": "hash",
    }

    @classmethod
    def compile(cls, expression: str) -> Filter:
        """Parse filter expression into executable filter."""
        if not expression.strip():
            return Filter(predicates=[])

        predicates: list[Callable[[Commit], bool]] = []
        negate = False

        tokens = expression.split()
        for token in tokens:
            if token == "--not":
                negate = True
                continue

            matched = False
            for pattern, filter_type in cls.FILTER_PATTERNS.items():
                match = re.match(pattern, token)
                if match:
                    value = match.group(1)
                    predicate = cls._create_predicate(filter_type, value)
                    if negate:
                        original = predicate
                        predicate = lambda c, orig=original: not orig(c)
                    predicates.append(predicate)
                    matched = True
                    break

            if not matched:
                predicates.append(cls._create_predicate("message", token))

        return Filter(predicates=predicates)

    @classmethod
    def _create_predicate(cls, filter_type: str, value: str) -> Callable[[Commit], bool]:
        """Create a predicate function for the filter type."""
        if filter_type == "author":
            return lambda c: c.author and value.lower() in c.author.name.lower()

        if filter_type == "author_email":
            return lambda c: c.author and value.lower() in c.author.email.lower()

        if filter_type == "date":
            return cls._make_date_filter(value)

        if filter_type == "date_after":
            date = datetime.strptime(value, "%Y-%m-%d")
            timestamp = date.timestamp()
            return lambda c: c.author_time >= timestamp

        if filter_type == "date_before":
            date = datetime.strptime(value, "%Y-%m-%d")
            timestamp = date.timestamp()
            return lambda c: c.author_time <= timestamp

        if filter_type == "branch":
            return lambda c: value.lower() in str(c.branches).lower()

        if filter_type == "message":
            q = value.lower()
            return lambda c: q in c.message.lower()

        if filter_type == "hash":
            return lambda c: c.short_oid.startswith(value.lower())

        return lambda c: True

    @classmethod
    def _make_date_filter(cls, date_str: str) -> Callable[[Commit], bool]:
        """Create date filter from partial date string."""
        if len(date_str) == 7:
            year, month = map(int, date_str.split("-"))
            start = datetime(year, month, 1).timestamp()
            if month == 12:
                end = datetime(year + 1, 1, 1).timestamp()
            else:
                end = datetime(year, month + 1, 1).timestamp()
        elif len(date_str) == 10:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            start = date.timestamp()
            end = start + 86400
        else:
            return lambda c: True

        return lambda c: start <= c.author_time < end

    @classmethod
    def filter_commits(cls, commits: list[Commit], filter: Filter) -> Iterator[Commit]:
        """Apply filter to commit list, preserving order."""
        for commit in commits:
            if cls._matches(commit, filter):
                yield commit

    @classmethod
    def _matches(cls, commit: Commit, filter: Filter) -> bool:
        """Check if commit matches filter."""
        if not filter.predicates:
            return True

        return all(predicate(commit) for predicate in filter.predicates)


def fuzzy_match(text: str, query: str) -> bool:
    """Check if query matches text using fuzzy matching."""
    text_lower = text.lower()
    query_lower = query.lower()

    if query_lower in text_lower:
        return True

    query_idx = 0
    for char in text_lower:
        if query_idx < len(query_lower) and char == query_lower[query_idx]:
            query_idx += 1

    return query_idx == len(query_lower)
