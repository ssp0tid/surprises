"""Tests for game systems."""

import pytest
from src.game.systems.difficulty import DifficultySystem, ScoringSystem


class TestDifficultySystem:
    """Tests for difficulty progression."""

    def test_base_difficulty(self):
        """Test level 1 has base difficulty."""
        diff = DifficultySystem()
        params = diff.get_params_for_level(1)

        assert params.enemy_speed_multiplier == pytest.approx(1.0, rel=0.1)
        assert params.score_multiplier == pytest.approx(1.0, rel=0.1)

    def test_difficulty_scaling(self):
        """Test difficulty increases with level."""
        diff = DifficultySystem()
        params_1 = diff.get_params_for_level(1)
        params_10 = diff.get_params_for_level(10)

        assert params_10.enemy_speed_multiplier > params_1.enemy_speed_multiplier
        assert params_10.enemy_health_multiplier > params_1.enemy_health_multiplier

    def test_boss_level(self):
        """Test boss level detection."""
        diff = DifficultySystem()

        assert diff.is_boss_level(5)
        assert diff.is_boss_level(10)
        assert not diff.is_boss_level(3)
        assert not diff.is_boss_level(7)


class TestScoringSystem:
    """Tests for scoring."""

    def test_base_score(self):
        """Test basic score calculation."""
        diff = DifficultySystem()
        scoring = ScoringSystem(diff)

        score = scoring.add_kill(10)
        assert score == 10

    def test_combo_multiplier(self):
        """Test combo multiplier increases score."""
        diff = DifficultySystem()
        scoring = ScoringSystem(diff)

        scoring.add_kill(10)
        score = scoring.add_kill(10)

        assert score >= 10

    def test_combo_timeout(self):
        """Test combo resets after timeout."""
        diff = DifficultySystem()
        scoring = ScoringSystem(diff)

        scoring.add_kill(10)
        scoring.update(0.1)

        assert scoring.combo_multiplier >= 1.0
