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

    def get_bus_voltage(self) -> float | None:
        """Gets the bus voltage from the INA219.

        Returns:
            The bus voltage in volts, or None if the data is not available.
        """
        try:
            return self._ina219.bus_voltage
        except Exception as e:
            self._log.error("Error retrieving bus voltage", e)

    def get_shunt_voltage(self) -> float | None:
        """Gets the shunt voltage from the INA219.

        Returns:
            The shunt voltage in volts, or None if the data is not available.
        """
        try:
            return self._ina219.shunt_voltage
        except Exception as e:
            self._log.error("Error retrieving shunt voltage", e)

    def get_current(self) -> float | None:
        """Gets the current from the INA219.

        Returns:
            The current in amps, or None if the data is not available.
        """
        try:
            return self._ina219.current
        except Exception as e:
            self._log.error("Error retrieving current", e)
