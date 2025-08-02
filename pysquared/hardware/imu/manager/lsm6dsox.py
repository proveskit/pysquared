"""This module defines the `LSM6DSOXManager` class, which provides a high-level interface
for interacting with the LSM6DSOX inertial measurement unit. It handles the initialization of the sensor and
provides methods for reading gyroscope, acceleration, and temperature data.

**Usage:**
```python
logger = Logger()
i2c = busio.I2C(board.SCL, board.SDA)
imu = LSM6DSOXManager(logger, i2c, 0x6A)
gyro_data = imu.get_gyro_data()
accel_data = imu.get_acceleration()
temp_data = imu.get_temperature()
```
"""

from adafruit_lsm6ds.lsm6dsox import LSM6DSOX
from busio import I2C

from ....logger import Logger
from ....protos.imu import IMUProto
from ....protos.temperature_sensor import TemperatureSensorProto
from ....sensor_reading.acceleration import Acceleration
from ....sensor_reading.error import (
    SensorReadingUnknownError,
)
from ....sensor_reading.gyro import Gyro
from ....sensor_reading.temperature import Temperature
from ...exception import HardwareInitializationError


class LSM6DSOXManager(IMUProto, TemperatureSensorProto):
    """Manages the LSM6DSOX IMU."""

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

    def get_gyro_data(self) -> Gyro:
        """Gets the gyroscope data from the IMU.

        Returns:
            A Gyro object containing the x, y, and z angular velocity in radians per second.

        Raises:
            SensorReadingUnknownError: If an unknown error occurs while reading the gyroscope data.
        """
        try:
            return Gyro(self._imu.gyro[0], self._imu.gyro[1], self._imu.gyro[2])
        except Exception as e:
            raise SensorReadingUnknownError("Failed to read gyroscope data") from e

    def get_acceleration(self) -> Acceleration:
        """Gets the acceleration data from the IMU.

        Returns:
            An Acceleration object containing the x, y, and z acceleration values in m/s².

        Raises:
            SensorReadingUnknownError: If an unknown error occurs while reading the acceleration data.
        """
        try:
            return Acceleration(
                self._imu.acceleration[0],
                self._imu.acceleration[1],
                self._imu.acceleration[2],
            )
        except Exception as e:
            raise SensorReadingUnknownError("Failed to read acceleration") from e

    def get_temperature(self) -> Temperature:
        """Gets the temperature reading from the IMU.

        Returns:
            A Temperature object containing the temperature in degrees Celsius.

        Raises:
            SensorReadingUnknownError: If an unknown error occurs while reading the temperature.
        """
        try:
            return Temperature(self._imu.temperature)
        except Exception as e:
            raise SensorReadingUnknownError("Failed to read temperature") from e
