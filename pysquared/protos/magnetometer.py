"""
Protocol defining the interface for a Magnetometer.
"""


class MagnetometerProto:
    def get_vector(self) -> tuple[float, float, float] | None:
        """Get the magnetic field vector from the magnetometer.

        :return: A tuple containing the x, y, and z magnetic field values in Gauss or None if not available.
        :rtype: tuple[float, float, float] | None

        :raises Exception: If there is an error retrieving the values.
        """
        ...
