class LoadSwitchManagerProto:
    def get_state(self, load_switch_id : int) -> bool:
        """Get the state of a load switch.
        :param int load_switch_id: The ID of the load switch.
        :param str load_switch_id: The ID of the load switch.
        :return: True if the load switch is on, False if it is off.
        :rtype: bool
        """
        ...
    def set_state(self, load_switch_id:int, state: bool) -> None:
        """Set the state of a load switch.
        :param int load_switch_id: The ID of the load switch.
        :param str load_switch_id: The ID of the load switch.
        :param bool state: True to turn on the load switch, False to turn it off.
        """
        ...
    