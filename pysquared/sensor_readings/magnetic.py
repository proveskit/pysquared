"""Magnetic sensor reading."""

try:
    from typing import Tuple
except ImportError:
    pass

from .base import Reading


class Magnetic(Reading):
    """Magnetic sensor reading in micro-Tesla (uT)."""

    def __init__(self, x: float, y: float, z: float) -> None:
        """Initialize the magnetic sensor reading.

        :param x: The x magnetic field in micro-Tesla (uT)
        :type x: float
        :param y: The y magnetic field in micro-Tesla (uT)
        :type y: float
        :param z: The z magnetic field in micro-Tesla (uT)
        :type z: float
        """
        super().__init__()
        self.x = x
        self.y = y
        self.z = z

    @property
    def value(self) -> Tuple[float, float, float]:
        """Magnetic field in x, y, z micro-Tesla (uT).

        :return: Magnetic field in x, y, z micro-Tesla (uT)
        :rtype: Tuple[float, float, float]
        """
        return (self.x, self.y, self.z)
