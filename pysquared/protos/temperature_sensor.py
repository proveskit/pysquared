"""
Protocol defining the interface for a temperature sensor.
"""


class TemperatureSensorProto:
    def get_temperature(self) -> float | None:
        """Get the temperature reading of the sensor.

        :return: The temperature in degrees Celsius or None if not available.
        :rtype: float | None
        """
        ...
