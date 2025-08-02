"""This protocol specifies the interface that any IMU implementation must adhere to,
ensuring consistent behavior across different IMU hardware.
"""

from ..sensor_reading.acceleration import Acceleration
from ..sensor_reading.gyro import Gyro


class IMUProto:
    """Protocol defining the interface for an Inertial Measurement Unit (IMU)."""

    def get_gyro_data(self) -> Gyro:
        """Gets the gyroscope data from the inertial measurement unit.

        Returns:
            A Gyro object containing the x, y, and z angular velocity in radians per second.

        Raises:
            SensorReadingValueError: If the reading returns an invalid value.
            SensorReadingTimeoutError: If the reading times out.
            SensorReadingUnknownError: If an unknown error occurs while reading the light sensor.
        """
        ...

    def get_acceleration(self) -> Acceleration:
        """Gets the acceleration data from the inertial measurement unit.

        Returns:
            An Acceleration object containing the x, y, and z acceleration values in m/s².

        Raises:
            SensorReadingValueError: If the reading returns an invalid value.
            SensorReadingTimeoutError: If the reading times out.
            SensorReadingUnknownError: If an unknown error occurs while reading the light sensor.
        """
        ...
