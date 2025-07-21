"""This protocol specifies the interface that any light sensor implementation
must adhere to, ensuring consistent behavior across different light sensor
hardware.
"""


class LightSensorProto:
    """Protocol defining the interface for a light sensor."""

    def get_light(self) -> float | None:
        """Gets the light reading of the sensor.

        Returns:
            The raw light level measurement, or None if not available.
        """
        ...

    def get_lux(self) -> float | None:
        """Gets the light reading of the sensor.

        Returns:
            The light level in Lux, or None if not available.
        """
        ...
