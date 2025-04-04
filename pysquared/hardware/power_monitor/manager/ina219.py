from ....logger import Logger
from ....protos.power_monitor import PowerMonitorProto
from ...decorators import with_retries
from ...exception import HardwareInitializationError

try:
    from mocks.adafruit_ina219.ina219 import INA219  # type: ignore
except ImportError:
    from adafruit_ina219 import INA219

# Type hinting only
try:
    from busio import I2C
except ImportError:
    pass


class INA219Manager(PowerMonitorProto):
    @with_retries(max_attempts=3, initial_delay=1)
    def __init__(
        self,
        logger: Logger,
        i2c: I2C,
        addr: int,
    ) -> None:
        """Initialize the INA219 power monitor.

        :param busio.I2C i2c: The I2C bus connected to the chip.
        :param int addr: The I2C address of the INA219.

        :raises HardwareInitializationError: If the INA219 fails to initialize.
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
        """Get the bus voltage from the INA219.

        :return: The bus voltage in volts.
        :rtype: float

        :raises Exception: If there is an error retrieving the value.
        """
        try:
            return self._ina219.bus_voltage
        except Exception as e:
            self._log.error("Error retrieving bus voltage", e)

    def get_shunt_voltage(self) -> float | None:
        """Get the shunt voltage from the INA219.

        :return: The shunt voltage in volts.
        :rtype: float

        :raises Exception: If there is an error retrieving the value.
        """
        try:
            return self._ina219.shunt_voltage
        except Exception as e:
            self._log.error("Error retrieving shunt voltage", e)

    def get_current(self) -> float | None:
        """Get the current from the INA219.

        :return: The current in amps.
        :rtype: float

        :raises Exception: If there is an error retrieving the value.
        """
        try:
            return self._ina219.current
        except Exception as e:
            self._log.error("Error retrieving current", e)
