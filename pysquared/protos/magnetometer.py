"""This protocol specifies the interface that any magnetometer implementation must
adhere to, ensuring consistent behavior across different magnetometer hardware.
"""


class MagnetometerProto:
    """Protocol defining the interface for a Magnetometer."""

    def get_vector(self) -> tuple[float, float, float] | None:
        """Gets the magnetic field vector from the magnetometer.

        Returns:
            A tuple containing the x, y, and z magnetic field values in Gauss, or
            None if not available.

        Raises:
            Exception: If there is an error retrieving the values.
        """
        ...
