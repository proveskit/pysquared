"""This protocol specifies the interface that any power monitor implementation must
adhere to, ensuring consistent behavior across different power monitor hardware.
"""

from ..sensor_reading.current import Current
from ..sensor_reading.voltage import Voltage


class PowerMonitorProto:
    """Protocol defining the interface for a Power Monitor."""

    def get_bus_voltage(self) -> Voltage:
        """Gets the bus voltage from the power monitor.

        Returns:
            A Voltage object containing the bus voltage in volts.

        Raises:
            SensorReadingValueError: If the reading returns an invalid value.
            SensorReadingTimeoutError: If the reading times out.
            SensorReadingUnknownError: If an unknown error occurs while reading the light sensor.
        """
        ...

    def get_shunt_voltage(self) -> Voltage:
        """Gets the shunt voltage from the power monitor.

        Returns:
            A Voltage object containing the shunt voltage in volts.

        Raises:
            SensorReadingValueError: If the reading returns an invalid value.
            SensorReadingTimeoutError: If the reading times out.
            SensorReadingUnknownError: If an unknown error occurs while reading the light sensor.
        """
        ...

    def get_current(self) -> Current:
        """Gets the current from the power monitor.

        Returns:
            A Current object containing the current in milliamps (mA)

        Raises:
            SensorReadingValueError: If the reading returns an invalid value.
            SensorReadingTimeoutError: If the reading times out.
            SensorReadingUnknownError: If an unknown error occurs while reading the light sensor.
        """
        ...
