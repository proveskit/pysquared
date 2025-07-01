"""
Protocol defining the interface for load switch management.
"""

from typing import Dict


class LoadSwitchProto:
    """Protocol defining the interface for load switch management."""

    def turn_on(self, switch_name: str) -> bool:
        """Turn on a specific load switch.

        :param str switch_name: The name of the load switch to turn on.

        :return: A Boolean indicating whether the operation was successful
        :rtype: bool

        :raises Exception: If there is an error toggling the load switch.
        """
        ...

    def turn_off(self, switch_name: str) -> bool:
        """Turn off a specific load switch.

        :param str switch_name: The name of the load switch to turn off.

        :return: A Boolean indicating whether the operation was successful
        :rtype: bool

        :raises Exception: If there is an error toggling the load switch.
        """
        ...

    def turn_all_on(self) -> bool:
        """Turn on all load switches.

        :return: A Boolean indicating whether the operation was successful
        :rtype: bool

        :raises Exception: If there is an error toggling the load switches.
        """
        ...

    def turn_all_off(self) -> bool:
        """Turn off all load switches.

        :return: A Boolean indicating whether the operation was successful
        :rtype: bool

        :raises Exception: If there is an error toggling the load switches.
        """
        ...

    def get_switch_state(self, switch_name: str) -> bool | None:
        """Get the current state of a specific load switch.

        :param str switch_name: The name of the load switch to check.

        :return: The current state of the load switch (True for on, False for off) or None if not found
        :rtype: bool | None
        """
        ...

    def get_all_states(self) -> Dict[str, bool]:
        """Get the current state of all load switches.

        :return: A dictionary mapping switch names to their current states
        :rtype: Dict[str, bool]
        """
        ...
