"""Magnetic sensor reading."""

try:
    from typing import Tuple
except ImportError:
    pass

from .base import Reading


class Magnetic(Reading):
    """Magnetic sensor reading in micro-Tesla (uT).

    Tesla is the SI unit of magnetic flux density (also called magnetic B-field strength),
    and 1 Tesla = 1,000,000 micro-Tesla (uT).
    """

    def __init__(self, x: float, y: float, z: float) -> None:
        """Initialize the magnetic sensor reading.

        Args:
            x: The x magnetic field in micro-Tesla (uT)
            y: The y magnetic field in micro-Tesla (uT)
            z: The z magnetic field in micro-Tesla (uT)
        """
        super().__init__()
        self.x = x
        self.y = y
        self.z = z

    @property
    def value(self) -> Tuple[float, float, float]:
        """Magnetic field in x, y, z micro-Tesla (uT).

        Tesla is the SI unit of magnetic flux density (also called magnetic B-field strength),
        and 1 Tesla = 1,000,000 micro-Tesla (uT).

        Returns:
            A tuple containing the x, y, and z components of the magnetic field.
        """
        return (self.x, self.y, self.z)
