"""This module defines the TemperatureSensorProto protocol for temperature sensors.

This protocol specifies the interface that any temperature sensor implementation
must adhere to, ensuring consistent behavior across different temperature sensor
hardware.

Usage:
    # This is a protocol class and should not be instantiated directly.
    # Implementations of this protocol should be used instead.
"""


class TemperatureSensorProto:
    """Protocol defining the interface for a temperature sensor."""

    def get_temperature(self) -> float | None:
        """Gets the temperature reading of the sensor.

        Returns:
            The temperature in degrees Celsius, or None if not available.
        """
        ...
