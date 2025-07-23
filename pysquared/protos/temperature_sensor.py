"""This protocol specifies the interface that any temperature sensor implementation
must adhere to, ensuring consistent behavior across different temperature sensor
hardware.
"""

from ..sensor_reading.temperature import Temperature


class TemperatureSensorProto:
    """Protocol defining the interface for a temperature sensor."""

    def get_temperature(self) -> Temperature:
        """Gets the temperature reading of the sensor.

        Returns:
            A Temperature object containing the temperature in degrees Celsius.

        Raises:
            SensorReadingValueError: If the reading returns an invalid value.
            SensorReadingTimeoutError: If the reading times out.
            SensorReadingUnknownError: If an unknown error occurs while reading the temperature
        """
        ...
