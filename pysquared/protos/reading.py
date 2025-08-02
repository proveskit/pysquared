"""This protocol specifies the interface that any sensor reading protocol implementation must
adhere to, ensuring consistent behavior across different types of sensor readings.
"""

try:
    from typing import Tuple
except ImportError:
    pass


class ReadingProto:
    """Protocol defining the interface for a sensor reading."""

    @property
    def timestamp(self) -> float:
        """Gets the timestamp of the reading.

        Returns:
            The timestamp of the reading in seconds since the epoch.
        """
        ...

    @property
    def value(self) -> Tuple[float, float, float] | float:
        """Gets the bus voltage from the power monitor.

        Returns:
            A Voltage object containing the bus voltage in volts.

        Raises:
            SensorReadingValueError: If the reading returns an invalid value.
            SensorReadingTimeoutError: If the reading times out.
            SensorReadingUnknownError: If an unknown error occurs while reading the light sensor.
        """
        ...
