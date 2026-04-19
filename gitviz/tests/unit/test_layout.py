"""Tests for graph layout algorithm."""

import pytest
from gitviz.models.commit import Commit
from gitviz.models.actor import Actor
from gitviz.models.repository import Repository
from gitviz.graph.layout import GraphLayout
from pathlib import Path


def create_test_commit(oid_bytes: str, parents: list[str] | None = None) -> Commit:
    """Create a test commit."""
    oid = bytes.fromhex(oid_bytes)
    author = Actor(name="Test", email="test@test.com")
    return Commit(
        oid=oid,
        tree_oid=b"0" * 20,
        parents=[bytes.fromhex(p) for p in (parents or [])],
        author=author,
        committer=author,
        author_time=1704067200,
        commit_time=1704067200,
        message="Test commit",
    )


def test_layout_single_commit():
    """Test layout with single commit."""
    repo = Repository(path=Path("/tmp/test"))

    commit = create_test_commit("a" * 40)
    repo.commits[commit.oid] = commit
    repo.head.commit_oid = commit.oid

    layout = GraphLayout(repo)
    nodes = layout.compute_layout()

    assert len(nodes) == 1
    assert nodes[0].column == 0


def test_layout_multiple_commits():
    """Test layout with multiple commits."""
    repo = Repository(path=Path("/tmp/test"))

    commit1 = create_test_commit("b" * 40, ["a" * 40])
    commit2 = create_test_commit("a" * 40)
    repo.commits[commit1.oid] = commit1
    repo.commits[commit2.oid] = commit2
    repo.head.commit_oid = commit1.oid

    layout = GraphLayout(repo)
    nodes = layout.compute_layout()

    assert len(nodes) == 2
    assert nodes[0].column == 0
    assert nodes[1].column == 0


def test_layout_with_limit():
    """Test layout with commit limit."""
    repo = Repository(path=Path("/tmp/test"))

    for i in range(10):
        oid_hex = f"{i:02x}" * 20
        parent = f"{(i + 1) % 10:02x}" * 20 if i < 9 else None
        commit = create_test_commit(oid_hex, ["a" * 40] if parent else [])
        repo.commits[commit.oid] = commit
        if i == 9:
            repo.head.commit_oid = commit.oid

    layout = GraphLayout(repo)
    nodes = layout.compute_layout(limit=5)

    assert len(nodes) <= 10
