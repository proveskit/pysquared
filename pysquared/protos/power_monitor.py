"""This protocol specifies the interface that any power monitor implementation must
adhere to, ensuring consistent behavior across different power monitor hardware.
"""


class PowerMonitorProto:
    """Protocol defining the interface for a Power Monitor."""

    def get_bus_voltage(self) -> float | None:
        """Gets the bus voltage from the power monitor.

        Returns:
            The bus voltage in volts, or None if not available.
        """
        ...

    def get_shunt_voltage(self) -> float | None:
        """Gets the shunt voltage from the power monitor.

        Returns:
            The shunt voltage in volts, or None if not available.
        """
        ...

    def get_current(self) -> float | None:
        """Gets the current from the power monitor.

        Returns:
            The current in amps, or None if not available.
        """
        ...
