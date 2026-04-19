"""Base entity classes and factory functions."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

PLAYER_SHIP = """
    ▲
   /|\\
  / | \\
"""

PLAYER_SHIP_SMALL = "▲"

ENEMY_BASIC = """
< ○ >
"""

ENEMY_ADVANCED = """
◄◄►
 ○○ 
"""

ENEMY_BOSS = """
╔═══╗
║▼▼▼║
╚═╦═╝
  ║
"""

ASTEROID_LARGE = """
  ***  
 *   * 
*     *
 *   * 
  ***  
"""

ASTEROID_MEDIUM = """
 ** 
 *  *
  ** 
"""

ASTEROID_SMALL = " * "

BULLET_PLAYER = "│"
BULLET_ENEMY = "▼"

EXPLOSION = """
  *◆*  
 *   * 
*  ✦  *
 *   * 
  *◆*  
"""


class EntityType(Enum):
    """All possible entity types in the game."""

    PLAYER = auto()
    ENEMY_BASIC = auto()
    ENEMY_ADVANCED = auto()
    ENEMY_BOSS = auto()
    ASTEROID_LARGE = auto()
    ASTEROID_MEDIUM = auto()
    ASTEROID_SMALL = auto()
    BULLET_PLAYER = auto()
    BULLET_ENEMY = auto()
    POWERUP = auto()
    EFFECT = auto()


class Component:
    """Base component class for ECS-lite pattern."""

    pass


@dataclass
class PositionComponent(Component):
    """World position of an entity."""

    x: float = 0.0
    y: float = 0.0


@dataclass
class VelocityComponent(Component):
    """Velocity vector of an entity."""

    vx: float = 0.0
    vy: float = 0.0


@dataclass
class HealthComponent(Component):
    """Health points of an entity."""

    current: int = 100
    max: int = 100


@dataclass
class CollisionComponent(Component):
    """Collision bounds of an entity."""

    radius: float = 1.0


@dataclass
class RenderComponent(Component):
    """Visual representation data."""

    ascii_art: str = ""
    color: Optional[str] = None
    width: int = 1
    height: int = 1
    layer: int = 0


@dataclass
class AIComponent(Component):
    """AI behavior configuration."""

    behavior: str = "none"
    target: Optional[uuid.UUID] = None
    state: str = "idle"
    cooldown: float = 0.0


@dataclass
class DamageComponent(Component):
    """Damage dealt on collision."""

    amount: int = 10


@dataclass
class ScoreComponent(Component):
    """Points awarded when destroyed."""

    points: int = 0


class Entity:
    """Base entity class with component-based architecture."""

    def __init__(self, entity_type: EntityType) -> None:
        self.id = uuid.uuid4()
        self.type = entity_type
        self.active = True
        self._components: dict[type, Component] = {}
        self._tags: set[str] = set()

    def add_component(self, component: Component) -> Entity:
        """Add a component to this entity. Returns self for chaining."""
        self._components[type(component)] = component
        return self

    def get_component(self, component_type: type[Component]) -> Optional[Component]:
        """Get a component by type, or None if not found."""
        return self._components.get(component_type)

    def has_component(self, component_type: type[Component]) -> bool:
        """Check if entity has a component."""
        return component_type in self._components

    def remove_component(self, component_type: type[Component]) -> bool:
        """Remove and return a component, or None if not found."""
        return self._components.pop(component_type, None) is not None

    def add_tag(self, tag: str) -> Entity:
        """Add a tag for quick filtering."""
        self._tags.add(tag)
        return self

    def has_tag(self, tag: str) -> bool:
        """Check if entity has a tag."""
        return tag in self._tags

    def remove_tag(self, tag: str) -> bool:
        """Remove a tag."""
        return self._tags.discard(tag) is None

    @property
    def position(self) -> PositionComponent:
        """Get position component (creates if missing)."""
        if not self.has_component(PositionComponent):
            self.add_component(PositionComponent())
        return self.get_component(PositionComponent)  # type: ignore

    @property
    def velocity(self) -> VelocityComponent:
        """Get velocity component (creates if missing)."""
        if not self.has_component(VelocityComponent):
            self.add_component(VelocityComponent())
        return self.get_component(VelocityComponent)  # type: ignore

    @property
    def health(self) -> Optional[HealthComponent]:
        """Get health component if present."""
        return self.get_component(HealthComponent)

    @property
    def collision(self) -> Optional[CollisionComponent]:
        """Get collision component if present."""
        return self.get_component(CollisionComponent)

    @property
    def render(self) -> Optional[RenderComponent]:
        """Get render component if present."""
        return self.get_component(RenderComponent)

    def __repr__(self) -> str:
        return f"Entity({self.type.name}, id={self.id})"


class EntityFactory:
    """Factory for creating game entities with predefined configurations."""

    @staticmethod
    def create_player() -> Entity:
        """Create player ship entity."""
        return (
            Entity(EntityType.PLAYER)
            .add_component(PositionComponent(x=40, y=35))
            .add_component(VelocityComponent())
            .add_component(HealthComponent(current=100, max=100))
            .add_component(CollisionComponent(radius=2.0))
            .add_component(
                RenderComponent(
                    ascii_art=PLAYER_SHIP_SMALL, color="bright_green", width=3, height=3, layer=10
                )
            )
            .add_component(DamageComponent(amount=0))
            .add_component(ScoreComponent(points=0))
            .add_tag("player")
            .add_tag("solid")
        )

    @staticmethod
    def create_asteroid(size: str = "medium", x: float = 0, y: float = 0) -> Entity:
        """Create asteroid entity."""
        sizes = {
            "large": (EntityType.ASTEROID_LARGE, 5.0, 50, ASTEROID_LARGE, 5, 5),
            "medium": (EntityType.ASTEROID_MEDIUM, 3.0, 25, ASTEROID_MEDIUM, 3, 3),
            "small": (EntityType.ASTEROID_SMALL, 1.5, 10, ASTEROID_SMALL, 1, 1),
        }
        entity_type, radius, points, art, width, height = sizes.get(size, sizes["medium"])

        return (
            Entity(entity_type)
            .add_component(PositionComponent(x=x, y=y))
            .add_component(VelocityComponent(vx=0, vy=0))
            .add_component(HealthComponent(current=1, max=1))
            .add_component(CollisionComponent(radius=radius))
            .add_component(
                RenderComponent(ascii_art=art, color="yellow", width=width, height=height, layer=5)
            )
            .add_component(DamageComponent(amount=10))
            .add_component(ScoreComponent(points=points))
            .add_tag("asteroid")
            .add_tag("solid")
        )

    @staticmethod
    def create_enemy(enemy_type: str = "basic", x: float = 0, y: float = 0) -> Entity:
        """Create enemy entity."""
        types = {
            "basic": (EntityType.ENEMY_BASIC, 1.5, 20, ENEMY_BASIC, 3, 3, "chase", 3),
            "advanced": (EntityType.ENEMY_ADVANCED, 2.0, 50, ENEMY_ADVANCED, 3, 2, "shoot", 5),
            "boss": (EntityType.ENEMY_BOSS, 5.0, 500, ENEMY_BOSS, 7, 5, "dive", 20),
        }
        (entity_type, radius, points, art, width, height, behavior, health) = types.get(
            enemy_type, types["basic"]
        )

        return (
            Entity(entity_type)
            .add_component(PositionComponent(x=x, y=y))
            .add_component(VelocityComponent())
            .add_component(HealthComponent(current=health, max=health))
            .add_component(CollisionComponent(radius=radius))
            .add_component(
                RenderComponent(ascii_art=art, color="red", width=width, height=height, layer=8)
            )
            .add_component(AIComponent(behavior=behavior))
            .add_component(DamageComponent(amount=20))
            .add_component(ScoreComponent(points=points))
            .add_tag("enemy")
            .add_tag("solid")
        )

    @staticmethod
    def create_bullet(x: float, y: float, vy: float, is_player: bool = True) -> Entity:
        """Create bullet entity."""
        return (
            Entity(EntityType.BULLET_PLAYER if is_player else EntityType.BULLET_ENEMY)
            .add_component(PositionComponent(x=x, y=y))
            .add_component(VelocityComponent(vx=0, vy=vy))
            .add_component(CollisionComponent(radius=0.5))
            .add_component(
                RenderComponent(
                    ascii_art=BULLET_PLAYER if is_player else BULLET_ENEMY,
                    color="bright_cyan" if is_player else "bright_red",
                    width=1,
                    height=1,
                    layer=15 if is_player else 7,
                )
            )
            .add_component(DamageComponent(amount=25 if is_player else 15))
            .add_tag("bullet")
            .add_tag("solid" if is_player else "enemy_bullet")
        )

    @staticmethod
    def create_explosion(x: float, y: float) -> Entity:
        """Create explosion effect entity."""
        return (
            Entity(EntityType.EFFECT)
            .add_component(PositionComponent(x=x, y=y))
            .add_component(
                RenderComponent(
                    ascii_art=EXPLOSION, color="bright_yellow", width=5, height=5, layer=20
                )
            )
            .add_tag("effect")
        )
