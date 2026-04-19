"""Matcher utilities for fuzzy and exact string matching."""

import re
from difflib import SequenceMatcher


def fuzzy_match(text: str, query: str, threshold: float = 0.6) -> bool:
    """
    Check if query fuzzy-matches text.

    Args:
        text: Text to search in
        query: Query to search for
        threshold: Minimum similarity ratio (0-1)

    Returns:
        True if query matches text
    """
    text_lower = text.lower()
    query_lower = query.lower()

    if query_lower in text_lower:
        return True

    ratio = SequenceMatcher(None, query_lower, text_lower).ratio()
    return ratio >= threshold


def fuzzy_score(text: str, query: str) -> float:
    """
    Get fuzzy match score for text against query.

    Returns:
        Similarity ratio (0-1)
    """
    text_lower = text.lower()
    query_lower = query.lower()

    if query_lower in text_lower:
        return 1.0

    return SequenceMatcher(None, query_lower, text_lower).ratio()


def exact_match(text: str, query: str, case_sensitive: bool = False) -> bool:
    """Check if query exactly matches text."""
    if not case_sensitive:
        return text.lower() == query.lower()
    return text == query


def regex_match(text: str, pattern: str) -> bool:
    """Check if text matches regex pattern."""
    try:
        return bool(re.search(pattern, text, re.IGNORECASE))
    except re.error:
        return False


def match_oid(oid: str, query: str) -> bool:
    """Check if query matches OID (supports partial)."""
    oid_lower = oid.lower()
    query_lower = query.lower()

    if query_lower in oid_lower:
        return True

    if len(query) >= 4:
        return oid_lower.startswith(query_lower)

    return False
