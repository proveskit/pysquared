"""
Protocol defining the interface for a solar panel.
"""


class SolarPanelProto:
    def get_temperature(self) -> float:
        """Gets the current temperature of the solar panel

        :return: The current temperature of the solar panel
        :rtype: float
        """
        ...

    def get_light_level(self) -> float:
        """Gets the current light level of the solar panel

        :return: The current light level of the solar panel
        :rtype: float
        """
        ...

    def drive_torque_coils(self, *kwargs) -> bool:
        """Drives the torque coils

        :return: A Boolean indicating whether the torque coils were driven successfully
        :rtype: bool

        :raises NotImplementedError: If not implemented by subclass.
        """
        ...
