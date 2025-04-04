"""
Protocol defining the interface for a Power Monitor.
"""


class PowerMonitorProto:
    def get_bus_voltage(self) -> float | None:
        """Get the bus voltage from the power monitor.

        :return: The bus voltage in volts or None if not available.
        :rtype: float | None

        :raises Exception: If there is an error retrieving the value.
        """
        ...

    def get_shunt_voltage(self) -> float | None:
        """Get the shunt voltage from the power monitor.

        :return: The shunt voltage in volts or None if not available.
        :rtype: float | None

        :raises Exception: If there is an error retrieving the value.
        """
        ...

    def get_current(self) -> float | None:
        """Get the current from the power monitor.

        :return: The current in amps or None if not available.
        :rtype: float | None

        :raises Exception: If there is an error retrieving the value.
        """
        ...
