"""This protocol specifies the interface that any magnetometer implementation must
adhere to, ensuring consistent behavior across different magnetometer hardware.
"""

from ..sensor_reading.magnetic import Magnetic


class MagnetometerProto:
    """Protocol defining the interface for a Magnetometer."""

    async def get_vector(self) -> Magnetic:
        """Gets the magnetic field vector from the magnetometer.

        Returns:
            A Magnetic object containing the x, y, and z magnetic field values in micro-Tesla (uT)

        Raises:
            SensorReadingTimeoutError: If the reading times out.
            SensorReadingUnknownError: If an unknown error occurs while reading the magnetometer.
        """
        ...
