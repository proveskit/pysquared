"""Mock for the Adafruit MCP9808 temperature sensor.

This module provides a mock implementation of the Adafruit MCP9808 temperature sensor for
testing purposes. It allows for simulating the behavior of the MCP9808 without the
need for actual hardware.
"""


class MCP9808:
    """A mock MCP9808 temperature sensor."""

    def __init__(self, i2c, addr) -> None:
        """Initializes the mock MCP9808.

        Args:
            i2c: The I2C bus to use.
            addr: The I2C address of the MCP9808.
        """
        self.i2c = i2c
        self.addr = addr

    temperature = 25.0
