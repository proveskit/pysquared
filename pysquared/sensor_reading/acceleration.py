"""Acceleration sensor reading."""

try:
    from typing import Tuple
except ImportError:
    pass

from .base import Reading


class Acceleration(Reading):
    """Acceleration sensor reading in meter per second²."""

    def __init__(self, x: float, y: float, z: float) -> None:
        """Initialize the acceleration sensor reading.

        Args:
            x: The x acceleration in meter per second²
            y: The y acceleration in meter per second²
            z: The z acceleration in meter per second²
        """
        super().__init__()
        self.x = x
        self.y = y
        self.z = z

    @property
    def value(self) -> Tuple[float, float, float]:
        """Acceleration in x, y, z meter per second².

        Returns:
            A tuple containing the x, y, and z components of the acceleration.
        """
        return (self.x, self.y, self.z)
