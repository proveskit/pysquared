"""
Protocol defining the interface for a load switch controller.
"""


class LoadSwitchProto:
    def enable_load(self) -> bool:
        """Enables the load switch

        :return: A Boolean indicating whether the enable or disable command was successful
        :rtype: bool

        :raises Exception: If there is an error enabling the load switch.
        :raises NotImplementedError: If not implemented by subclass.
        """
        ...

    def disable_load(self) -> bool:
        """Disables the load switch

        :return: A Boolean indicating whether the enable or disable command was successful
        :rtype: bool

        :raises Exception: If there is an error disabling the load switch.
        :raises NotImplementedError: If not implemented by subclass.
        """
        ...

    def reset_load(self) -> bool:
        """Resets the load switch

        :return: A Boolean indicating whether the reset command was successful
        :rtype: bool

        :raises Exception: If there is an error resetting the load switch.
        :raises NotImplementedError: If not implemented by subclass.
        """
        ...

    def get_load_state(self) -> bool:
        """Gets the current state of the load switch

        :return: A Boolean indicating whether the load is enabled
        :rtype: bool

        :raises Exception: If there is an error reading the load switch state.
        :raises NotImplementedError: If not implemented by subclass.
        """
        ...
