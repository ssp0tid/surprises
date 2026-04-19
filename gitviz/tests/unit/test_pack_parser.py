"""Tests for pack file parser."""

import pytest
from pathlib import Path

from gitviz.parser.pack import PackIndex


def test_pack_index_import():
    """Test that PackIndex can be imported."""
    assert PackIndex is not None


def test_pack_parser_import():
    """Test that PackFileParser can be imported."""
    from gitviz.parser.pack import PackFileParser

    assert PackFileParser is not None
