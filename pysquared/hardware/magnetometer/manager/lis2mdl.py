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

import asyncio

from adafruit_lis2mdl import LIS2MDL
from busio import I2C

from ....logger import Logger
from ....protos.magnetometer import MagnetometerProto
from ....sensor_reading.error import (
    SensorReadingTimeoutError,
    SensorReadingUnknownError,
)
from ....sensor_reading.magnetic import Magnetic
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

    async def get_vector(self) -> Magnetic:
        """Gets the magnetic field vector from the magnetometer.

        Returns:
            A Magnetic object containing the x, y, and z magnetic field values in micro-Tesla (uT)

        Raises:
            SensorReadingTimeoutError: If the reading times out.
            SensorReadingUnknownError: If an unknown error occurs while reading the magnetometer.
        """
        timeout = 1.0  # seconds
        try:
            m = await asyncio.wait_for(self._magnetometer.asyncio_magnetic, timeout)
            return Magnetic(
                x=m[0],
                y=m[1],
                z=m[2],
            )
        except asyncio.TimeoutError:
            raise SensorReadingTimeoutError(
                "Timeout while waiting for magnetometer data"
            )
        except Exception as e:
            raise SensorReadingUnknownError(
                "Unknown error while reading magnetometer data"
            ) from e
