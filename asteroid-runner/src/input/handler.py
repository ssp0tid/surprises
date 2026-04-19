"""Input handling system."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from textual.events import Key


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
    """Centralized input handling system."""

    DEFAULT_BINDINGS: list[KeyBinding] = [
        KeyBinding("w", InputAction.MOVE_UP),
        KeyBinding("s", InputAction.MOVE_DOWN),
        KeyBinding("a", InputAction.MOVE_LEFT),
        KeyBinding("d", InputAction.MOVE_RIGHT),
        KeyBinding("up", InputAction.MOVE_UP),
        KeyBinding("down", InputAction.MOVE_DOWN),
        KeyBinding("left", InputAction.MOVE_LEFT),
        KeyBinding("right", InputAction.MOVE_RIGHT),
        KeyBinding("i", InputAction.MOVE_UP),
        KeyBinding("k", InputAction.MOVE_DOWN),
        KeyBinding("j", InputAction.MOVE_LEFT),
        KeyBinding("l", InputAction.MOVE_RIGHT),
        KeyBinding("space", InputAction.SHOOT),
        KeyBinding("z", InputAction.SHOOT),
        KeyBinding("escape", InputAction.PAUSE),
        KeyBinding("p", InputAction.PAUSE),
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
        self._shoot_delay: float = 0.15

        for binding in self.DEFAULT_BINDINGS:
            self._bindings[binding.key.lower()] = binding.action

    def process_key(self, key: Key) -> Optional[InputAction]:
        """Process a key event and return the corresponding action."""
        key_name = key.key.lower()

        if key_name in self._bindings:
            action = self._bindings[key_name]

            if key.events == "pressed":
                self._handle_action_press(action)
            elif key.events == "released":
                self._handle_action_release(action)

            return action

        return None

    def _handle_action_press(self, action: InputAction) -> None:
        """Handle action key press."""
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
