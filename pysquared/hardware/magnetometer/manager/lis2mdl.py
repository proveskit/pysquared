from ....logger import Logger
from ...decorators import with_retries
from ...exception import HardwareInitializationError
from ..magnetometer_protocol import MagnetometerProto

try:
    from mocks.adafruit_lis2mdl.lis2mdl import LIS2MDL  # type: ignore
except ImportError:
    from lib.adafruit_lis2mdl import LIS2MDL

# Type hinting only
try:
    from busio import I2C
except ImportError:
    pass


class LIS2MDLManager(MagnetometerProto):
    """Manager class for creating LIS2MDL magnetometer instances.
    The purpose of the manager class is to hide the complexity of magnetometer initialization from the caller.
    Specifically we should try to keep adafruit_lis2mdl to only this manager class.
    """

    @with_retries(max_attempts=3, initial_delay=1)
    def __init__(
        self,
        logger: Logger,
        i2c: I2C,
    ) -> None:
        """Initialize the manager class.

        :param Logger logger: Logger instance for logging messages.
        :param busio.I2C i2c: The I2C bus connected to the chip.

        :raises HardwareInitializationError: If the magnetometer fails to initialize.
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
        """Get the magnetic field vector from the magnetometer.

        :return: A tuple containing the x, y, and z magnetic field values in Gauss or None if not available.
        :rtype: tuple[float, float, float] | None

        :raises Exception: If there is an error retrieving the values.
        """
        try:
            return self._magnetometer.magnetic
        except Exception as e:
            self._log.error("Error retrieving magnetometer sensor values", e)
