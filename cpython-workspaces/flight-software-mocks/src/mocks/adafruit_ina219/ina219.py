"""Mock for the Adafruit INA219 power monitor.

This module provides a mock implementation of the Adafruit INA219 power monitor for
testing purposes. It allows for simulating the behavior of the INA219 without the
need for actual hardware.
"""


class INA219:
    """A mock INA219 power monitor."""

    def __init__(self, i2c, addr) -> None:
        """Initializes the mock INA219.

        Args:
            i2c: The I2C bus to use.
            addr: The I2C address of the INA219.
        """
        self.i2c = i2c
        self.addr = addr

    bus_voltage = 0.0
    shunt_voltage = 0.0
    current = 0.0
