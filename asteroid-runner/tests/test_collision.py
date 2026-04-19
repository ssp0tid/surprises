"""Tests for collision detection."""

import pytest
from src.game.entities.base import EntityFactory
from src.game.systems.collision import CollisionSystem, CollisionGrid


class TestCollisionGrid:
    """Tests for CollisionGrid."""

    def test_grid_insert(self):
        """Test inserting entities into grid."""
        grid = CollisionGrid(cell_size=10)
        entity = EntityFactory.create_player()
        entity.position.x = 15
        entity.position.y = 25

        grid.insert(entity)

        assert entity in grid.get_nearby(entity)

    def test_grid_clear(self):
        """Test clearing grid."""
        grid = CollisionGrid(cell_size=10)
        entity = EntityFactory.create_player()
        grid.insert(entity)

        grid.clear()

        assert entity not in grid.get_nearby(entity)


class TestCollisionDetection:
    """Tests for collision detection."""

    def test_circle_collision(self):
        """Test basic circle-circle collision."""
        collision = CollisionSystem()

        entity_a = EntityFactory.create_player()
        entity_b = EntityFactory.create_asteroid(
            "medium", x=entity_a.position.x + 1, y=entity_a.position.y
        )

        assert collision._check_collision(entity_a, entity_b)

    def test_no_collision(self):
        """Test entities not colliding."""
        collision = CollisionSystem()

        entity_a = EntityFactory.create_player()
        entity_b = EntityFactory.create_asteroid("small", x=100, y=100)

        assert not collision._check_collision(entity_a, entity_b)

    def test_can_collide_rules(self):
        """Test collision rules."""
        collision = CollisionSystem()

        player = EntityFactory.create_player()
        asteroid = EntityFactory.create_asteroid("medium")

        assert collision._can_collide(player, asteroid)

        enemy = EntityFactory.create_enemy("basic")
        assert collision._can_collide(player, enemy)
