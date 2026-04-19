"""Game state management."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Optional

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
    """Game state machine with transition callbacks."""

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
        """Attempt to transition to a new state."""
        if not self.can_transition(target):
            return False

        old_state = self._state
        self._history.append(old_state)
        self._state = target

        for callback in self._transition_callbacks:
            callback(old_state, target)

        return True

    def on_transition(self, callback: Callable[[GameState, GameState], None]) -> None:
        """Register a transition callback."""
        self._transition_callbacks.append(callback)

    def get_history(self) -> list[GameState]:
        """Get state transition history."""
        return self._history.copy()


@dataclass
class GameData:
    """Persistent game data that survives across sessions."""

    high_scores: list[tuple[str, int]] = field(default_factory=list)
    total_games_played: int = 0
    total_time_played: float = 0.0
    highest_level_reached: int = 1


@dataclass
class SessionData:
    """Session-specific game data (resets each game)."""

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
    """Complete game context including all state."""

    state_machine: StateMachine = field(default_factory=StateMachine)
    game_data: GameData = field(default_factory=GameData)
    session: SessionData = field(default_factory=SessionData)

    player: Optional["Entity"] = field(default=None, repr=False)
    entities: dict[uuid.UUID, "Entity"] = field(default_factory=dict)

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
