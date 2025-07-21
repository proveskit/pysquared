"""This module defines the `VEML7700Manager` class, which provides a high-level interface
for interacting with the VEML7700 light sensor. It handles the initialization of the sensor
and provides methods for reading light levels in various formats.

**Usage:**
```python
logger = Logger()
i2c = busio.I2C(board.SCL, board.SDA)
light_sensor = VEML7700Manager(logger, i2c)
lux_data = light_sensor.get_lux()
```
"""

import time

from adafruit_veml7700 import VEML7700
from busio import I2C

from ....logger import Logger
from ....protos.light_sensor import LightSensorProto
from ...exception import HardwareInitializationError


class VEML7700Manager(LightSensorProto):
    """Manages the VEML7700 ambient light sensor."""

    def __init__(
        self,
        logger: Logger,
        i2c: I2C,
        integration_time: int = VEML7700.ALS_25MS,
    ) -> None:
        """Initializes the VEML7700Manager.

        Args:
            logger: The logger to use.
            i2c: The I2C bus connected to the chip.
            integration_time: The integration time for the light sensor (default is 25ms).

        Raises:
            HardwareInitializationError: If the light sensor fails to initialize.
        """
        self._log: Logger = logger
        self.is_valid: bool = False

        try:
            self._log.debug("Initializing light sensor")
            self._light_sensor: VEML7700 = VEML7700(i2c)
            self._light_sensor.light_integration_time = integration_time
        except Exception as e:
            raise HardwareInitializationError(
                "Failed to initialize light sensor"
            ) from e

    def get_light(self) -> float | None:
        """Gets the light reading of the sensor with default gain and integration time.

        Returns:
            The raw light level measurement, or None if not available.
        """
        try:
            return self._light_sensor.light
        except Exception as e:
            self._log.error("Failed to get light reading:", e)
            return None

    def get_lux(self) -> float | None:
        """Gets the light reading of the sensor with default gain and integration time.

        Returns:
            The light level in Lux, or None if not available.
        """
        try:
            return self._light_sensor.lux
        except Exception as e:
            self._log.error("Failed to get lux reading:", e)
            return None

    def get_auto_lux(self) -> float | None:
        """Gets the auto lux reading of the sensor. This runs the sensor in auto mode
        and returns the lux value by searching through the available gain and integration time
        combinations to find the best match.

        Returns:
            The auto lux level, or None if not available.
        """
        try:
            return self._light_sensor.autolux
        except Exception as e:
            self._log.error("Failed to get auto lux reading:", e)
            return None

    def self_test(self) -> bool:
        """Performs a self-test on the light sensor to ensure it is functioning correctly.

        Returns:
            True if the self-test passes, False otherwise.
        """
        # Attempt to read a value from the sensor
        lux = self.get_auto_lux()
        if lux is None or lux == 0:
            self._log.warning("Light sensor self-test failed: No valid reading")
            self.is_valid = False
            return False
        # If we can read a value, the sensor is likely functioning
        self._log.debug("Light sensor self-test passed")
        self.is_valid = True
        return True

    def reset(self) -> None:
        """Resets the light sensor."""
        try:
            self._light_sensor.light_shutdown = True
            time.sleep(0.1)  # Allow time for the sensor to reset
            self._light_sensor.light_shutdown = False
            self._log.debug("Light sensor reset successfully")
        except Exception as e:
            self._log.error("Failed to reset light sensor:", e)
