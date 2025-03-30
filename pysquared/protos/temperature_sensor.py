"""
Protocol defining the interface for a temperature sensor.
"""


class TemperatureSensorProto:
    def get_temperature(self) -> float:
        """Get the temperature reading of the sensor.

        :return: The temperature in degrees Celsius.
        :rtype: float

        :raises RuntimeError: If the temperature reading fails.
        """
        ...
