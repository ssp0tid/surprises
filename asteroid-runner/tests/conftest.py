"""Test configuration."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def sample_entity_data():
    """Sample entity data for testing."""
    return {
        "x": 10.0,
        "y": 20.0,
        "vx": 5.0,
        "vy": -3.0,
        "health": 100,
        "max_health": 100,
    }


@pytest.fixture
def game_config():
    """Game configuration for testing."""
    from src.game.config import GameConfig

    return GameConfig()
