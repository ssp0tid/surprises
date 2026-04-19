"""Tests for entity system."""

import pytest
from src.game.entities.base import (
    Entity,
    EntityType,
    EntityFactory,
    PositionComponent,
    VelocityComponent,
    HealthComponent,
    CollisionComponent,
)


class TestEntity:
    """Tests for Entity class."""

    def test_entity_creation(self):
        """Test basic entity creation."""
        entity = Entity(EntityType.PLAYER)
        assert entity.type == EntityType.PLAYER
        assert entity.active is True
        assert entity.id is not None

    def test_component_add_get(self):
        """Test adding and retrieving components."""
        entity = Entity(EntityType.PLAYER)
        pos = PositionComponent(x=10, y=20)

        entity.add_component(pos)

        assert entity.has_component(PositionComponent)
        assert entity.get_component(PositionComponent) is pos
        assert entity.position is pos

    def test_component_removal(self):
        """Test removing components."""
        entity = Entity(EntityType.PLAYER)
        entity.add_component(PositionComponent())

        assert entity.has_component(PositionComponent)

        removed = entity.remove_component(PositionComponent)
        assert removed is True
        assert entity.has_component(PositionComponent) is False

    def test_tags(self):
        """Test entity tagging."""
        entity = Entity(EntityType.PLAYER)
        entity.add_tag("player")
        entity.add_tag("solid")

        assert entity.has_tag("player")
        assert entity.has_tag("solid")
        assert not entity.has_tag("enemy")


class TestEntityFactory:
    """Tests for EntityFactory."""

    def test_player_factory(self):
        """Test player entity factory."""
        player = EntityFactory.create_player()

        assert player.type == EntityType.PLAYER
        assert player.has_tag("player")
        assert player.has_component(HealthComponent)
        assert player.health.current == 100

    def test_asteroid_factory_sizes(self):
        """Test asteroid factory with different sizes."""
        large = EntityFactory.create_asteroid("large")
        medium = EntityFactory.create_asteroid("medium")
        small = EntityFactory.create_asteroid("small")

        assert large.type == EntityType.ASTEROID_LARGE
        assert medium.type == EntityType.ASTEROID_MEDIUM
        assert small.type == EntityType.ASTEROID_SMALL

        assert large.collision.radius > medium.collision.radius
        assert medium.collision.radius > small.collision.radius

    def test_bullet_factory(self):
        """Test bullet factory."""
        bullet = EntityFactory.create_bullet(10, 20, -100, is_player=True)

        assert bullet.has_tag("bullet")
        assert bullet.has_tag("solid")
        assert bullet.position.x == 10
        assert bullet.position.y == 20
