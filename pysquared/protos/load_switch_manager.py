"""
Protocol defining the interface for a group of load switches.
"""


class LoadSwtichManagerProto:
    def get_state(self, load_switch_id: int) -> bool:
        """Gets the current state of the load switch.

        :param int load_switch_id: The ID of the load switch to query.

        :return: A Boolean indicating whether the load switch is on (True) or off (False).
        :rtype: bool

        :raises Exception: If there is an error reading the load switch state.
        """
        ...

    def set_state(self, load_switch_id: int, state: bool) -> None:
        """Sets the state of the load switch.

        :param int load_switch_id: The ID of the load switch to control.
        :param bool state: The desired state of the load switch (True for on, False for off).

        :raises Exception: If there is an error setting the load switch state.
        """
        ...
