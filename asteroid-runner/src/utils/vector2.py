"""2D Vector math utilities."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Union


@dataclass
class Vector2:
    """
    2D vector for positions and velocities.

    Provides common vector operations with type safety.
    """

    x: float = 0.0
    y: float = 0.0

    def __post_init__(self) -> None:
        """Validate vector components."""
        if not isinstance(self.x, (int, float)):
            raise TypeError(f"x must be numeric, got {type(self.x)}")
        if not isinstance(self.y, (int, float)):
            raise TypeError(f"y must be numeric, got {type(self.y)}")

    @property
    def magnitude(self) -> float:
        """Get the length of the vector."""
        return math.sqrt(self.x * self.x + self.y * self.y)

    @property
    def magnitude_squared(self) -> float:
        """Get the squared length (avoids sqrt for comparisons)."""
        return self.x * self.x + self.y * self.y

    @property
    def normalized(self) -> Vector2:
        """Get a unit vector in the same direction."""
        mag = self.magnitude
        if mag == 0:
            return Vector2(0, 0)
        return Vector2(self.x / mag, self.y / mag)

    def dot(self, other: Vector2) -> float:
        """Calculate dot product with another vector."""
        return self.x * other.x + self.y * other.y

    def cross(self, other: Vector2) -> float:
        """Calculate 2D cross product (returns scalar)."""
        return self.x * other.y - self.y * other.x

    def distance_to(self, other: Vector2) -> float:
        """Get distance to another point."""
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)

    def distance_squared_to(self, other: Vector2) -> float:
        """Get squared distance to another point (avoids sqrt)."""
        dx = self.x - other.x
        dy = self.y - other.y
        return dx * dx + dy * dy

    def angle_to(self, other: Vector2) -> float:
        """Get angle in radians to another point."""
        return math.atan2(other.y - self.y, other.x - self.x)

    def lerp(self, other: Vector2, t: float) -> Vector2:
        """Linear interpolation to another vector."""
        t = max(0.0, min(1.0, t))
        return Vector2(
            self.x + (other.x - self.x) * t,
            self.y + (other.y - self.y) * t,
        )

    def __add__(self, other: Vector2) -> Vector2:
        """Add two vectors."""
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector2) -> Vector2:
        """Subtract two vectors."""
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: Union[int, float]) -> Vector2:
        """Multiply vector by scalar."""
        return Vector2(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: Union[int, float]) -> Vector2:
        """Multiply scalar by vector."""
        return Vector2(self.x * scalar, self.y * scalar)

    def __truediv__(self, scalar: Union[int, float]) -> Vector2:
        """Divide vector by scalar."""
        if scalar == 0:
            raise ZeroDivisionError("Cannot divide vector by zero")
        return Vector2(self.x / scalar, self.y / scalar)

    def __neg__(self) -> Vector2:
        """Negate vector."""
        return Vector2(-self.x, -self.y)

    def __abs__(self) -> Vector2:
        """Get absolute value of components."""
        return Vector2(abs(self.x), abs(self.y))

    def __repr__(self) -> str:
        return f"Vector2({self.x:.2f}, {self.y:.2f})"

    def to_tuple(self) -> tuple[float, float]:
        """Convert to tuple."""
        return (self.x, self.y)

    @classmethod
    def from_angle(cls, angle: float, magnitude: float = 1.0) -> Vector2:
        """Create vector from angle and magnitude."""
        return cls(
            math.cos(angle) * magnitude,
            math.sin(angle) * magnitude,
        )

    @classmethod
    def zero(cls) -> Vector2:
        """Create zero vector."""
        return cls(0.0, 0.0)

    @classmethod
    def up(cls) -> Vector2:
        """Create unit vector pointing up (decreases y)."""
        return cls(0.0, -1.0)

    @classmethod
    def down(cls) -> Vector2:
        """Create unit vector pointing down (increases y)."""
        return cls(0.0, 1.0)

    @classmethod
    def left(cls) -> Vector2:
        """Create unit vector pointing left (decreases x)."""
        return cls(-1.0, 0.0)

    @classmethod
    def right(cls) -> Vector2:
        """Create unit vector pointing right (increases x)."""
        return cls(1.0, 0.0)
