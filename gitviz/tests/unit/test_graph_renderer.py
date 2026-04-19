"""Tests for ASCII renderer."""

import pytest
from gitviz.graph.ascii_renderer import ASCIIRenderer, GRAPH_CHARS
from gitviz.graph.node import GraphNode, Edge
from gitviz.models.commit import Commit
from gitviz.models.actor import Actor


def test_graph_chars():
    """Test that all required graph characters are defined."""
    required_chars = ["pipe", "dash", "corner_down", "corner_up", "dot", "empty", "head"]
    for char in required_chars:
        assert char in GRAPH_CHARS


def test_renderer_empty():
    """Test renderer with no nodes."""
    renderer = ASCIIRenderer()
    result = renderer.render([])
    assert result == []


def test_renderer_single_node():
    """Test renderer with single node."""
    renderer = ASCIIRenderer()

    oid = b"a" * 20
    commit = Commit(
        oid=oid,
        tree_oid=b"0" * 20,
        author=Actor(name="Test", email="test@test.com"),
        author_time=1704067200,
    )

    node = GraphNode(
        oid=oid,
        row=0,
        column=0,
        color="cyan",
        symbol="●",
        commit=commit,
    )

    result = renderer.render([node])
    assert len(result) == 1


def test_column_state():
    """Test column state initialization."""
    from gitviz.graph.ascii_renderer import ColumnState

    state = ColumnState()
    assert state.char == " "
    assert state.color == "default"
    assert not state.is_continuing
