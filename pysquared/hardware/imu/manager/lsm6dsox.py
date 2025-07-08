"""This module provides a manager for the LSM6DSOX IMU.

The LSM6DSOXManager class provides a high-level interface for interacting with the
LSM6DSOX inertial measurement unit. It handles the initialization of the sensor and
provides methods for reading gyroscope, acceleration, and temperature data.

Usage:
    logger = Logger()
    i2c = busio.I2C(board.SCL, board.SDA)
    imu = LSM6DSOXManager(logger, i2c, 0x6A)
    gyro_data = imu.get_gyro_data()
    accel_data = imu.get_acceleration()
    temp_data = imu.get_temperature()
"""

from adafruit_lsm6ds.lsm6dsox import LSM6DSOX
from busio import I2C

from ....logger import Logger
from ....protos.imu import IMUProto
from ....protos.temperature_sensor import TemperatureSensorProto
from ...decorators import with_retries
from ...exception import HardwareInitializationError


class LSM6DSOXManager(IMUProto, TemperatureSensorProto):
    """Manages the LSM6DSOX IMU."""

    @with_retries(max_attempts=3, initial_delay=1)
    def __init__(
        self,
        logger: Logger,
        i2c: I2C,
        address: int,
    ) -> None:
        """Initializes the LSM6DSOXManager.

        Args:
            logger: The logger to use.
            i2c: The I2C bus connected to the chip.
            address: The I2C address of the IMU.

        Raises:
            HardwareInitializationError: If the IMU fails to initialize.
        """
        self._log: Logger = logger

        try:
            self._log.debug("Initializing IMU")
            self._imu: LSM6DSOX = LSM6DSOX(i2c, address)
        except Exception as e:
            raise HardwareInitializationError("Failed to initialize IMU") from e

    def get_gyro_data(self) -> tuple[float, float, float] | None:
        """Gets the gyroscope data from the IMU.

        Returns:
            A tuple containing the x, y, and z angular acceleration values in
            radians per second, or None if the data is not available.
        """
        try:
            return self._imu.gyro
        except Exception as e:
            self._log.error("Error retrieving IMU gyro sensor values", e)

    def get_acceleration(self) -> tuple[float, float, float] | None:
        """Gets the acceleration data from the IMU.

        Returns:
            A tuple containing the x, y, and z acceleration values in m/s^2, or
            None if the data is not available.
        """
        try:
            return self._imu.acceleration
        except Exception as e:
            self._log.error("Error retrieving IMU acceleration sensor values", e)

    def get_temperature(self) -> float | None:
        """Gets the temperature reading from the IMU.

        Returns:
            The temperature in degrees Celsius, or None if the data is not available.
        """
        try:
            return self._imu.temperature
        except Exception as e:
            self._log.error("Error retrieving IMU temperature sensor values", e)
