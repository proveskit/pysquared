"""This module defines the `LIS2MDLManager` class, which provides a high-level interface
for interacting with the LIS2MDL magnetometer. It handles the initialization of the sensor
and provides a method for reading the magnetic field vector.

**Usage:**
```python
logger = Logger()
i2c = busio.I2C(board.SCL, board.SDA)
magnetometer = LIS2MDLManager(logger, i2c)
mag_data = magnetometer.get_vector()
```
"""

from adafruit_lis2mdl import LIS2MDL
from busio import I2C

from ....logger import Logger
from ....protos.magnetometer import MagnetometerProto
from ...exception import HardwareInitializationError


class LIS2MDLManager(MagnetometerProto):
    """Manages the LIS2MDL magnetometer."""

    def __init__(
        self,
        logger: Logger,
        i2c: I2C,
    ) -> None:
        """Initializes the LIS2MDLManager.

        Args:
            logger: The logger to use.
            i2c: The I2C bus connected to the chip.

        Raises:
            HardwareInitializationError: If the magnetometer fails to initialize.
        """
        self._log: Logger = logger

        try:
            self._log.debug("Initializing magnetometer")
            self._magnetometer: LIS2MDL = LIS2MDL(i2c)
        except Exception as e:
            raise HardwareInitializationError(
                "Failed to initialize magnetometer"
            ) from e

    def get_vector(self) -> tuple[float, float, float] | None:
        """Gets the magnetic field vector from the magnetometer.

        Returns:
            A tuple containing the x, y, and z magnetic field values in Gauss, or
            None if the data is not available.
        """
        try:
            return self._magnetometer.magnetic
        except Exception as e:
            self._log.error("Error retrieving magnetometer sensor values", e)
