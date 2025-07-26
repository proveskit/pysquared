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
from adafruit_tca9548a import TCA9548A_Channel
from busio import I2C

from ....logger import Logger
from ....protos.temperature_sensor import TemperatureSensorProto
from ....sensor_reading.error import SensorReadingUnknownError
from ....sensor_reading.temperature import Temperature
from ...exception import HardwareInitializationError


class MCP9808Manager(TemperatureSensorProto):
    """Manages the MCP9808 temperature sensor."""

    def __init__(
        self,
        logger: Logger,
        i2c: I2C | TCA9548A_Channel,
        addr: int,
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

    def get_temperature(self) -> Temperature:
        """Gets the temperature reading from the MCP9808.

        Returns:
            A Temperature object containing the temperature in degrees Celsius.

        Raises:
            SensorReadingUnknownError: If an unknown error occurs while reading the temperature.
        """
        try:
            return Temperature(self._mcp9808.temperature)
        except Exception as e:
            raise SensorReadingUnknownError(
                "Failed to read temperature from MCP9808"
            ) from e
