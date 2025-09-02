"""This module defines the `INA219Manager` class, which provides a high-level interface
for interacting with the INA219 power monitor. It handles the initialization of the sensor
and provides methods for reading bus voltage, shunt voltage, and current.

**Usage:**
```python
logger = Logger()
i2c = busio.I2C(board.SCL, board.SDA)
power_monitor = INA219Manager(logger, i2c, 0x40)
bus_voltage = power_monitor.get_bus_voltage()
shunt_voltage = power_monitor.get_shunt_voltage()
current = power_monitor.get_current()
```
"""

from adafruit_ina219 import INA219
from busio import I2C

from ....logger import Logger
from ....protos.power_monitor import PowerMonitorProto
from ....sensor_reading.current import Current
from ....sensor_reading.error import (
    SensorReadingUnknownError,
)
from ....sensor_reading.voltage import Voltage
from ...exception import HardwareInitializationError


class INA219Manager(PowerMonitorProto):
    """Manages the INA219 power monitor."""

    def __init__(
        self,
        logger: Logger,
        i2c: I2C,
        addr: int,
    ) -> None:
        """Initializes the INA219Manager.

        Args:
            logger: The logger to use.
            i2c: The I2C bus connected to the chip.
            addr: The I2C address of the INA219.

        Raises:
            HardwareInitializationError: If the INA219 fails to initialize.
        """
        self._log: Logger = logger
        try:
            logger.debug("Initializing INA219 power monitor")
            self._ina219: INA219 = INA219(i2c, addr)
        except Exception as e:
            raise HardwareInitializationError(
                "Failed to initialize INA219 power monitor"
            ) from e

    def get_bus_voltage(self) -> Voltage:
        """Gets the bus voltage from the INA219.

        Returns:
            A Voltage object containing the bus voltage in volts.

        Raises:
            SensorReadingUnknownError: If an unknown error occurs while reading the light sensor.
        """
        try:
            return Voltage(self._ina219.bus_voltage)
        except Exception as e:
            raise SensorReadingUnknownError("Failed to get bus voltage") from e

    def get_shunt_voltage(self) -> Voltage:
        """Gets the shunt voltage from the INA219.

        Returns:
            A Voltage object containing the shunt voltage in volts.

        Raises:
            SensorReadingUnknownError: If an unknown error occurs while reading the light sensor.
        """
        try:
            return Voltage(self._ina219.shunt_voltage)
        except Exception as e:
            raise SensorReadingUnknownError("Failed to get shunt voltage") from e

    def get_current(self) -> Current:
        """Gets the current from the INA219.

        Returns:
            A Current object containing the current in milliamps (mA)

        Raises:
            SensorReadingUnknownError: If an unknown error occurs while reading the light sensor.
        """
        try:
            return Current(self._ina219.current)
        except Exception as e:
            raise SensorReadingUnknownError("Failed to get current") from e
