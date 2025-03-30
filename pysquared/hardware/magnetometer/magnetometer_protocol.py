"""
This module defines a protocol for creating magnetometer instances.
This is useful for defining an interface that can be implemented by different classes
for different types of magnetometers. This allows for flexibility in the design of the system,
enabling the use of different magnetometer implementations without changing the code that uses them.

CircuitPython does not support Protocols directly, but this class can still be used to define an interface

https://docs.python.org/3/library/typing.html#typing.Protocol
"""


class MagnetometerProto:
    def get_vector(self) -> tuple[float, float, float] | None:
        """Get the magnetic field vector from the magnetometer.

        :return: A tuple containing the x, y, and z magnetic field values in Gauss or None if not available.
        :rtype: tuple[float, float, float] | None

        :raises Exception: If there is an error retrieving the values.
        """
        ...
