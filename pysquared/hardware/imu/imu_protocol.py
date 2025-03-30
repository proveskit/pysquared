"""
This module defines a protocol for creating IMU instances.
This is useful for defining an interface that can be implemented by different classes
for different types of IMUs. This allows for flexibility in the design of the system,
enabling the use of different IMU implementations without changing the code that uses them.

CircuitPython does not support Protocols directly, but this class can still be used to define an interface

https://docs.python.org/3/library/typing.html#typing.Protocol
"""


class InertialMeasurementUnitProto:
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

    def get_temperature(self) -> float | None:
        """Get the temperature reading from the inertial measurement unit, if available.

        :return: The temperature in degrees Celsius or None if not available.
        :rtype: float | None

        :raises Exception: If there is an error retrieving the temperature value.
        """
        ...
