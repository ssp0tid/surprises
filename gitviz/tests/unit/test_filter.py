"""Tests for filter engine."""

import pytest
from gitviz.models.commit import Commit
from gitviz.models.actor import Actor
from gitviz.search.filter_engine import FilterEngine


def create_test_commit(
    oid_hex: str,
    author_name: str = "Test Author",
    message: str = "Test commit message",
    author_time: int = 1704067200,
) -> Commit:
    """Create a test commit."""
    return Commit(
        oid=bytes.fromhex(oid_hex),
        tree_oid=b"0" * 20,
        author=Actor(name=author_name, email=f"{author_name.lower()}@test.com"),
        author_time=author_time,
        commit_time=author_time,
        message=message,
    )


def test_filter_compile_empty():
    """Test compiling empty filter."""
    filter = FilterEngine.compile("")
    assert filter.predicates == []


def test_filter_author():
    """Test author filter."""
    filter = FilterEngine.compile("author:John")

    commit = create_test_commit("a" * 40, author_name="John Doe")
    assert list(FilterEngine.filter_commits([commit], filter)) == [commit]

    commit2 = create_test_commit("b" * 40, author_name="Jane Smith")
    assert list(FilterEngine.filter_commits([commit2], filter)) == []


def test_filter_message():
    """Test message filter."""
    filter = FilterEngine.compile("message:fix")

    commit = create_test_commit("a" * 40, message="fix: bug in login")
    assert list(FilterEngine.filter_commits([commit], filter)) == [commit]

    commit2 = create_test_commit("b" * 40, message="feat: new feature")
    assert list(FilterEngine.filter_commits([commit2], filter)) == []


def test_filter_hash():
    """Test hash filter."""
    filter = FilterEngine.compile("hash:abc123")

    commit = create_test_commit("abc1234567890" * 2)
    assert list(FilterEngine.filter_commits([commit], filter)) == [commit]


def test_fuzzy_match():
    """Test fuzzy matching."""
    from gitviz.search.matcher import fuzzy_match

    assert fuzzy_match("Hello World", "hello")
    assert fuzzy_match("Hello World", "world")
    assert fuzzy_match("Hello World", "lo wo")
    assert not fuzzy_match("Hello World", "xyz")
