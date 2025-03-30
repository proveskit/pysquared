"""
Protocol defining the interface for an Inertial Measurement Unit (IMU).
"""


class IMUProto:
    def get_gyro_data(self) -> tuple[float, float, float] | None:
        """Get the gyroscope data from the inertial measurement unit.

        :return: A tuple containing the x, y, and z angular acceleration values in radians per second or None if not available.
        :rtype: tuple[float, float, float] | None

        :raises Exception: If there is an error retrieving the values.
        """
        ...

    def get_acceleration(self) -> tuple[float, float, float] | None:
        """Get the acceleration data from the inertial measurement unit.

        :return: A tuple containing the x, y, and z acceleration values in m/s^2 or None if not available.
        :rtype: tuple[float, float, float] | None

        :raises Exception: If there is an error retrieving the values.
        """
        ...
