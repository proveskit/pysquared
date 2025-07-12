"""This protocol specifies the interface that any IMU implementation must adhere to,
ensuring consistent behavior across different IMU hardware.
"""


class IMUProto:
    """Protocol defining the interface for an Inertial Measurement Unit (IMU)."""

    def get_gyro_data(self) -> tuple[float, float, float] | None:
        """Gets the gyroscope data from the inertial measurement unit.

        Returns:
            A tuple containing the x, y, and z angular acceleration values in
            radians per second, or None if not available.

        Raises:
            Exception: If there is an error retrieving the values.
        """
        ...

    def get_acceleration(self) -> tuple[float, float, float] | None:
        """Gets the acceleration data from the inertial measurement unit.

        Returns:
            A tuple containing the x, y, and z acceleration values in m/s^2, or
            None if not available.

        Raises:
            Exception: If there is an error retrieving the values.
        """
        ...
