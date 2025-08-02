"""Gyro sensor reading."""

try:
    from typing import Tuple
except ImportError:
    pass

from .base import Reading


class Gyro(Reading):
    """Gyro sensor reading in radians per second."""

    def __init__(self, x: float, y: float, z: float) -> None:
        """Initialize the gyro sensor reading.

        Args:
            x: The x angular velocity in radians per second
            y: The y angular velocity in radians per second
            z: The z angular velocity in radians per second
        """
        super().__init__()
        self.x = x
        self.y = y
        self.z = z

    @property
    def value(self) -> Tuple[float, float, float]:
        """Angular velocity in x, y, z radians per second

        Returns:
            A tuple containing the x, y, and z components of the angular velocity.
        """
        return (self.x, self.y, self.z)
