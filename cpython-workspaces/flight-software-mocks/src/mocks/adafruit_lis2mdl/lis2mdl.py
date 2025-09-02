"""Mock for the Adafruit LIS2MDL magnetometer.

This module provides a mock implementation of the Adafruit LIS2MDL magnetometer for
testing purposes. It allows for simulating the behavior of the LIS2MDL without the
need for actual hardware.
"""

# from pysquared.sensor_reading.magnetic import Magnetic


class LIS2MDL:
    """A mock LIS2MDL magnetometer."""

    def __init__(self, i2c) -> None:
        """Initializes the mock LIS2MDL.

        Args:
            i2c: The I2C bus to use.
        """
        pass
