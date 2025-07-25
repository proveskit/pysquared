"""This module defines the `MCP9808Manager` class, which provides a high-level interface
for interacting with the MCP9808 temperature sensor. It handles the initialization of the sensor
and provides methods for reading temperature data.

**Usage:**
```python
logger = Logger()
i2c = busio.I2C(board.SCL, board.SDA)
temp_sensor = MCP9808Manager(logger, i2c, 0x18)
temperature = temp_sensor.get_temperature()
```
"""

from adafruit_mcp9808 import MCP9808
from busio import I2C

try:
    from typing_extensions import Literal
except ImportError:
    pass

from ....logger import Logger
from ....protos.temperature_sensor import TemperatureSensorProto
from ...exception import HardwareInitializationError


class MCP9808Manager(TemperatureSensorProto):
    """Manages the MCP9808 temperature sensor."""

    def __init__(
        self,
        logger: Logger,
        i2c: I2C,
        addr: int = 0x18,
        resolution: Literal[0, 1, 2, 3] = 1,
    ) -> None:
        """Initializes the MCP9808Manager.

        Args:
            logger: The logger to use.
            i2c: The I2C bus connected to the chip.
            addr: The I2C address of the MCP9808. Defaults to 0x18.
            resolution: The resolution of the temperature sensor. Defaults to 1 which is 0.25 degrees celsius.
            =======   ============   ==============
            Value     Resolution     Reading Time
            =======   ============   ==============
            0          0.5°C            30 ms
            1          0.25°C           65 ms
            2         0.125°C          130 ms
            3         0.0625°C         250 ms
            =======   ============   ==============

        Raises:
            HardwareInitializationError: If the MCP9808 fails to initialize.
        """
        self._log: Logger = logger
        try:
            logger.debug("Initializing MCP9808 temperature sensor")
            self._mcp9808: MCP9808 = MCP9808(i2c, addr)
        except Exception as e:
            raise HardwareInitializationError(
                "Failed to initialize MCP9808 temperature sensor"
            ) from e

        self._mcp9808.resolution = resolution

    def get_temperature(self) -> float | None:
        """Gets the temperature reading from the MCP9808.

        Returns:
            The temperature in degrees Celsius, or None if the data is not available.
        """
        try:
            return self._mcp9808.temperature
        except Exception as e:
            self._log.error("Error retrieving MCP9808 temperature sensor values", e)
            return None
