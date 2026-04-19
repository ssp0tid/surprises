"""Tests for Commit model."""

import pytest
from datetime import datetime
from gitviz.models.commit import Commit
from gitviz.models.actor import Actor


def test_commit_short_oid():
    """Test short OID property."""
    oid = bytes.fromhex("61616161616161616161")
    commit = Commit(oid=oid)
    assert commit.short_oid == "6161616"


def test_commit_full_oid():
    """Test full OID property."""
    oid = bytes.fromhex("6161616161616161616161616161616161616161")
    commit = Commit(oid=oid)
    assert commit.full_oid == "6161616161616161616161616161616161616161"


def test_commit_is_merge():
    """Test is_merge property."""
    oid = b"a" * 20
    parent_oid = b"b" * 20

    commit_single = Commit(oid=oid, parents=[parent_oid])
    assert not commit_single.is_merge

    commit_merge = Commit(oid=oid, parents=[parent_oid, b"c" * 20])
    assert commit_merge.is_merge


def test_commit_short_message():
    """Test short_message property."""
    oid = b"a" * 20

    commit_short = Commit(oid=oid, message="Short message")
    assert commit_short.short_message == "Short message"

    long_msg = "x" * 100
    commit_long = Commit(oid=oid, message=long_msg)
    assert len(commit_long.short_message) == 75
    assert commit_long.short_message.endswith("...")


def test_commit_author_date():
    """Test author_date property."""
    oid = b"a" * 20
    timestamp = 1704067200
    commit = Commit(oid=oid, author_time=timestamp)
    assert commit.author_date == datetime.fromtimestamp(timestamp)


def test_actor_str():
    """Test Actor string representation."""
    actor = Actor(name="Test User", email="test@example.com")
    assert str(actor) == "Test User <test@example.com>"


def test_actor_matches():
    """Test Actor matches method."""
    actor = Actor(name="John Doe", email="john@example.com")

    assert actor.matches("John")
    assert actor.matches("Doe")
    assert actor.matches("john")
    assert actor.matches("@example.com")
    assert not actor.matches("unknown")
