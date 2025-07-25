"""This protocol specifies the interface that any light sensor implementation
must adhere to, ensuring consistent behavior across different light sensor
hardware.
"""

from ..sensor_reading.light import Light
from ..sensor_reading.lux import Lux


class LightSensorProto:
    """Protocol defining the interface for a light sensor."""

    def get_light(self) -> Light:
        """Gets the light reading of the sensor.

        Returns:
            A Light object containing a non-unit-specific light level reading.

        Raises:
            SensorReadingValueError: If the reading returns an invalid value.
            SensorReadingTimeoutError: If the reading times out.
            SensorReadingUnknownError: If an unknown error occurs while reading the light sensor.
        """
        ...

    def get_lux(self) -> Lux:
        """Gets the light reading of the sensor.

        Returns:
            A Lux object containing the light level in SI lux.

        Raises:
            SensorReadingValueError: If the reading returns an invalid value.
            SensorReadingTimeoutError: If the reading times out.
            SensorReadingUnknownError: If an unknown error occurs while reading the light sensor.
        """
        ...
