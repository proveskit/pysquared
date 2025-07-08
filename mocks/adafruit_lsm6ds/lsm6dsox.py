"""Mock for the Adafruit LSM6DSOX IMU.

This module provides a mock implementation of the Adafruit LSM6DSOX IMU for
testing purposes. It allows for simulating the behavior of the LSM6DSOX without the
need for actual hardware.

Usage:
    i2c = I2C()
    lsm6dsox = LSM6DSOX(i2c, 0x6A)
    acceleration = lsm6dsox.acceleration
    gyro = lsm6dsox.gyro
    temperature = lsm6dsox.temperature
"""

from busio import I2C


class LSM6DSOX:
    """A mock LSM6DSOX IMU."""

    def __init__(self, i2c_bus: I2C, address: int) -> None:
        """Initializes the mock LSM6DSOX.

        Args:
            i2c_bus: The I2C bus to use.
            address: The I2C address of the LSM6DSOX.
        """
        ...

    acceleration: tuple[float, float, float] = (0.0, 0.0, 0.0)
    gyro: tuple[float, float, float] = (0.0, 0.0, 0.0)
    temperature: float = 0.0
