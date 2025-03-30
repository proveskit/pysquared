try:
    from mocks.adafruit_lsm6ds.lsm6dsox import LSM6DSOX  # type: ignore
except ImportError:
    from lib.adafruit_lsm6ds.lsm6dsox import LSM6DSOX

from ....logger import Logger
from ....protos.imu import IMUProto
from ....protos.temperature_sensor import TemperatureSensorProto
from ...decorators import with_retries
from ...exception import HardwareInitializationError

# Type hinting only
try:
    from busio import I2C
except ImportError:
    pass


class LSM6DSOXManager(IMUProto, TemperatureSensorProto):
    """Manager class for creating LIS2MDL IMU instances.
    The purpose of the manager class is to hide the complexity of IMU initialization from the caller.
    Specifically we should try to keep adafruit_lsm6ds to only this manager class.
    """

    @with_retries(max_attempts=3, initial_delay=1)
    def __init__(
        self,
        logger: Logger,
        i2c: I2C,
        address: int,
    ) -> None:
        """Initialize the manager class.

        :param Logger logger: Logger instance for logging messages.
        :param busio.I2C i2c: The I2C bus connected to the chip.
        :param int address: The I2C address of the IMU.

        :raises HardwareInitializationError: If the IMU fails to initialize.
        """
        self._log: Logger = logger

        try:
            self._log.debug("Initializing IMU")
            self._imu: LSM6DSOX = LSM6DSOX(i2c, address)
        except Exception as e:
            raise HardwareInitializationError("Failed to initialize IMU") from e

    def get_gyro_data(self) -> tuple[float, float, float] | None:
        """Get the gyroscope data from the inertial measurement unit.

        :return: A tuple containing the x, y, and z angular acceleration values in radians per second or None if not available.
        :rtype: tuple[float, float, float] | None

        :raises Exception: If there is an error retrieving the values.
        """
        try:
            return self._imu.gyro
        except Exception as e:
            self._log.error("Error retrieving IMU gyro sensor values", e)

    def get_acceleration(self) -> tuple[float, float, float] | None:
        """Get the acceleration data from the inertial measurement unit.

        :return: A tuple containing the x, y, and z acceleration values in m/s^2 or None if not available.
        :rtype: tuple[float, float, float] | None

        :raises Exception: If there is an error retrieving the values.
        """
        try:
            return self._imu.acceleration
        except Exception as e:
            self._log.error("Error retrieving IMU acceleration sensor values", e)

    def get_temperature(self) -> float | None:
        """Get the temperature reading from the inertial measurement unit, if available.

        :return: The temperature in degrees Celsius or None if not available.
        :rtype: float | None

        :raises Exception: If there is an error retrieving the temperature value.
        """
        try:
            return self._imu.temperature
        except Exception as e:
            self._log.error("Error retrieving IMU temperature sensor values", e)
