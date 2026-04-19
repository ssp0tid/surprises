# Terminal ASCII Roguelike Space Shooter - Implementation Plan

## Project Overview

**Project Name:** Asteriod Runner (ASCII Space Shooter)  
**Type:** Real-time Interactive TUI Game  
**Framework:** Python 3.11+ with Textual TUI Framework  
**Core Functionality:** A roguelike space shooter rendered entirely in the terminal with smooth 60fps rendering, procedural content generation, and persistent high scores.  
**Target Users:** Terminal enthusiasts, roguelike fans, casual gamers who appreciate ASCII aesthetics

---

## Table of Contents

1. [Game Concept & Vision](#1-game-concept--vision)
2. [Technical Architecture](#2-technical-architecture)
3. [File Structure](#3-file-structure)
4. [Dependencies](#4-dependencies)
5. [Game Loop Architecture](#5-game-loop-architecture)
6. [Core Systems](#6-core-systems)
7. [Rendering Pipeline](#7-rendering-pipeline)
8. [Input Handling](#8-input-handling)
9. [State Management](#9-state-management)
10. [Collision Detection](#10-collision-detection)
11. [Entity Systems](#11-entity-systems)
12. [Game Mechanics](#12-game-mechanics)
13. [UI Screens](#13-ui-screens)
14. [Error Handling & Edge Cases](#14-error-handling--edge-cases)
15. [Performance Optimization](#15-performance-optimization)
16. [Testing Strategy](#16-testing-strategy)
17. [Implementation Phases](#17-implementation-phases)

---

## 1. Game Concept & Vision

### Gameplay Loop

```
┌─────────────────────────────────────────────────────────────┐
│                    MAIN MENU                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  NEW GAME   │  │ HIGH SCORES │  │   QUIT      │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    GAMEPLAY                                  │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ SCORE: 00000    LEVEL: 01    HEALTH: ████████░░        │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │                                                         │ │
│  │     *              .  *   .                             │ │
│  │          .                    *                        │ │
│  │                    .              .                     │ │
│  │    *     ▲                        *                    │ │
│  │         /|\    < >    *     .                         │ │
│  │        / | \         .              .                  │ │
│  │                  *                        *           │ │
│  │     .                    .                            │ │
│  │  *        .    *                     .                │ │
│  │                                                         │ │
│  └─────────────────────────────────────────────────────────┘ │
│                    [ESC] PAUSE                              │
└─────────────────────────────────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
    ┌──────────────────┐      ┌──────────────────┐
    │     PAUSE        │      │    GAME OVER     │
    │ ┌──────────────┐ │      │  SCORE: 12450    │
    │ │  RESUME      │ │      │  LEVEL: 07       │
    │ │  RESTART     │ │      │  NEW HIGH SCORE! │
    │ │  MAIN MENU   │ │      │ ┌──────────────┐ │
    │ └──────────────┘ │      │ │PLAY AGAIN     │ │
    └──────────────────┘      │ │MAIN MENU      │ │
                             │ └──────────────┘ │
                             └──────────────────┘
```

### ASCII Art Assets

```python
# Player Ship (pointing up)
PLAYER_SHIP = """
    ▲
   /|\\
  / | \\
"""

PLAYER_SHIP_SMALL = "▲"

# Enemy Ships
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

# Asteroids (various sizes)
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

# Projectiles
BULLET_PLAYER = "│"
BULLET_ENEMY = "▼"

# Effects
EXPLOSION = """
  *◆*  
 *   * 
*  ✦  *
 *   * 
  *◆*  
"""

# Health Bar
HEALTH_FULL = "████████"
HEALTH_EMPTY = "░░░░░░░░"
```

---

## 2. Technical Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         APPLICATION                             │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   TEXTUAL   │  │   GAME      │  │      GAME STATE         │ │
│  │   APP       │◄─┤   ENGINE    │◄─┤  ┌─────┐ ┌───────────┐  │ │
│  │  (Main)     │  │  (Update)   │  │  │HUD  │ │ Entities  │  │ │
│  └─────────────┘  └─────────────┘  │  └─────┘ └───────────┘  │ │
│         │                 ▲         │  ┌───────────────────┐  │ │
│         │                 │         │  │ World/Level Gen  │  │ │
│         ▼                 │         │  └───────────────────┘  │ │
│  ┌─────────────┐  ┌─────────────┐  │  ┌───────────────────┐  │ │
│  │  RENDERER   │◄─┤   INPUT     │  │  │ Score/Statistics  │  │ │
│  │  (Widget)   │  │  HANDLER    │  │  └───────────────────┘  │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │                      ▲
         ▼                      │
┌─────────────────┐    ┌─────────────────┐
│   HIGH SCORE    │    │   AUDIO         │
│   PERSISTENCE   │    │   (Optional)    │
│   (JSON File)   │    │   (Beeps)       │
└─────────────────┘    └─────────────────┘
```

### Design Patterns Used

1. **Entity-Component System (ECS-lite)** - Flexible entity composition
2. **State Machine** - Game state transitions
3. **Observer Pattern** - Event-driven updates
4. **Factory Pattern** - Entity creation with pooling
5. **Command Pattern** - Input buffering and undo potential

---

## 3. File Structure

```
asteroid-runner/
├── pyproject.toml                 # Project metadata and dependencies
├── README.md                      # Project documentation
├── PLAN.md                        # This implementation plan
│
├── src/
│   ├── __init__.py
│   │
│   ├── main.py                   # Application entry point
│   │
│   ├── app.py                    # Textual App subclass
│   │
│   ├── game/
│   │   ├── __init__.py
│   │   │
│   │   ├── engine.py             # Core game loop and timing
│   │   ├── state.py              # Game state machine
│   │   │
│   │   ├── entities/
│   │   │   ├── __init__.py
│   │   │   ├── base.py           # Base Entity class
│   │   │   ├── player.py         # Player ship entity
│   │   │   ├── enemy.py          # Enemy ship entities
│   │   │   ├── asteroid.py       # Asteroid entities
│   │   │   ├── bullet.py         # Projectile entities
│   │   │   └── effects.py        # Visual effects (explosions, etc.)
│   │   │
│   │   ├── systems/
│   │   │   ├── __init__.py
│   │   │   ├── collision.py      # Collision detection system
│   │   │   ├── movement.py       # Movement/physics system
│   │   │   ├── spawner.py        # Entity spawning system
│   │   │   ├── difficulty.py     # Difficulty progression
│   │   │   └── scoring.py        # Score calculation
│   │   │
│   │   ├── world/
│   │   │   ├── __init__.py
│   │   │   ├── generator.py      # Procedural generation
│   │   │   └── grid.py           # Spatial grid for optimization
│   │   │
│   │   └── config.py             # Game configuration constants
│   │
│   ├── ui/
│   │   ├── __init__.py
│   │   │
│   │   ├── game_screen.py        # Main game widget
│   │   ├── hud.py                # Heads-up display
│   │   ├── menu_screen.py        # Main menu
│   │   ├── pause_screen.py       # Pause overlay
│   │   ├── game_over_screen.py   # Game over display
│   │   ├── high_scores_screen.py # High scores display
│   │   │
│   │   └── widgets/
│   │       ├── __init__.py
│   │       ├── ascii_art.py      # ASCII art rendering
│   │       ├── health_bar.py     # Health bar widget
│   │       └── animated_text.py   # Text animations
│   │
│   ├── input/
│   │   ├── __init__.py
│   │   ├── handler.py            # Input processing
│   │   └── keybindings.py        # Key configuration
│   │
│   ├── persistence/
│   │   ├── __init__.py
│   │   ├── high_scores.py        # High score management
│   │   └── save_manager.py       # General save/load
│   │
│   └── utils/
│       ├── __init__.py
│       ├── vector2.py             # 2D vector math
│       ├── random_utils.py       # Seeded random utilities
│       ├── timing.py             # Delta time and FPS
│       └── debug.py              # Debug utilities
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # Pytest fixtures
│   │
│   ├── test_entities.py          # Entity unit tests
│   ├── test_collision.py          # Collision detection tests
│   ├── test_systems.py            # System tests
│   ├── test_world.py              # World generation tests
│   ├── test_persistence.py         # Save/load tests
│   │
│   └── test_integration.py        # Integration tests
│
├── assets/
│   └── high_scores.json          # High scores data file
│
└── docs/
    ├── ARCHITECTURE.md           # Detailed architecture docs
    └── CONTROLS.md               # User controls documentation
```

---

## 4. Dependencies

### pyproject.toml

```toml
[project]
name = "asteroid-runner"
version = "1.0.0"
description = "Terminal ASCII Roguelike Space Shooter"
readme = "README.md"
requires-python = ">=3.11"
license = { text = "MIT" }
authors = [
    { name = "Developer" }
]
keywords = ["game", "ascii", "roguelike", "terminal", "tui"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: End Users/Desktop",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Games/Entertainment :: Arcade",
]

dependencies = [
    "textual>=0.52.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.21.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
filterwarnings = [
    "ignore::DeprecationWarning",
]

[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "W", "I", "N", "D", "UP", "YTT", "ANN", "S", "BLE", "FBT", "B", "A", "COM", "C4", "DTZ", "T10", "DJ", "EM", "EXE", "ISC", "ICN", "G", "INP", "PIE", "T20", "PYI", "PT", "Q", "RSE", "RET", "SLF", "SIM", "TID", "TCH", "ARG", "PTH", "ERA", "PD", "PGH", "PL", "TRY", "RUF", "UP"]
ignore = ["D100", "D101", "D102", "D103", "D104", "D105", "D107", "D203", "D213", "ANN101", "ANN102", "ANN401", "PLR0913", "PLR2004"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.hatch.build.targets.wheel]
packages = ["src"]
```

### Minimum System Requirements

- Python 3.11 or later
- Terminal with ANSI/VT100 support
- Minimum 80x24 terminal size (recommended 120x40 for best experience)
- Keyboard with function keys support (for F-keys if used)

---

## 5. Game Loop Architecture

### Fixed vs Variable Timestep

```
┌─────────────────────────────────────────────────────────────────┐
│                    GAME LOOP OVERVIEW                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │  INPUT   │───▶│  UPDATE  │───▶│ PHYSICS  │───▶│ RENDER   │ │
│  │  (16ms)  │    │  (16ms)  │    │ (16ms)   │    │ (16ms)   │ │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘ │
│       │              │               │               │        │
│       ▼              ▼               ▼               ▼        │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                    FRAME @ 60 FPS                        │  │
│  │                 (16.67ms per frame)                     │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Game Loop Implementation

```python
# src/game/engine.py

import time
from dataclasses import dataclass, field
from typing import Callable, Optional
from collections import deque

import textual.logging
from textual.message import Message

logger = textual.logging.get_logger()


@dataclass
class TimingStats:
    """Runtime statistics for performance monitoring."""
    frame_times: deque[float] = field(default_factory=lambda: deque(maxlen=60))
    update_times: deque[float] = field(default_factory=lambda: deque(maxlen=60))
    render_times: deque[float] = field(default_factory=lambda: deque(maxlen=60))
    fps: float = 60.0
    update_rate: float = 60.0
    dropped_frames: int = 0


class GameLoop:
    """
    Fixed timestep game loop running at 60 FPS.
    
    Architecture:
    ┌─────────────────────────────────────────────────────────┐
    │                     GAME LOOP                            │
    │  ┌─────────────────────────────────────────────────┐   │
    │  │              accumulator = 0.0                   │   │
    │  │  ┌───────────────────────────────────────────┐   │   │
    │  │  │  while running:                            │   │   │
    │  │  │    currentTime = performance_counter()     │   │   │
    │  │  │    frameTime = currentTime - lastTime      │   │   │
    │  │  │    lastTime = currentTime                   │   │   │
    │  │  │    accumulator += frameTime                 │   │   │
    │  │  │                                            │   │   │
    │  │  │    # Fixed timestep updates                │   │   │
    │  │  │    while accumulator >= FIXED_DT:          │   │   │
    │  │  │      process_input()                       │   │   │
    │  │  │      update(FIXED_DT)                      │   │   │
    │  │  │      accumulator -= FIXED_DT               │   │   │
    │  │  │                                            │   │   │
    │  │  │    # Variable timestep render              │   │   │
    │  │  │    alpha = accumulator / FIXED_DT         │   │   │
    │  │  │    render(alpha)  # interpolation ready    │   │   │
    │  │  └───────────────────────────────────────────┘   │   │
    │  └─────────────────────────────────────────────────┘   │
    └─────────────────────────────────────────────────────────┘
    """

    FIXED_DT: float = 1.0 / 60.0  # 60 updates per second
    MAX_FRAME_SKIP: int = 5       # Max updates before skipping render
    TARGET_FPS: float = 60.0
    TARGET_FRAME_TIME: float = 1.0 / TARGET_FPS

    def __init__(
        self,
        update_callback: Callable[[float], None],
        render_callback: Callable[[float], None],
        input_callback: Callable[[], None],
    ) -> None:
        self._update = update_callback
        self._render = render_callback
        self._process_input = input_callback
        
        self._running = False
        self._paused = False
        self._accumulator: float = 0.0
        self._last_time: float = 0.0
        self._current_time: float = 0.0
        
        self._stats = TimingStats()
        
        # For delta time in render
        self._interpolation_alpha: float = 0.0

    def start(self) -> None:
        """Start the game loop."""
        self._running = True
        self._paused = False
        self._last_time = self._get_time()
        logger.info("Game loop started")

    def stop(self) -> None:
        """Stop the game loop."""
        self._running = False
        logger.info("Game loop stopped")

    def pause(self) -> None:
        """Pause the game loop."""
        self._paused = True
        logger.info("Game loop paused")

    def resume(self) -> None:
        """Resume the game loop."""
        self._paused = False
        self._last_time = self._get_time()
        self._accumulator = 0.0
        logger.info("Game loop resumed")

    def _get_time(self) -> float:
        """Get current time in seconds using high-resolution timer."""
        return time.perf_counter()

    def _calculate_fps(self) -> float:
        """Calculate rolling average FPS from frame times."""
        if not self._stats.frame_times:
            return 0.0
        avg_frame_time = sum(self._stats.frame_times) / len(self._stats.frame_times)
        return 1.0 / avg_frame_time if avg_frame_time > 0 else 0.0

    def tick(self) -> bool:
        """
        Execute one game loop iteration.
        
        Returns:
            True if frame was processed, False if skipped (e.g., paused)
        """
        if not self._running or self._paused:
            return False

        frame_start = self._get_time()
        
        # Calculate delta time
        self._current_time = self._get_time()
        frame_time = self._current_time - self._last_time
        self._last_time = self._current_time

        # Clamp frame time to prevent spiral of death
        if frame_time > 0.25:
            frame_time = 0.25
            logger.warning("Frame time clamped to 250ms")

        self._accumulator += frame_time

        # Fixed timestep updates
        update_count = 0
        while self._accumulator >= self.FIXED_DT:
            update_start = self._get_time()
            
            self._process_input()
            self._update(self.FIXED_DT)
            
            update_end = self._get_time()
            self._stats.update_times.append(update_end - update_start)
            
            self._accumulator -= self.FIXED_DT
            update_count += 1

            # Prevent update spiral (emergency brake)
            if update_count > self.MAX_FRAME_SKIP:
                logger.warning(f"Skipping render: {update_count} updates needed")
                self._stats.dropped_frames += 1
                self._accumulator = 0.0
                break

        # Calculate interpolation alpha for smooth rendering
        self._interpolation_alpha = self._accumulator / self.FIXED_DT

        # Render with interpolation
        render_start = self._get_time()
        self._render(self._interpolation_alpha)
        render_end = self._get_time()

        # Record timing stats
        frame_end = self._get_time()
        self._stats.frame_times.append(frame_end - frame_start)
        self._stats.render_times.append(render_end - render_start)
        self._stats.fps = self._calculate_fps()

        return True

    @property
    def stats(self) -> TimingStats:
        """Get current timing statistics."""
        return self._stats

    @property
    def is_running(self) -> bool:
        """Check if game loop is running."""
        return self._running

    @property
    def is_paused(self) -> bool:
        """Check if game loop is paused."""
        return self._paused


class GameLoopDriver:
    """
    Drives the game loop using Textual's reactive updates.
    
    Integrates with Textual's update cycle to achieve 60 FPS rendering
    while maintaining fixed timestep physics.
    """

    def __init__(self, game_loop: GameLoop) -> None:
        self._game_loop = game_loop
        self._frame_count: int = 0

    def on_update(self) -> None:
        """
        Called by Textual on each animation frame.
        This is our hook into Textual's update cycle.
        """
        self._frame_count += 1
        self._game_loop.tick()
```

---

## 6. Core Systems

### Entity System

```python
# src/game/entities/base.py

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..engine import GameEngine


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
    """
    Base component class for ECS-lite pattern.
    
    Components are data containers that can be attached to entities.
    They should not contain logic, only data.
    """
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
    radius: float = 1.0  # Circular collision radius


@dataclass
class RenderComponent(Component):
    """Visual representation data."""
    ascii_art: str = ""
    color: Optional[str] = None
    width: int = 1
    height: int = 1
    layer: int = 0  # Rendering order (higher = on top)


@dataclass
class AIComponent(Component):
    """AI behavior configuration."""
    behavior: str = "none"  # "chase", "wander", "shoot", "dive"
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
    """
    Base entity class with component-based architecture.
    
    Entity ──────────────────────────────────────────────────┐
    │                                                         │
    │  Has-a Components:                                      │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
    │  │  Position   │  │   Velocity  │  │   Health    │    │
    │  │  (x, y)     │  │  (vx, vy)   │  │  (hp/max)   │    │
    │  └─────────────┘  └─────────────┘  └─────────────┘    │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
    │  │  Collision  │  │   Render    │  │     AI     │    │
    │  │  (radius)   │  │  (art/layer)│  │  (behavior)│    │
    │  └─────────────┘  └─────────────┘  └─────────────┘    │
    │                                                         │
    └─────────────────────────────────────────────────────────┘
    """

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

    def add_tag(self, tag: str) -> None:
        """Add a tag for quick filtering."""
        self._tags.add(tag)

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
    """
    Factory for creating game entities with predefined configurations.
    
    Provides type-safe entity creation with sensible defaults.
    """

    @staticmethod
    def create_player() -> Entity:
        """Create player ship entity."""
        return (
            Entity(EntityType.PLAYER)
            .add_component(PositionComponent(x=40, y=35))
            .add_component(VelocityComponent())
            .add_component(HealthComponent(current=100, max=100))
            .add_component(CollisionComponent(radius=2.0))
            .add_component(RenderComponent(
                ascii_art=PLAYER_SHIP_SMALL,
                color="bright_green",
                width=3,
                height=3,
                layer=10
            ))
            .add_component(DamageComponent(amount=0))  # Player doesn't deal collision damage
            .add_component(ScoreComponent(points=0))
            .add_tag("player")
            .add_tag("solid")
        )

    @staticmethod
    def create_asteroid(size: str = "medium", x: float = 0, y: float = 0) -> Entity:
        """Create asteroid entity."""
        sizes = {
            "large": (EntityType.ASTEROID_LARGE, 5.0, 50, ASTEROID_LARGE),
            "medium": (EntityType.ASTEROID_MEDIUM, 3.0, 25, ASTEROID_MEDIUM),
            "small": (EntityType.ASTEROID_SMALL, 1.5, 10, ASTEROID_SMALL),
        }
        entity_type, radius, points, art = sizes.get(size, sizes["medium"])
        
        return (
            Entity(entity_type)
            .add_component(PositionComponent(x=x, y=y))
            .add_component(VelocityComponent(vx=0, vy=0))
            .add_component(HealthComponent(current=1, max=1))
            .add_component(CollisionComponent(radius=radius))
            .add_component(RenderComponent(
                ascii_art=art,
                color="yellow",
                width=5 if size == "large" else 3 if size == "medium" else 1,
                height=5 if size == "large" else 3 if size == "medium" else 1,
                layer=5
            ))
            .add_component(DamageComponent(amount=10))
            .add_component(ScoreComponent(points=points))
            .add_tag("asteroid")
            .add_tag("solid")
        )

    @staticmethod
    def create_enemy(enemy_type: str = "basic", x: float = 0, y: float = 0) -> Entity:
        """Create enemy entity."""
        types = {
            "basic": (EntityType.ENEMY_BASIC, 1.5, 20, ENEMY_BASIC, "chase"),
            "advanced": (EntityType.ENEMY_ADVANCED, 2.0, 50, ENEMY_ADVANCED, "shoot"),
            "boss": (EntityType.ENEMY_BOSS, 5.0, 500, ENEMY_BOSS, "dive"),
        }
        entity_type, radius, points, art, behavior = types.get(enemy_type, types["basic"])
        
        return (
            Entity(entity_type)
            .add_component(PositionComponent(x=x, y=y))
            .add_component(VelocityComponent())
            .add_component(HealthComponent(current=3 if enemy_type == "basic" else 5 if enemy_type == "advanced" else 20, max=3))
            .add_component(CollisionComponent(radius=radius))
            .add_component(RenderComponent(
                ascii_art=art,
                color="red",
                width=3 if enemy_type != "boss" else 7,
                height=3 if enemy_type != "boss" else 5,
                layer=8
            ))
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
            .add_component(RenderComponent(
                ascii_art=BULLET_PLAYER if is_player else BULLET_ENEMY,
                color="bright_cyan" if is_player else "bright_red",
                width=1,
                height=1,
                layer=15 if is_player else 7
            ))
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
            .add_component(RenderComponent(
                ascii_art=EXPLOSION,
                color="bright_yellow",
                width=5,
                height=5,
                layer=20
            ))
            .add_tag("effect")
        )


# ASCII Art Constants (defined at module level for factory access)
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
```

---

## 7. Rendering Pipeline

```python
# src/ui/game_screen.py

from __future__ import annotations

from typing import TYPE_CHECKING, Iterator
from dataclasses import dataclass

from textual.app import RenderResult
from textual.widget import Widget
from textual.scrollbar import ScrollBarTheme
from textual.color import Color

if TYPE_CHECKING:
    from ..game.engine import GameEngine


@dataclass
class RenderLayer:
    """A single layer of rendered entities for sorting."""
    entities: list["Entity"]


class GameRenderer(Widget):
    """
    Main game rendering widget using Textual's chunked rendering.
    
    Rendering Pipeline:
    ┌─────────────────────────────────────────────────────────────────┐
    │                    RENDERING PIPELINE                           │
    │                                                                  │
    │  1. Collect all active entities                                  │
    │  2. Sort by layer (ascending)                                    │
    │  3. For each layer:                                              │
    │     ┌─────────────────────────────────────────────────────────┐ │
    │     │  Convert world coords → screen coords                     │ │
    │     │  Clip to visible area                                    │ │
    │     │  Apply color/style                                        │ │
    │     │  Render ASCII art                                         │ │
    │     └─────────────────────────────────────────────────────────┘ │
    │  4. Composite layers (background to foreground)                  │
    │  5. Draw UI overlay (HUD, effects)                               │
    │                                                                  │
    └─────────────────────────────────────────────────────────────────┘
    """

    # ANSI color codes for ASCII rendering
    COLORS = {
        "white": "\x1b[37m",
        "bright_green": "\x1b[92m",
        "bright_cyan": "\x1b[96m",
        "bright_red": "\x1b[91m",
        "bright_yellow": "\x1b[93m",
        "yellow": "\x1b[33m",
        "red": "\x1b[31m",
        "cyan": "\x1b[36m",
        "reset": "\x1b[0m",
        "bold": "\x1b[1m",
    }

    def __init__(self, engine: "GameEngine") -> None:
        super().__init__()
        self._engine = engine
        self._framebuffer: list[list[str]] = []
        self._dirty = True

    def on_mount(self) -> None:
        """Initialize renderer on mount."""
        self.update_scrollbar_theme(ScrollBarTheme())

    def render(self) -> RenderResult:
        """Main render method called by Textual."""
        if not self._engine.is_running:
            yield from self._render_empty()
            return

        # Update framebuffer
        self._update_framebuffer()

        # Render framebuffer to Textual
        for row in self._framebuffer:
            yield "".join(row)
            yield "\n"

    def _render_empty(self) -> Iterator[str]:
        """Render empty state."""
        yield " " * self.size.width
        yield "\n"

    def _update_framebuffer(self) -> None:
        """Update the ASCII framebuffer from game state."""
        width = self.size.width
        height = self.size.height

        # Initialize empty framebuffer
        self._framebuffer = [[" " for _ in range(width)] for _ in range(height)]

        # Get all visible entities sorted by layer
        entities = sorted(
            self._engine.get_visible_entities(),
            key=lambda e: e.render.layer if e.render else 0
        )

        # Render each entity
        for entity in entities:
            if not entity.active or not entity.render:
                continue

            pos = entity.position
            art = entity.render.ascii_art
            color = entity.render.color

            # Convert world position to screen position (center of viewport)
            screen_x = int(pos.x)
            screen_y = int(pos.y)

            # Render ASCII art (multi-line)
            for dy, line in enumerate(art.split("\n")):
                row = screen_y + dy
                if 0 <= row < height:
                    for dx, char in enumerate(line):
                        col = screen_x + dx - len(line) // 2
                        if 0 <= col < width and char != " ":
                            cell = self.COLORS.get(color, "") + char + self.COLORS["reset"]
                            self._framebuffer[row][col] = cell

    def clear(self) -> None:
        """Mark renderer as needing full refresh."""
        self._dirty = True


class HUDRenderer:
    """
    Renders the heads-up display overlay.
    
    Layout:
    ┌─────────────────────────────────────────────────────────────────┐
    │ SCORE: 00000    LEVEL: 01    HEALTH: ████████░░    FPS: 60     │
    └─────────────────────────────────────────────────────────────────┘
    """

    def __init__(self) -> None:
        self._display_cache: dict[str, str] = {}

    def render_hud(
        self,
        score: int,
        level: int,
        health: int,
        max_health: int,
        fps: float,
        width: int,
    ) -> str:
        """Render the HUD bar."""
        # Format components
        score_str = f"SCORE: {score:05d}"
        level_str = f"LEVEL: {level:02d}"
        
        # Health bar
        health_ratio = health / max_health if max_health > 0 else 0
        filled = int(health_ratio * 10)
        health_bar = "█" * filled + "░" * (10 - filled)
        health_str = f"HEALTH: {health_bar}"
        
        fps_str = f"FPS: {fps:.0f}"

        # Compose HUD
        hud = f"{score_str}   {level_str}   {health_str}   {fps_str}"
        
        # Pad to screen width
        if len(hud) < width:
            hud += " " * (width - len(hud))
        
        return hud[:width]
```

---

## 8. Input Handling

```python
# src/input/handler.py

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Optional, Set

from textual import on
from textual.app import ComposeResult
from textual.events import Key
from textual.message import Message
from textual.widgets import Button, Static


class InputAction(Enum):
    """All possible player actions from input."""
    MOVE_UP = auto()
    MOVE_DOWN = auto()
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    SHOOT = auto()
    PAUSE = auto()
    MENU_UP = auto()
    MENU_DOWN = auto()
    MENU_SELECT = auto()
    MENU_BACK = auto()


@dataclass
class InputState:
    """Current state of all input axes."""
    up: bool = False
    down: bool = False
    left: bool = False
    right: bool = False
    shoot: bool = False


@dataclass
class KeyBinding:
    """Configuration for a key binding."""
    key: str
    action: InputAction
    modifiers: tuple[str, ...] = field(default_factory=tuple)


class InputHandler:
    """
    Centralized input handling system.
    
    Input Flow:
    ┌─────────────────────────────────────────────────────────────────┐
    │                     INPUT HANDLING                              │
    │                                                                  │
    │  KeyEvent ──▶ InputHandler ──▶ ActionQueue ──▶ GameEngine        │
    │                    │                        │                   │
    │                    ▼                        ▼                   │
    │              KeyMappings              ActionProcessor           │
    │                                                                  │
    │  Supported Inputs:                                              │
    │  ┌─────────────────────────────────────────────────────────┐    │
    │  │ Movement:  WASD / Arrow Keys / IJKL / HJKL (vim)        │    │
    │  │ Shoot:     Space / Z / Enter                            │    │
    │  │ Pause:     Escape / P / Tab                            │    │
    │  │ Menu:      W/S/Up/Down + Enter to select               │    │
    │  └─────────────────────────────────────────────────────────┘    │
    │                                                                  │
    └─────────────────────────────────────────────────────────────────┘
    """

    # Default key bindings (supports multiple input styles)
    DEFAULT_BINDINGS: list[KeyBinding] = [
        # Movement - WASD
        KeyBinding("w", InputAction.MOVE_UP),
        KeyBinding("s", InputAction.MOVE_DOWN),
        KeyBinding("a", InputAction.MOVE_LEFT),
        KeyBinding("d", InputAction.MOVE_RIGHT),
        
        # Movement - Arrow Keys
        KeyBinding("up", InputAction.MOVE_UP),
        KeyBinding("down", InputAction.MOVE_DOWN),
        KeyBinding("left", InputAction.MOVE_LEFT),
        KeyBinding("right", InputAction.MOVE_RIGHT),
        
        # Movement - Vim style
        KeyBinding("i", InputAction.MOVE_UP),
        KeyBinding("k", InputAction.MOVE_DOWN),
        KeyBinding("j", InputAction.MOVE_LEFT),
        KeyBinding("l", InputAction.MOVE_RIGHT),
        
        # Shoot
        KeyBinding("space", InputAction.SHOOT),
        KeyBinding("z", InputAction.SHOOT),
        
        # Pause
        KeyBinding("escape", InputAction.PAUSE),
        KeyBinding("p", InputAction.PAUSE),
        
        # Menu
        KeyBinding("w", InputAction.MENU_UP),
        KeyBinding("s", InputAction.MENU_DOWN),
        KeyBinding("up", InputAction.MENU_UP),
        KeyBinding("down", InputAction.MENU_DOWN),
        KeyBinding("enter", InputAction.MENU_SELECT),
    ]

    def __init__(self) -> None:
        self._bindings: dict[str, InputAction] = {}
        self._state = InputState()
        self._action_queue: list[InputAction] = []
        self._shoot_cooldown: float = 0.0
        self._shoot_delay: float = 0.15  # 150ms between shots

        # Build lookup table
        for binding in self.DEFAULT_BINDINGS:
            self._bindings[binding.key.lower()] = binding.action

    def process_key(self, key: Key) -> Optional[InputAction]:
        """
        Process a key event and return the corresponding action.
        
        Args:
            key: The Key event from Textual
            
        Returns:
            The InputAction if the key maps to an action, None otherwise
        """
        key_name = key.key.lower()
        
        if key_name in self._bindings:
            action = self._bindings[key_name]
            
            # Handle key press vs release
            if key.events == "pressed":
                self._handle_action_press(action)
            elif key.events == "released":
                self._handle_action_release(action)
            
            return action
        
        return None

    def _handle_action_press(self, action: InputAction) -> None:
        """Handle action key press."""
        # Update state
        match action:
            case InputAction.MOVE_UP:
                self._state.up = True
            case InputAction.MOVE_DOWN:
                self._state.down = True
            case InputAction.MOVE_LEFT:
                self._state.left = True
            case InputAction.MOVE_RIGHT:
                self._state.right = True
            case InputAction.SHOOT:
                self._state.shoot = True
        
        # Queue action (for immediate response actions)
        if action not in self._action_queue:
            self._action_queue.append(action)

    def _handle_action_release(self, action: InputAction) -> None:
        """Handle action key release."""
        match action:
            case InputAction.MOVE_UP:
                self._state.up = False
            case InputAction.MOVE_DOWN:
                self._state.down = False
            case InputAction.MOVE_LEFT:
                self._state.left = False
            case InputAction.MOVE_RIGHT:
                self._state.right = False
            case InputAction.SHOOT:
                self._state.shoot = False

    def update(self, dt: float) -> None:
        """Update input state (for cooldowns)."""
        if self._shoot_cooldown > 0:
            self._shoot_cooldown -= dt

    def can_shoot(self) -> bool:
        """Check if player can fire (cooldown elapsed)."""
        return self._state.shoot and self._shoot_cooldown <= 0

    def fire_shot(self) -> None:
        """Mark that a shot was fired (starts cooldown)."""
        self._shoot_cooldown = self._shoot_delay

    @property
    def state(self) -> InputState:
        """Get current input state."""
        return self._state

    def pop_action(self) -> Optional[InputAction]:
        """Pop the next action from the queue."""
        if self._action_queue:
            return self._action_queue.pop(0)
        return None

    def clear_queue(self) -> None:
        """Clear all pending actions."""
        self._action_queue.clear()

    def reset(self) -> None:
        """Reset input state to defaults."""
        self._state = InputState()
        self._action_queue.clear()
        self._shoot_cooldown = 0.0
```

---

## 9. State Management

```python
# src/game/state.py

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Optional, TypeVar, Generic

from textual.message import Message


class GameState(Enum):
    """All possible game states."""
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    HIGH_SCORES = auto()


class StateTransition(Message, bubble=True):
    """Message emitted when state changes."""

    def __init__(self, from_state: GameState, to_state: GameState) -> None:
        super().__init__()
        self.from_state = from_state
        self.to_state = to_state


class StateMachine:
    """
    Game state machine with transition callbacks.
    
    State Diagram:
    ┌─────────────────────────────────────────────────────────────────┐
    │                        STATE MACHINE                            │
    │                                                                  │
    │     ┌──────────┐                                                │
    │     │   MENU   │◀───────────────────────────────────────┐      │
    │     └────┬─────┘                                        │      │
    │          │ start                                        │      │
    │          ▼                                              │      │
    │     ┌──────────┐     pause      ┌──────────┐            │      │
    │     │ PLAYING  │──────────────▶│  PAUSED  │            │      │
    │     └────┬─────┘◀──────────────└──────────┘   quit      │      │
    │          │                                        ┘      │      │
    │          │ game over                                    │      │
    │          ▼                                              │      │
    │     ┌──────────┐                                        │      │
    │     │ GAME_OVER│─────────────────────────────────────────┘      │
    │     └──────────┘         (restart)                              │
    │          │                                                    │
    │          │ high scores                                         │
    │          ▼                                                    │
    │     ┌──────────────┐                                           │
    │     │ HIGH_SCORES  │                                           │
    │     └──────────────┘                                           │
    │                                                                  │
    └─────────────────────────────────────────────────────────────────┘
    """

    # Valid state transitions
    VALID_TRANSITIONS: dict[GameState, set[GameState]] = {
        GameState.MENU: {GameState.PLAYING, GameState.HIGH_SCORES},
        GameState.PLAYING: {GameState.PAUSED, GameState.GAME_OVER},
        GameState.PAUSED: {GameState.PLAYING, GameState.MENU},
        GameState.GAME_OVER: {GameState.MENU, GameState.PLAYING, GameState.HIGH_SCORES},
        GameState.HIGH_SCORES: {GameState.MENU},
    }

    def __init__(self, initial_state: GameState = GameState.MENU) -> None:
        self._state = initial_state
        self._history: list[GameState] = []
        self._transition_callbacks: list[Callable[[GameState, GameState], None]] = []

    @property
    def state(self) -> GameState:
        """Get current state."""
        return self._state

    def can_transition(self, target: GameState) -> bool:
        """Check if transition is valid."""
        return target in self.VALID_TRANSITIONS.get(self._state, set())

    def transition(self, target: GameState) -> bool:
        """
        Attempt to transition to a new state.
        
        Returns:
            True if transition succeeded, False if invalid
        """
        if not self.can_transition(target):
            return False

        old_state = self._state
        self._history.append(old_state)
        self._state = target

        # Notify listeners
        for callback in self._transition_callbacks:
            callback(old_state, target)

        return True

    def on_transition(
        self, callback: Callable[[GameState, GameState], None]
    ) -> None:
        """Register a transition callback."""
        self._transition_callbacks.append(callback)

    def get_history(self) -> list[GameState]:
        """Get state transition history."""
        return self._history.copy()


@dataclass
class GameData:
    """
    Persistent game data that survives across sessions.
    """
    high_scores: list[tuple[str, int]] = field(default_factory=list)
    total_games_played: int = 0
    total_time_played: float = 0.0
    highest_level_reached: int = 1


@dataclass
class SessionData:
    """
    Session-specific game data (resets each game).
    """
    session_id: uuid.UUID = field(default_factory=uuid.uuid4)
    score: int = 0
    level: int = 1
    health: int = 100
    max_health: int = 100
    enemies_killed: int = 0
    accuracy: float = 0.0
    shots_fired: int = 0
    shots_hit: int = 0
    play_time: float = 0.0
    difficulty: float = 1.0


@dataclass
class GameContext:
    """
    Complete game context including all state.
    
    Architecture:
    ┌─────────────────────────────────────────────────────────────────┐
    │                    GAME CONTEXT                                 │
    │                                                                  │
    │  ┌──────────────────────────────────────────────────────────┐  │
    │  │                    StateMachine                          │  │
    │  │  (MENU → PLAYING → PAUSED/GAME_OVER → ...)              │  │
    │  └──────────────────────────────────────────────────────────┘  │
    │                                                                  │
    │  ┌─────────────────┐  ┌─────────────────┐                     │
    │  │   GameData      │  │  SessionData    │                     │
    │  │  (persistent)   │  │  (per-game)      │                     │
    │  ├─────────────────┤  ├─────────────────┤                     │
    │  │ high_scores[]   │  │ score: int      │                     │
    │  │ games_played    │  │ level: int      │                     │
    │  │ time_played     │  │ health: int     │                     │
    │  └─────────────────┘  │ ...             │                     │
    │                       └─────────────────┘                     │
    │                                                                  │
    │  ┌──────────────────────────────────────────────────────────┐  │
    │  │                   EntityManager                          │  │
    │  │  player: Entity                                         │  │
    │  │  enemies: dict[uuid, Entity]                           │  │
    │  │  asteroids: dict[uuid, Entity]                         │  │
    │  │  bullets: dict[uuid, Entity]                           │  │
    │  │  effects: dict[uuid, Entity]                           │  │
    │  └──────────────────────────────────────────────────────────┘  │
    │                                                                  │
    └─────────────────────────────────────────────────────────────────┘
    """
    state_machine: StateMachine = field(default_factory=StateMachine)
    game_data: GameData = field(default_factory=GameData)
    session: SessionData = field(default_factory=SessionData)
    
    # Entity references (set during game initialization)
    player: Optional["Entity"] = field(default=None, repr=False)
    entities: dict[uuid.UUID, "Entity"] = field(default_factory=dict)
    
    # World state
    world_width: int = 80
    world_height: int = 40
    scroll_offset: float = 0.0
    
    def reset_session(self) -> None:
        """Reset session data for a new game."""
        self.session = SessionData()
        self.entities.clear()
        self.player = None

    def add_score(self, points: int) -> None:
        """Add points to score and check level progression."""
        self.session.score += points
        self._check_level_progression()

    def _check_level_progression(self) -> None:
        """Check and update level based on score thresholds."""
        level_thresholds = [0, 500, 1500, 3000, 5000, 8000, 12000, 17000, 23000, 30000]
        
        new_level = 1
        for i, threshold in enumerate(level_thresholds):
            if self.session.score >= threshold:
                new_level = i + 1
        
        if new_level > self.session.level:
            self.session.level = new_level
            self.session.difficulty = 1.0 + (new_level - 1) * 0.15
```

---

## 10. Collision Detection

```python
# src/game/systems/collision.py

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Iterator
from collections import defaultdict

if TYPE_CHECKING:
    from ..entities.base import Entity
    from ..state import GameContext


class CollisionGrid:
    """
    Spatial partitioning grid for efficient collision detection.
    
    Uses a uniform grid to reduce collision checks from O(n²) to O(n).
    
    Grid Cell Structure:
    ┌────┬────┬────┬────┬────┐
    │    │    │    │    │    │
    ├────┼────┼────┼────┼────┤
    │    │ ●  │    │ ●  │    │  ● = Entity
    ├────┼────┼────┼────┼────┤  Each cell stores
    │    │    │    │    │    │  entities within it
    ├────┼────┼────┼────┼────┤
    │ ●  │    │    │    │ ●  │
    └────┴────┴────┴────┴────┘
    """

    def __init__(self, cell_size: int = 10) -> None:
        self._cell_size = cell_size
        self._grid: dict[tuple[int, int], set[Entity]] = defaultdict(set)

    def clear(self) -> None:
        """Clear all entities from grid."""
        self._grid.clear()

    def _get_cell(self, x: float, y: float) -> tuple[int, int]:
        """Get cell coordinates for a position."""
        return (int(x) // self._cell_size, int(y) // self._cell_size)

    def insert(self, entity: Entity) -> None:
        """Insert an entity into the grid."""
        if not entity.collision or not entity.active:
            return
        
        pos = entity.position
        cell = self._get_cell(pos.x, pos.y)
        self._grid[cell].add(entity)
        
        # Also insert into adjacent cells for edge cases
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                adj_cell = (cell[0] + dx, cell[1] + dy)
                self._grid[adj_cell].add(entity)

    def get_nearby(self, entity: Entity) -> Iterator[Entity]:
        """Get all entities in nearby cells."""
        if not entity.collision:
            return
        
        pos = entity.position
        cell = self._get_cell(pos.x, pos.y)
        
        # Check all cells that could contain colliding entities
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                adj_cell = (cell[0] + dx, cell[1] + dy)
                yield from self._grid.get(adj_cell, set())


class CollisionSystem:
    """
    Handles collision detection between entities.
    
    Collision Types:
    ┌─────────────────────────────────────────────────────────────────┐
    │                  COLLISION MATRIX                               │
    │                                                                  │
    │                 │ Player │ Enemy │ Bullet │ Asteroid │ Powerup │
    │  ───────────────┼────────┼───────┼────────┼──────────┼────────│
    │  Player         │   -    │   Y   │   -    │    Y     │   Y    │
    │  Enemy          │   Y    │   -   │   Y    │    N     │   N    │
    │  Player Bullet  │   -    │   Y   │   -    │    Y     │   -    │
    │  Enemy Bullet   │   Y    │   -   │   -    │    N     │   -    │
    │  Asteroid       │   Y    │   N   │   Y    │    N     │   N    │
    │                                                                  │
    │  Y = Collide, N = Pass through, - = Same type (no check)       │
    └─────────────────────────────────────────────────────────────────┘
    """

    # Collision mask - which entity tags collide with which
    COLLISION_RULES: dict[str, set[str]] = {
        "player": {"enemy", "asteroid", "enemy_bullet", "powerup"},
        "enemy": {"player", "bullet"},
        "bullet": {"enemy", "asteroid"},
        "asteroid": {"player", "bullet"},
        "powerup": {"player"},
    }

    def __init__(self) -> None:
        self._grid = CollisionGrid(cell_size=10)
        self._collision_pairs: list[tuple[Entity, Entity, str]] = []
        self._debug_mode = False

    def detect_collisions(self, context: GameContext) -> list[tuple[Entity, Entity]]:
        """
        Detect all collisions in the current frame.
        
        Algorithm:
        1. Clear and rebuild spatial grid
        2. For each entity, query nearby cells
        3. Check circle-circle collision
        4. Apply collision rules
        5. Return valid collision pairs
        
        Returns:
            List of (entity_a, entity_b) tuples for colliding entities
        """
        self._collision_pairs.clear()
        self._grid.clear()

        # Insert all entities into spatial grid
        for entity in context.entities.values():
            if entity.active:
                self._grid.insert(entity)
        
        if context.player and context.player.active:
            self._grid.insert(context.player)

        # Check collisions using spatial partitioning
        checked_pairs: set[tuple[str, str]] = set()
        
        for entity in list(context.entities.values()) + ([context.player] if context.player else []):
            if not entity or not entity.active:
                continue
            
            # Get entities that this entity might collide with
            for other in self._grid.get_nearby(entity):
                if other.id == entity.id or not other.active:
                    continue
                
                # Create sorted pair key to avoid duplicate checks
                pair_key = tuple(sorted([str(entity.id), str(other.id)]))
                if pair_key in checked_pairs:
                    continue
                checked_pairs.add(pair_key)

                # Check if collision is allowed
                if not self._can_collide(entity, other):
                    continue

                # Perform circle collision check
                if self._check_collision(entity, other):
                    self._collision_pairs.append((entity, other, "collision"))

        return [(a, b) for a, b, _ in self._collision_pairs]

    def _can_collide(self, entity_a: Entity, entity_b: Entity) -> bool:
        """Check if two entities are allowed to collide based on tags."""
        # Find common collision categories
        for tag_a in entity_a._tags:
            for tag_b in entity_b._tags:
                if tag_a in self.COLLISION_RULES:
                    if tag_b in self.COLLISION_RULES[tag_a]:
                        return True
                if tag_b in self.COLLISION_RULES:
                    if tag_a in self.COLLISION_RULES[tag_b]:
                        return True
        return False

    def _check_collision(self, entity_a: Entity, entity_b: Entity) -> bool:
        """
        Check if two entities are colliding using circle collision.
        
        Circle Collision Formula:
        distance(A, B) < radius(A) + radius(B)
        
        where distance(A, B) = sqrt((Ax - Bx)² + (Ay - By)²)
        """
        pos_a = entity_a.position
        pos_b = entity_b.position
        col_a = entity_a.collision
        col_b = entity_b.collision

        if not col_a or not col_b:
            return False

        # Calculate distance between centers
        dx = pos_a.x - pos_b.x
        dy = pos_a.y - pos_b.y
        distance_sq = dx * dx + dy * dy

        # Sum of radii
        radius_sum = col_a.radius + col_b.radius

        return distance_sq < radius_sum * radius_sum

    def resolve_collision(
        self, entity_a: Entity, entity_b: Entity
    ) -> list[str]:
        """
        Resolve collision between two entities.
        
        Returns list of effects to apply (e.g., "damage", "destroy", "score")
        """
        effects: list[str] = []
        
        # Get damage components
        dmg_a = entity_a.get_component(DamageComponent)
        dmg_b = entity_b.get_component(DamageComponent)

        # Apply damage (simplified - both take each other's damage)
        if entity_a.health and dmg_b:
            entity_a.health.current -= dmg_b.amount
            effects.append(f"damage_{entity_a.type.name}")
            
            if entity_a.health.current <= 0:
                effects.append(f"destroy_{entity_a.type.name}")

        if entity_b.health and dmg_a:
            entity_b.health.current -= dmg_a.amount
            effects.append(f"damage_{entity_b.type.name}")
            
            if entity_b.health.current <= 0:
                effects.append(f"destroy_{entity_b.type.name}")

        # Award score for destroying enemies/asteroids
        score_a = entity_a.get_component(ScoreComponent)
        score_b = entity_b.get_component(ScoreComponent)

        if entity_b.health and entity_b.health.current <= 0 and score_b:
            effects.append(f"score_{score_b.points}")
        
        if entity_a.health and entity_a.health.current <= 0 and score_a:
            effects.append(f"score_{score_a.points}")

        return effects

    def enable_debug(self) -> None:
        """Enable collision debug mode."""
        self._debug_mode = True

    def disable_debug(self) -> None:
        """Disable collision debug mode."""
        self._debug_mode = False


from ..entities.base import Entity, DamageComponent
```

---

## 11. Entity Systems

### Movement System

```python
# src/game/systems/movement.py

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..state import GameContext
    from ..entities.base import Entity


class MovementSystem:
    """
    Handles entity movement and physics.
    
    Features:
    - Configurable velocity and acceleration
    - World boundary clamping
    - Screen wrapping (optional)
    - Smooth interpolation
    """

    def __init__(
        self,
        world_width: int,
        world_height: int,
        wrap_horizontal: bool = False,
        wrap_vertical: bool = True,
    ) -> None:
        self._world_width = world_width
        self._world_height = world_height
        self._wrap_horizontal = wrap_horizontal
        self._wrap_vertical = wrap_vertical

    def update(self, context: GameContext, dt: float) -> None:
        """Update positions of all entities."""
        all_entities = list(context.entities.values())
        if context.player and context.player.active:
            all_entities.append(context.player)

        for entity in all_entities:
            self._update_entity(entity, dt)

    def _update_entity(self, entity: Entity, dt: float) -> None:
        """Update a single entity's position."""
        if not entity.has_component(VelocityComponent):
            return

        vel = entity.velocity
        pos = entity.position

        # Apply velocity
        new_x = pos.x + vel.vx * dt
        new_y = pos.y + vel.vy * dt

        # Handle boundaries
        if self._wrap_horizontal:
            new_x = new_x % self._world_width
        else:
            new_x = max(0, min(self._world_width - 1, new_x))

        if self._wrap_vertical:
            new_y = new_y % self._world_height
        else:
            new_y = max(0, min(self._world_height - 1, new_y))

        pos.x = new_x
        pos.y = new_y

    def apply_acceleration(
        self, entity: Entity, ax: float, ay: float, dt: float
    ) -> None:
        """Apply acceleration to an entity."""
        if not entity.has_component(VelocityComponent):
            return
        entity.velocity.vx += ax * dt
        entity.velocity.vy += ay * dt

    def set_velocity(self, entity: Entity, vx: float, vy: float) -> None:
        """Set absolute velocity for an entity."""
        if not entity.has_component(VelocityComponent):
            return
        entity.velocity.vx = vx
        entity.velocity.vy = vy

    def stop_entity(self, entity: Entity) -> None:
        """Stop an entity completely."""
        if entity.has_component(VelocityComponent):
            entity.velocity.vx = 0
            entity.velocity.vy = 0
```

### Spawner System

```python
# src/game/systems/spawner.py

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Callable
from dataclasses import dataclass

if TYPE_CHECKING:
    from ..state import GameContext
    from ..entities.base import Entity


@dataclass
class SpawnConfig:
    """Configuration for entity spawning."""
    min_distance_from_player: float = 20.0
    spawn_margin: float = 5.0
    max_attempts: int = 10


class SpawnerSystem:
    """
    Handles entity spawning with procedural generation.
    
    Spawn Zones:
    ┌─────────────────────────────────────────────────────────────────┐
    │                    SPAWN BOUNDARIES                            │
    │                                                                  │
    │   ┌────────────────────────────────────────────────────────┐   │
    │   │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │   │
    │   │ ░░░░░░░░░░ SPAWN ZONE (top 20%) ░░░░░░░░░░░░░░░░░░░░░░░ │   │
    │   │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │   │
    │   │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │   │
    │   │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │   │
    │   │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │   │
    │   │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │   │
    │   │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │   │
    │   │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │   │
    │   │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│   │
    │   │░░░░ PLAYER ZONE (bottom 30%) ░░░░░░░░░░░░░░░░░░░░░░░░░░│   │
    │   │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│   │
    │   └────────────────────────────────────────────────────────┘   │
    │                                                                  │
    │   Side spawns: enemies occasionally spawn from left/right        │
    │                                                                  │
    └─────────────────────────────────────────────────────────────────┘
    """

    def __init__(
        self,
        config: SpawnConfig,
        world_width: int,
        world_height: int,
    ) -> None:
        self._config = config
        self._world_width = world_width
        self._world_height = world_height
        
        # Spawn timers
        self._asteroid_timer: float = 0.0
        self._enemy_timer: float = 0.0
        
        # Callbacks for entity creation
        self._factories: dict[str, Callable[..., Entity]] = {}

    def register_factory(self, name: str, factory: Callable[..., Entity]) -> None:
        """Register an entity factory."""
        self._factories[name] = factory

    def update(self, context: GameContext, dt: float) -> None:
        """Update spawn timers and spawn entities."""
        difficulty = context.session.difficulty
        
        # Update timers
        self._asteroid_timer += dt
        self._enemy_timer += dt

        # Asteroid spawning (increases with difficulty)
        asteroid_interval = 2.0 / difficulty
        if self._asteroid_timer >= asteroid_interval:
            self._spawn_asteroid(context)
            self._asteroid_timer = 0.0

        # Enemy spawning (increases with difficulty)
        enemy_interval = 4.0 / difficulty
        if self._enemy_timer >= enemy_interval:
            self._spawn_enemy(context)
            self._enemy_timer = 0.0

        # Boss spawning (every 5 levels)
        if context.session.level % 5 == 0 and context.session.level > 0:
            if not self._has_boss(context):
                self._spawn_boss(context)

    def _spawn_asteroid(self, context: GameContext) -> None:
        """Spawn an asteroid at a random position."""
        # Choose random size with weighted probability
        sizes = ["large", "medium", "small"]
        weights = [0.2, 0.4, 0.4]
        size = random.choices(sizes, weights)[0]

        # Find valid spawn position
        x, y = self._find_spawn_position(context, margin_top=5)

        # Create asteroid
        asteroid = self._factories["asteroid"](size=size, x=x, y=y)
        
        # Set velocity based on difficulty
        asteroid.velocity.vy = random.uniform(2.0, 4.0) * context.session.difficulty
        asteroid.velocity.vx = random.uniform(-1.0, 1.0)
        
        # Add to context
        context.entities[asteroid.id] = asteroid

    def _spawn_enemy(self, context: GameContext) -> None:
        """Spawn an enemy based on current level."""
        # Determine enemy type
        level = context.session.level
        if level < 3:
            enemy_type = "basic"
        elif level < 7:
            enemy_type = random.choice(["basic", "advanced"])
        else:
            enemy_type = random.choice(["basic", "advanced", "advanced"])

        # Find spawn position (from sides or top)
        spawn_type = random.choice(["top", "left", "right"])
        if spawn_type == "top":
            x = random.uniform(5, self._world_width - 5)
            y = -5
        elif spawn_type == "left":
            x = -5
            y = random.uniform(5, self._world_height // 2)
        else:
            x = self._world_width + 5
            y = random.uniform(5, self._world_height // 2)

        # Create enemy
        enemy = self._factories["enemy"](enemy_type=enemy_type, x=x, y=y)
        
        # Add to context
        context.entities[enemy.id] = enemy

    def _spawn_boss(self, context: GameContext) -> None:
        """Spawn a boss enemy."""
        x = self._world_width // 2
        y = -10
        
        boss = self._factories["enemy"](enemy_type="boss", x=x, y=y)
        context.entities[boss.id] = boss

    def _find_spawn_position(
        self, context: GameContext, margin_top: float = 0
    ) -> tuple[float, float]:
        """Find a valid spawn position away from player."""
        player = context.player
        
        for _ in range(self._config.max_attempts):
            x = random.uniform(
                self._config.spawn_margin,
                self._world_width - self._config.spawn_margin
            )
            y = random.uniform(
                margin_top,
                self._world_height // 3
            )

            # Check distance from player
            if player and player.active:
                dx = x - player.position.x
                dy = y - player.position.y
                distance = (dx * dx + dy * dy) ** 0.5
                
                if distance >= self._config.min_distance_from_player:
                    return (x, y)

        # Fallback to random position
        return (
            random.uniform(5, self._world_width - 5),
            random.uniform(margin_top, self._world_height // 3)
        )

    def _has_boss(self, context: GameContext) -> bool:
        """Check if there's already a boss in the game."""
        for entity in context.entities.values():
            if entity.type.name == "ENEMY_BOSS" and entity.active:
                return True
        return False

    def reset_timers(self) -> None:
        """Reset all spawn timers."""
        self._asteroid_timer = 0.0
        self._enemy_timer = 0.0
```

---

## 12. Game Mechanics

### Difficulty Progression

```python
# src/game/systems/difficulty.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class DifficultyParams:
    """Parameters affected by difficulty scaling."""
    enemy_speed_multiplier: float = 1.0
    enemy_health_multiplier: float = 1.0
    enemy_spawn_rate_multiplier: float = 1.0
    asteroid_density_multiplier: float = 1.0
    asteroid_speed_multiplier: float = 1.0
    score_multiplier: float = 1.0
    special_enemy_chance: float = 0.0


class DifficultySystem:
    """
    Manages difficulty progression based on level and performance.
    
    Progression Curve:
    ┌─────────────────────────────────────────────────────────────────┐
    │                      DIFFICULTY CURVE                           │
    │                                                                  │
    │  Difficulty                                                     │
    │      │                                                          │
    │  3.0 │                    ╭────────                             │
    │      │               ╭────╯                                    │
    │  2.0 │          ╭────╯                                         │
    │      │     ╭────╯                                             │
    │  1.0 │─────╯                                                   │
    │      └──────────────────────────────────────────────▶          │
    │        1    2    3    4    5    6    7    8    9   10  Level  │
    │                                                                  │
    │  Formula: difficulty = 1.0 + (level - 1) * 0.15                │
    │                                                                  │
    └─────────────────────────────────────────────────────────────────┘
    """

    # Level thresholds for special events
    BOSS_LEVELS = {5, 10, 15, 20}
    HARDMODE_LEVEL = 15

    # Difficulty parameters at each level
    LEVEL_PARAMS: dict[int, DifficultyParams] = {
        1: DifficultyParams(),
        2: DifficultyParams(
            enemy_speed_multiplier=1.1,
            enemy_health_multiplier=1.0,
        ),
        3: DifficultyParams(
            enemy_speed_multiplier=1.15,
            enemy_health_multiplier=1.1,
            special_enemy_chance=0.1,
        ),
        4: DifficultyParams(
            enemy_speed_multiplier=1.2,
            enemy_health_multiplier=1.2,
            special_enemy_chance=0.15,
        ),
        5: DifficultyParams(
            enemy_speed_multiplier=1.25,
            enemy_health_multiplier=1.3,
            special_enemy_chance=0.2,
            asteroid_density_multiplier=1.5,
        ),
    }

    def __init__(self) -> None:
        self._current_params = DifficultyParams()

    def get_params_for_level(self, level: int) -> DifficultyParams:
        """Get interpolated difficulty parameters for a level."""
        # Use base parameters with level-based scaling
        base = DifficultyParams()
        
        # Linear interpolation based on level
        level_factor = min(level, 20) / 10.0  # Normalize to 0-2 range
        
        return DifficultyParams(
            enemy_speed_multiplier=base.enemy_speed_multiplier * (1.0 + 0.1 * level_factor),
            enemy_health_multiplier=base.enemy_health_multiplier * (1.0 + 0.15 * level_factor),
            enemy_spawn_rate_multiplier=base.enemy_spawn_rate_multiplier * (1.0 + 0.2 * level_factor),
            asteroid_density_multiplier=base.asteroid_density_multiplier * (1.0 + 0.1 * level_factor),
            asteroid_speed_multiplier=base.asteroid_speed_multiplier * (1.0 + 0.1 * level_factor),
            score_multiplier=base.score_multiplier * (1.0 + 0.05 * level_factor),
            special_enemy_chance=min(0.3, 0.05 * level_factor),
        )

    def update(self, level: int) -> DifficultyParams:
        """Update current difficulty parameters."""
        self._current_params = self.get_params_for_level(level)
        return self._current_params

    def is_boss_level(self, level: int) -> bool:
        """Check if current level should have a boss."""
        return level in self.BOSS_LEVELS

    def is_hardmode(self, level: int) -> bool:
        """Check if hardmode is active."""
        return level >= self.HARDMODE_LEVEL

    @property
    def current(self) -> DifficultyParams:
        """Get current difficulty parameters."""
        return self._current_params


class ScoringSystem:
    """
    Handles score calculation and tracking.
    
    Score Sources:
    ┌─────────────────────────────────────────────────────────────────┐
    │                    SCORE VALUES                                 │
    │                                                                  │
    │  Asteroid (small)      10 pts                                    │
    │  Asteroid (medium)     25 pts                                    │
    │  Asteroid (large)      50 pts                                    │
    │  Enemy (basic)         20 pts                                    │
    │  Enemy (advanced)      50 pts                                    │
    │  Boss                  500 pts                                   │
    │  Level completion      100 × level                               │
    │  Survival bonus        1 pt / second                             │
    │                                                                  │
    │  Multipliers:                                                 │
    │  - Consecutive kills: +0.1x per kill (max 2.0x)                 │
    │  - No damage level: +0.5x bonus                                 │
    │  - Hardmode: +1.0x multiplier                                   │
    │                                                                  │
    └─────────────────────────────────────────────────────────────────┘
    """

    COMBO_TIMEOUT = 3.0  # Seconds before combo resets
    COMBO_INCREMENT = 0.1  # Multiplier increase per kill
    MAX_COMBO = 2.0  # Maximum multiplier

    def __init__(self, difficulty: DifficultySystem) -> None:
        self._difficulty = difficulty
        self._combo: float = 1.0
        self._combo_timer: float = 0.0
        self._kills_since_damage: int = 0

    def add_kill(self, base_score: int) -> int:
        """Add a kill and return the calculated score with multipliers."""
        # Update combo
        self._combo = min(self.MAX_COMBO, self._combo + self.COMBO_INCREMENT)
        self._combo_timer = self.COMBO_TIMEOUT
        self._kills_since_damage += 1

        # Calculate final score
        difficulty_mult = self._difficulty.current.score_multiplier
        final_score = int(base_score * self._combo * difficulty_mult)
        
        return final_score

    def add_survival_points(self, seconds: float, level: int) -> int:
        """Add points for surviving."""
        return int(seconds * level * 0.5)

    def take_damage(self) -> None:
        """Reset combo when player takes damage."""
        self._combo = 1.0
        self._kills_since_damage = 0

    def update(self, dt: float) -> None:
        """Update combo timer."""
        if self._combo_timer > 0:
            self._combo_timer -= dt
            if self._combo_timer <= 0:
                self._combo = 1.0

    @property
    def combo_multiplier(self) -> float:
        """Get current combo multiplier."""
        return self._combo

    @property
    def is_no_damage_bonus_active(self) -> bool:
        """Check if no-damage bonus is active (50+ kills without damage)."""
        return self._kills_since_damage >= 50
```

---

## 13. UI Screens

### Main Menu Screen

```python
# src/ui/menu_screen.py

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Button, Static
from textual.containers import Container, VerticalScroll
from textual.events import Click
from textual.message import Message


class MenuScreen(Container):
    """
    Main menu screen with ASCII art title and navigation.
    
    Layout:
    ┌─────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │                    ╔═══════════════════════╗                    │
    │                    ║  ASTEROID RUNNER     ║                    │
    │                    ║     ══════════       ║                    │
    │                    ║  ~ Space Shooter ~   ║                    │
    │                    ╚═══════════════════════╝                    │
    │                                                                  │
    │                         ▲                                       │
    │                        /|\                                      │
    │                       / | \                                     │
    │                                                                  │
    │                      ╔═══════╗                                  │
    │                      ║ START ║                                  │
    │                      ╚═══════╝                                  │
    │                      ╔═══════╗                                  │
    │                      ║ SCORES║                                  │
    │                      ╚═══════╝                                  │
    │                      ╔═══════╗                                  │
    │                      ║ QUIT  ║                                  │
    │                      ╚═══════╝                                  │
    │                                                                  │
    │              [WASD/Arrows] Navigate  [Enter] Select             │
    │                                                                  │
    └─────────────────────────────────────────────────────────────────┘
    """

    class StartGame(Message):
        """Request to start a new game."""
        pass

    class ShowHighScores(Message):
        """Request to show high scores."""
        pass

    class QuitGame(Message):
        """Request to quit the application."""
        pass

    BINDINGS = [
        Binding("w", "menu_up", "Move up", show=False),
        Binding("s", "menu_down", "Move down", show=False),
        Binding("up", "menu_up", "Move up", show=False),
        Binding("down", "menu_down", "Move down", show=False),
        Binding("enter", "menu_select", "Select", show=False),
        Binding("escape", "app.bell", "Cancel", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._selected_index = 0
        self._menu_items = ["START GAME", "HIGH SCORES", "QUIT"]

    def compose(self) -> ComposeResult:
        """Compose the menu UI."""
        yield Static(
            """
╔════════════════════════════════════╗
║      ╔═══╗ ╔═══╗ ╔═══╗            ║
║      ║ A ║═║ S ║═║ T ║            ║
║      ╚═══╝ ╚═══╝ ╚═══╝            ║
║   ╔═══════════════════════════╗    ║
║   ║   ASTEROID RUNNER         ║    ║
║   ╚═══════════════════════════╝    ║
║       ~ Space Shooter ~            ║
╚════════════════════════════════════╝
            """,
            id="title-art",
            classes="title",
        )

        yield Static(
            """
    ▲
   /|\\
  / | \\
            """,
            id="ship-art",
            classes="ship",
        )

        with VerticalScroll(id="menu-container"):
            for i, item in enumerate(self._menu_items):
                yield Button(
                    item,
                    id=f"menu-{i}",
                    classes="menu-item" if i != self._selected_index else "menu-item selected",
                )

        yield Static(
            "[WASD/Arrows] Navigate  •  [Enter] Select  •  [Esc] Quit",
            id="controls-hint",
            classes="hint",
        )

    def on_mount(self) -> None:
        """Initialize menu state."""
        self._update_selection()

    def watch__selected_index(self) -> None:
        """Update visual selection."""
        self._update_selection()

    def _update_selection(self) -> None:
        """Update the visual state of menu items."""
        for i, item in enumerate(self._menu_items):
            button = self.query_one(f"#menu-{i}", Button)
            if i == self._selected_index:
                button.set_class(True, "selected")
            else:
                button.set_class(False, "selected")

    def action_menu_up(self) -> None:
        """Move selection up."""
        self._selected_index = (self._selected_index - 1) % len(self._menu_items)

    def action_menu_down(self) -> None:
        """Move selection down."""
        self._selected_index = (self._selected_index + 1) % len(self._menu_items)

    def action_menu_select(self) -> None:
        """Activate selected menu item."""
        self.post_message(self._get_selected_action())

    def _get_selected_action(self) -> Message:
        """Get the message for the currently selected item."""
        actions = {
            0: self.StartGame,
            1: self.ShowHighScores,
            2: self.QuitGame,
        }
        return actions[self._selected_index]()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button click."""
        button_id = event.button.id
        if button_id and button_id.startswith("menu-"):
            self._selected_index = int(button_id.split("-")[1])
            self.action_menu_select()
```

### Pause Screen

```python
# src/ui/pause_screen.py

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Button, Static
from textual.containers import Container
from textual.message import Message


class PauseScreen(Container):
    """
    Pause overlay screen.
    
    Layout:
    ┌─────────────────────────────────────────────────────────────────┐
    │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
    │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
    │░░░░░░░░░░░░░░░░░░░░░░░░░░░░┌─────────────┐░░░░░░░░░░░░░░░░░░░│
    │░░░░░░░░░░░░░░░░░░░░░░░░░░░░│   PAUSED    │░░░░░░░░░░░░░░░░░░░│
    │░░░░░░░░░░░░░░░░░░░░░░░░░░░░├─────────────┤░░░░░░░░░░░░░░░░░░░│
    │░░░░░░░░░░░░░░░░░░░░░░░░░░░░│  [Resume]   │░░░░░░░░░░░░░░░░░░░│
    │░░░░░░░░░░░░░░░░░░░░░░░░░░░░│  [Restart]  │░░░░░░░░░░░░░░░░░░░│
    │░░░░░░░░░░░░░░░░░░░░░░░░░░░░│  [Quit]     │░░░░░░░░░░░░░░░░░░░│
    │░░░░░░░░░░░░░░░░░░░░░░░░░░░░└─────────────┘░░░░░░░░░░░░░░░░░░│
    │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
    └─────────────────────────────────────────────────────────────────┘
    """

    class Resume(Message):
        """Request to resume game."""
        pass

    class Restart(Message):
        """Request to restart game."""
        pass

    class Quit(Message):
        """Request to quit to menu."""
        pass

    BINDINGS = [
        Binding("escape", "resume", "Resume", show=False),
        Binding("r", "restart", "Restart", show=False),
        Binding("q", "quit", "Quit", show=False),
    ]

    def compose(self) -> ComposeResult:
        """Compose the pause UI."""
        with Container(id="pause-content"):
            yield Static("╔═══════════════╗", id="pause-header")
            yield Static("║    PAUSED     ║", id="pause-title")
            yield Static("╚═══════════════╝", id="pause-footer")
            yield Button("Resume", id="btn-resume")
            yield Button("Restart", id="btn-restart")
            yield Button("Quit to Menu", id="btn-quit")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        match event.button.id:
            case "btn-resume":
                self.post_message(self.Resume())
            case "btn-restart":
                self.post_message(self.Restart())
            case "btn-quit":
                self.post_message(self.Quit())

    def action_resume(self) -> None:
        """Resume game."""
        self.post_message(self.Resume())

    def action_restart(self) -> None:
        """Restart game."""
        self.post_message(self.Restart())

    def action_quit(self) -> None:
        """Quit to menu."""
        self.post_message(self.Quit())
```

### Game Over Screen

```python
# src/ui/game_over_screen.py

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Button, Static
from textual.containers import Container
from textual.message import Message


class GameOverScreen(Container):
    """
    Game over screen with score display and high score notification.
    
    Layout:
    ┌─────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │                                                                  │
    │                    ╔═══════════════════╗                      │
    │                    ║    GAME OVER       ║                      │
    │                    ╚═══════════════════╝                      │
    │                                                                  │
    │                    ╔═══════════════════╗                      │
    │                    ║                   ║                      │
    │                    ║   SCORE: 12450    ║                      │
    │                    ║   LEVEL: 07       ║                      │
    │                    ║   KILLS: 42       ║                      │
    │                    ║                   ║                      │
    │                    ╚═══════════════════╝                      │
    │                                                                  │
    │              ★★★ NEW HIGH SCORE! ★★★                          │
    │                                                                  │
    │                      ╔═══════════╗                             │
    │                      ║ PLAY AGAIN║                             │
    │                      ╚═══════════╝                             │
    │                      ╔═══════════╗                             │
    │                      ║ MAIN MENU ║                             │
    │                      ╚═══════════╝                             │
    │                                                                  │
    └─────────────────────────────────────────────────────────────────┘
    """

    class PlayAgain(Message):
        """Request to play again."""
        pass

    class MainMenu(Message):
        """Request to return to main menu."""
        pass

    BINDINGS = [
        Binding("enter", "play_again", "Play Again", show=False),
        Binding("escape", "main_menu", "Main Menu", show=False),
    ]

    def __init__(
        self,
        score: int = 0,
        level: int = 1,
        kills: int = 0,
        is_high_score: bool = False,
    ) -> None:
        super().__init__()
        self._score = score
        self._level = level
        self._kills = kills
        self._is_high_score = is_high_score

    def compose(self) -> ComposeResult:
        """Compose the game over UI."""
        with Container(id="gameover-container"):
            yield Static(
                """
╔═══════════════════════╗
║      GAME OVER        ║
╚═══════════════════════╝
                """,
                id="gameover-title",
            )

            yield Static(
                f"""
╔═══════════════════════╗
║                       ║
║    SCORE: {self._score:05d}     ║
║    LEVEL: {self._level:02d}        ║
║    KILLS: {self._kills:03d}        ║
║                       ║
╚═══════════════════════╝
                """,
                id="gameover-stats",
            )

            if self._is_high_score:
                yield Static(
                    "★ ★ ★ NEW HIGH SCORE! ★ ★ ★",
                    id="high-score-banner",
                    classes="highlight",
                )

            yield Button("PLAY AGAIN", id="btn-play-again")
            yield Button("MAIN MENU", id="btn-main-menu")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        match event.button.id:
            case "btn-play-again":
                self.post_message(self.PlayAgain())
            case "btn-main-menu":
                self.post_message(self.MainMenu())

    def action_play_again(self) -> None:
        """Play again."""
        self.post_message(self.PlayAgain())

    def action_main_menu(self) -> None:
        """Return to main menu."""
        self.post_message(self.MainMenu())
```

---

## 14. Error Handling & Edge Cases

### Error Handling Strategy

```python
# src/utils/error_handling.py

from __future__ import annotations

import logging
import traceback
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Optional, TypeVar, Generic, Iterator
from enum import Enum, auto

import textual.logging

logger = textual.logging.get_logger()


class ErrorSeverity(Enum):
    """Severity levels for errors."""
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


@dataclass
class GameError:
    """Structured error information."""
    message: str
    severity: ErrorSeverity
    context: dict = field(default_factory=dict)
    exc_info: Optional[tuple] = None

    def log(self) -> None:
        """Log the error with appropriate level."""
        msg = f"[{self.severity.name}] {self.message}"
        if self.context:
            msg += f" | Context: {self.context}"
        
        match self.severity:
            case ErrorSeverity.DEBUG:
                logger.debug(msg)
            case ErrorSeverity.INFO:
                logger.info(msg)
            case ErrorSeverity.WARNING:
                logger.warning(msg)
            case ErrorSeverity.ERROR:
                logger.error(msg)
            case ErrorSeverity.CRITICAL:
                logger.critical(msg)


class ErrorHandler:
    """
    Centralized error handling for the game.
    
    Handles:
    - Game logic errors (entity not found, invalid state)
    - I/O errors (file operations, persistence)
    - Rendering errors (terminal resize, Unicode issues)
    - Input errors (unknown keys, device errors)
    """

    def __init__(self) -> None:
        self._error_log: list[GameError] = []
        self._max_log_size = 100

    @contextmanager
    def handle(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        reraise: bool = True,
        **context: object,
    ) -> Iterator[None]:
        """
        Context manager for error handling.
        
        Usage:
            with error_handler.handle("Entity creation failed"):
                entity = create_entity()
        """
        error: Optional[GameError] = None
        
        try:
            yield
        except Exception as e:
            error = GameError(
                message=message,
                severity=severity,
                context=context,
                exc_info=(type(e), e, e.__traceback__),
            )
            error.log()
            self._log_error(error)
            
            if reraise:
                raise
        
        if not error:
            # Log successful operation at debug level
            debug_error = GameError(
                message=f"Success: {message}",
                severity=ErrorSeverity.DEBUG,
                context=context,
            )
            self._log_error(debug_error)

    def _log_error(self, error: GameError) -> None:
        """Add error to log."""
        self._error_log.append(error)
        if len(self._error_log) > self._max_log_size:
            self._error_log.pop(0)

    def get_recent_errors(self, count: int = 10) -> list[GameError]:
        """Get recent errors."""
        return self._error_log[-count:]

    def has_critical_errors(self) -> bool:
        """Check if any critical errors occurred."""
        return any(e.severity == ErrorSeverity.CRITICAL for e in self._error_log)


# Global error handler instance
_global_handler = ErrorHandler()


@contextmanager
def handle_error(
    message: str,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    reraise: bool = True,
    **context: object,
) -> Iterator[None]:
    """Global error handling context manager."""
    with _global_handler.handle(message, severity, reraise, **context):
        yield
```

### Edge Case Handling

```python
# Edge Cases and Their Solutions

EDGE_CASES = {
    # Terminal Resize
    "terminal_resize": {
        "problem": "Terminal size changes while game is running",
        "solution": """
            1. Listen to Textual's resize events
            2. Pause game during resize
            3. Recalculate all positions relative to new size
            4. Clamp entities to new boundaries
            5. Resume with updated dimensions
        """,
        "code": """
            def on_resize(self, event: Resize) -> None:
                self._pause()
                self._update_dimensions(event.width, event.height)
                self._clamp_entities()
                self._resume()
        """
    },

    # Rapid Input
    "rapid_input": {
        "problem": "Player mashing keys faster than game can process",
        "solution": """
            1. Use input buffering with fixed capacity
            2. Cooldown system for continuous actions (shooting)
            3. Debounce for menu navigation
            4. Drop excess inputs rather than queue them
        """,
        "code": """
            if self._shoot_cooldown <= 0:
                self._fire_bullet()
                self._shoot_cooldown = SHOOT_DELAY
        """
    },

    # Entity Cleanup
    "entity_cleanup": {
        "problem": "Dead entities causing memory leaks or collision issues",
        "solution": """
            1. Mark entities as inactive, don't delete immediately
            2. Batch cleanup at end of frame
            3. Remove from spatial grid before deletion
            4. Clear entity references in other systems
        """,
        "code": """
            # During update
            for entity in entities_to_remove:
                entity.active = False
                self._grid.remove(entity.id)
            
            # Batch delete at end of frame
            self._entities = {k: v for k, v in self._entities.items() if v.active}
        """
    },

    # Bullet Cleanup
    "bullet_cleanup": {
        "problem": "Bullets going off-screen and never being removed",
        "solution": """
            1. Check bullet bounds each frame
            2. Remove bullets outside world + margin
            3. Use object pooling to reduce GC pressure
        """,
        "code": """
            MARGIN = 5
            if (bullet.x < -MARGIN or bullet.x > width + MARGIN or
                bullet.y < -MARGIN or bullet.y > height + MARGIN):
                bullet.active = False
        """
    },

    # High Score Corruption
    "high_score_corruption": {
        "problem": "High scores file becomes corrupted or unreadable",
        "solution": """
            1. Write to temp file first, then rename (atomic write)
            2. Validate JSON structure on load
            3. Fall back to empty scores if validation fails
            4. Log corruption for debugging
        """,
        "code": """
            def save_high_scores(self, scores: list) -> None:
                temp_path = self._path.with_suffix('.tmp')
                self._path.write_text(json.dumps(scores, indent=2))
                temp_path.rename(self._path)  # Atomic on POSIX
        """
    },

    # Division by Zero
    "division_by_zero": {
        "problem": "Math operations with zero values (health, ammo, etc.)",
        "solution": """
            1. Guard divisions with zero checks
            2. Use max(1, value) for denominators
            3. Clamp values to valid ranges
        """,
        "code": """
            ratio = current / max(1, max_value)  # Safe division
            health_ratio = max(0.0, min(1.0, health / max_health))
        """
    },

    # Off-by-One Errors
    "off_by_one": {
        "problem": "Entities spawning partially off-screen",
        "solution": """
            1. Use half-width/height for boundary calculations
            2. Clamp positions explicitly
            3. Add margin to spawn boundaries
        """,
        "code": """
            x = max(entity_width/2, min(width - entity_width/2, x))
            y = max(entity_height/2, min(height - entity_height/2, y))
        """
    },
}
```

---

## 15. Performance Optimization

### Optimization Strategies

```python
# Performance Optimization Techniques

OPTIMIZATIONS = {
    # 1. Object Pooling
    "object_pooling": {
        "description": "Reuse entity objects instead of creating/destroying",
        "implementation": """
            class EntityPool:
                def __init__(self, factory, max_size=100):
                    self._pool = [factory() for _ in range(max_size)]
                    self._active = set()
                
                def acquire(self) -> Entity:
                    if self._pool:
                        entity = self._pool.pop()
                    else:
                        entity = self._factory()
                    self._active.add(entity)
                    return entity
                
                def release(self, entity: Entity):
                    entity.reset()  # Reset to default state
                    self._active.remove(entity)
                    self._pool.append(entity)
        """
    },

    # 2. Dirty Flag Rendering
    "dirty_rendering": {
        "description": "Only re-render changed portions of the screen",
        "implementation": """
            class DirtyRect:
                def __init__(self, x, y, w, h):
                    self.x, self.y, self.w, self.h = x, y, w, h
                
                def intersects(self, other):
                    return not (self.x + self.w < other.x or
                               other.x + other.w < self.x or
                               self.y + self.h < other.y or
                               other.y + other.h < self.y)
            
            # Only redraw dirty regions
            if self._dirty_rect.intersects(entity.bounds):
                self._render_entity(entity)
        """
    },

    # 3. Batch Processing
    "batch_processing": {
        "description": "Process entities in batches for cache efficiency",
        "implementation": """
            # Instead of processing entities one by one
            entities = [e for e in self._entities if e.active]
            
            # Batch update positions
            positions = [e.position for e in entities]
            velocities = [e.velocity for e in entities]
            
            for i in range(len(entities)):
                positions[i].x += velocities[i].vx * dt
                positions[i].y += velocities[i].vy * dt
        """
    },

    # 4. Spatial Partitioning
    "spatial_partitioning": {
        "description": "Grid-based collision detection for O(n) vs O(n²)",
        "implementation": """
            # Already implemented in CollisionGrid class
            # Only check entities in nearby cells
            for entity in self._grid.get_nearby(target):
                if self._check_collision(entity, target):
                    collisions.append((entity, target))
        """
    },

    # 5. Frame Skip
    "frame_skip": {
        "description": "Skip rendering if behind on updates",
        "implementation": """
            # In game loop
            if self._update_count > MAX_FRAME_SKIP:
                self._skip_render = True
                logger.warning(f"Skipping render: {self._update_count} updates")
            
            if not self._skip_render:
                self._render()
        """
    },
}
```

---

## 16. Testing Strategy

```python
# tests/test_entities.py

import pytest
from src.game.entities.base import (
    Entity, EntityType, EntityFactory,
    PositionComponent, VelocityComponent, HealthComponent,
    CollisionComponent, RenderComponent
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
        
        # Larger asteroids should have larger collision radius
        assert large.collision.radius > medium.collision.radius
        assert medium.collision.radius > small.collision.radius


class TestCollisionDetection:
    """Tests for collision detection."""

    def test_circle_collision(self):
        """Test basic circle-circle collision."""
        from src.game.systems.collision import CollisionSystem
        from src.game.state import GameContext
        
        collision = CollisionSystem()
        
        # Create two entities
        entity_a = EntityFactory.create_player()
        entity_b = EntityFactory.create_asteroid("medium", x=entity_a.position.x + 1, y=entity_a.position.y)
        
        # They should collide (distance < sum of radii)
        # Player radius = 2.0, medium asteroid radius = 3.0
        assert collision._check_collision(entity_a, entity_b)

    def test_no_collision(self):
        """Test entities not colliding."""
        from src.game.systems.collision import CollisionSystem
        
        collision = CollisionSystem()
        
        entity_a = EntityFactory.create_player()
        entity_b = EntityFactory.create_asteroid("small", x=100, y=100)  # Far away
        
        assert not collision._check_collision(entity_a, entity_b)

    def test_can_collide_rules(self):
        """Test collision rules."""
        from src.game.systems.collision import CollisionSystem
        
        collision = CollisionSystem()
        
        player = EntityFactory.create_player()
        asteroid = EntityFactory.create_asteroid("medium")
        
        assert collision._can_collide(player, asteroid)  # player-asteroid = Y
        
        enemy = EntityFactory.create_enemy("basic")
        assert collision._can_collide(player, enemy)  # player-enemy = Y


class TestDifficultySystem:
    """Tests for difficulty progression."""

    def test_base_difficulty(self):
        """Test level 1 has base difficulty."""
        from src.game.systems.difficulty import DifficultySystem
        
        diff = DifficultySystem()
        params = diff.get_params_for_level(1)
        
        assert params.enemy_speed_multiplier == pytest.approx(1.0, rel=0.1)
        assert params.score_multiplier == pytest.approx(1.0, rel=0.1)

    def test_difficulty_scaling(self):
        """Test difficulty increases with level."""
        from src.game.systems.difficulty import DifficultySystem
        
        diff = DifficultySystem()
        params_1 = diff.get_params_for_level(1)
        params_10 = diff.get_params_for_level(10)
        
        assert params_10.enemy_speed_multiplier > params_1.enemy_speed_multiplier
        assert params_10.enemy_health_multiplier > params_1.enemy_health_multiplier

    def test_boss_level(self):
        """Test boss level detection."""
        from src.game.systems.difficulty import DifficultySystem
        
        diff = DifficultySystem()
        
        assert diff.is_boss_level(5)
        assert diff.is_boss_level(10)
        assert not diff.is_boss_level(3)
        assert not diff.is_boss_level(7)


class TestScoringSystem:
    """Tests for scoring."""

    def test_base_score(self):
        """Test basic score calculation."""
        from src.game.systems.difficulty import DifficultySystem, ScoringSystem
        
        diff = DifficultySystem()
        scoring = ScoringSystem(diff)
        
        score = scoring.add_kill(10)  # Small asteroid
        assert score == 10  # 1.0x multiplier

    def test_combo_multiplier(self):
        """Test combo multiplier increases score."""
        from src.game.systems.difficulty import DifficultySystem, ScoringSystem
        
        diff = DifficultySystem()
        scoring = ScoringSystem(diff)
        
        # Multiple kills
        scoring.add_kill(10)  # Combo starts at 1.0
        score = scoring.add_kill(10)  # Combo should increase
        
        assert score >= 10  # At least base score

    def test_combo_timeout(self):
        """Test combo resets after timeout."""
        from src.game.systems.difficulty import DifficultySystem, ScoringSystem
        
        diff = DifficultySystem()
        scoring = ScoringSystem(diff)
        
        scoring.add_kill(10)
        scoring.update(0.1)
        
        # Combo should still be active
        assert scoring.combo_multiplier >= 1.0
```

---

## 17. Implementation Phases

### Phase 1: Foundation (Day 1-2)

**Goals:**
- Project setup with dependencies
- Basic Textual app structure
- Core game loop implementation
- Entity system base classes

**Deliverables:**
```
✓ pyproject.toml with dependencies
✓ Basic Textual App subclass
✓ Game loop with fixed timestep
✓ Entity and Component base classes
✓ Entity factory functions
```

### Phase 2: Core Gameplay (Day 3-5)

**Goals:**
- Player movement and controls
- Basic rendering (ASCII characters)
- Collision detection system
- Projectile and shooting mechanics

**Deliverables:**
```
✓ Input handling (WASD/arrows)
✓ Player movement system
✓ Bullet spawning and movement
✓ Circle-circle collision detection
✓ Basic HUD display
```

### Phase 3: Procedural Content (Day 6-8)

**Goals:**
- Asteroid generation and spawning
- Enemy AI behaviors
- Difficulty progression system
- Scoring system with combos

**Deliverables:**
```
✓ Spatial grid for efficient collision
✓ Asteroid spawning system
✓ Enemy AI (chase, shoot, dive)
✓ Difficulty scaling
✓ Score tracking with multipliers
```

### Phase 4: Game Flow (Day 9-10)

**Goals:**
- Game state machine
- Menu screens
- Pause functionality
- Game over and restart

**Deliverables:**
```
✓ State machine implementation
✓ Main menu screen
✓ Pause overlay
✓ Game over screen
✓ Restart functionality
```

### Phase 5: Polish (Day 11-12)

**Goals:**
- High score persistence
- Visual effects (explosions)
- Sound effects (optional, terminal beeps)
- Error handling and edge cases

**Deliverables:**
```
✓ High score JSON persistence
✓ Explosion effects
✓ Terminal beep sounds
✓ Comprehensive error handling
✓ Debug mode toggle
```

### Phase 6: Testing & Refinement (Day 13-14)

**Goals:**
- Unit tests for core systems
- Integration testing
- Performance optimization
- Bug fixes

**Deliverables:**
```
✓ Unit test suite (>80% coverage target)
✓ Integration tests
✓ Performance profiling
✓ Bug fixes and polish
```

---

## Appendix: Configuration Constants

```python
# src/game/config.py

from dataclasses import dataclass


@dataclass(frozen=True)
class GameConfig:
    """Immutable game configuration constants."""

    # Display
    DEFAULT_WIDTH: int = 80
    DEFAULT_HEIGHT: int = 40
    MIN_WIDTH: int = 60
    MIN_HEIGHT: int = 24

    # Timing
    TARGET_FPS: int = 60
    FIXED_DT: float = 1.0 / 60.0
    MAX_FRAME_SKIP: int = 5

    # Player
    PLAYER_SPEED: float = 300.0  # pixels per second
    PLAYER_MAX_HEALTH: int = 100
    PLAYER_SHOOT_COOLDOWN: float = 0.15  # seconds
    PLAYER_BULLET_SPEED: float = 600.0

    # Enemies
    ENEMY_BASE_SPEED: float = 100.0
    ENEMY_SPAWN_INTERVAL: float = 4.0  # seconds at base difficulty
    ENEMY_BULLET_SPEED: float = 300.0

    # Asteroids
    ASTEROID_SPAWN_INTERVAL: float = 2.0  # seconds at base difficulty
    ASTEROID_BASE_SPEED: float = 80.0
    ASTEROID_SPEED_VARIANCE: float = 40.0

    # Scoring
    SCORE_ASTEROID_SMALL: int = 10
    SCORE_ASTEROID_MEDIUM: int = 25
    SCORE_ASTEROID_LARGE: int = 50
    SCORE_ENEMY_BASIC: int = 20
    SCORE_ENEMY_ADVANCED: int = 50
    SCORE_BOSS: int = 500

    # Difficulty
    DIFFICULTY_SCALE_PER_LEVEL: float = 0.15
    LEVEL_SCORE_THRESHOLDS: tuple[int, ...] = (
        0, 500, 1500, 3000, 5000, 8000, 12000, 17000, 23000, 30000
    )

    # Persistence
    HIGH_SCORES_FILE: str = "assets/high_scores.json"
    MAX_HIGH_SCORES: int = 10


# Global config instance
CONFIG = GameConfig()
```

---

## Summary Checklist

### Core Features
- [ ] Fixed 60 FPS game loop with interpolation
- [ ] WASD/Arrow keyboard controls
- [ ] Space to shoot, ESC to pause
- [ ] Smooth player movement
- [ ] ASCII art rendering

### Gameplay
- [ ] Procedural asteroid generation
- [ ] Enemy ships with AI behaviors
- [ ] Collision detection with spatial partitioning
- [ ] Scoring system with combos
- [ ] Difficulty progression per level

### UI/UX
- [ ] Main menu screen
- [ ] HUD with score/level/health
- [ ] Pause menu
- [ ] Game over screen
- [ ] High scores display

### Persistence
- [ ] High score JSON file
- [ ] Atomic file writes
- [ ] Validation on load

### Code Quality
- [ ] Type hints throughout
- [ ] Error handling with logging
- [ ] Unit tests for core systems
- [ ] Clean architecture (ECS-lite)

---

*Plan generated for Terminal ASCII Roguelike Space Shooter*  
*Framework: Python 3.11+ with Textual TUI*  
*Target: 60 FPS real-time gameplay in terminal*
