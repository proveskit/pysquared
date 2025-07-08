"""Mock for the Adafruit LIS2MDL magnetometer.

This module provides a mock implementation of the Adafruit LIS2MDL magnetometer for
testing purposes. It allows for simulating the behavior of the LIS2MDL without the
need for actual hardware.

Usage:
    i2c = I2C()
    lis2mdl = LIS2MDL(i2c)
    magnetic_field = lis2mdl.magnetic
"""


class LIS2MDL:
    """A mock LIS2MDL magnetometer."""

    def __init__(self, i2c) -> None:
        """Initializes the mock LIS2MDL.

        Args:
            i2c: The I2C bus to use.
        """
        self.i2c = i2c

    magnetic: tuple[float, float, float] = (0.0, 0.0, 0.0)
