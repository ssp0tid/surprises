"""Tests for persistence."""

import pytest
import tempfile
from pathlib import Path
from src.persistence.high_scores import HighScoreManager


class TestHighScoreManager:
    """Tests for high score persistence."""

    def test_empty_scores(self):
        """Test manager with no scores."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "scores.json"
            manager = HighScoreManager(filepath)

            scores = manager.get_scores()
            assert scores == []

    def test_add_score(self):
        """Test adding a score."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "scores.json"
            manager = HighScoreManager(filepath)

            rank = manager.add_score("TEST", 100)

            assert rank == 1
            scores = manager.get_scores()
            assert len(scores) == 1
            assert scores[0] == ("TEST", 100)

    def test_high_score_check(self):
        """Test high score qualification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "scores.json"
            manager = HighScoreManager(filepath)

            assert manager.is_high_score(100)

            for i in range(10):
                manager.add_score(f"PLAYER{i}", 1000 - i * 50)

            assert not manager.is_high_score(50)
            assert manager.is_high_score(2000)
