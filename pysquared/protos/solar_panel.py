"""
Protocol defining the interface for a solar panel.
"""


class SolarPanelProto:
    def get_temperature(self) -> float | None:
        """Gets the current temperature of the solar panel

        :return: The current temperature of the solar panel or None if sensor unavailable/failed
        :rtype: float | None
        """
        ...

    def get_light_level(self) -> float | None:
        """Gets the current light level of the solar panel

        :return: The current light level of the solar panel or None if sensor unavailable/failed
        :rtype: float | None
        """
        ...

    def get_all_data(self) -> tuple[float | None, float | None]:
        """Gets all the data from the solar panel

        :return: A tuple containing the temperature and light level of the solar panel
        :rtype: tuple[float | None, float | None]
        """
        ...

    def drive_torque_coils(self, **kwargs) -> bool:
        """Drives the torque coils

        :return: A Boolean indicating whether the torque coils were driven successfully
        :rtype: bool

        :raises NotImplementedError: If not implemented by subclass.
        """
        ...

    def get_sensor_states(self) -> dict:
        """Gets the current state of the sensors on the solar panel

        :return: A dictionary containing the states of the sensors on the solar panel
        :rtype: dict
        """
        ...

    def get_error_count(self) -> int:
        """Gets the number of errors that have occurred on the solar panel since the last reset

        :return: The number of errors that have occurred on the solar panel since the last reset
        :rtype: int
        """
        ...
