"""
Protocol defining the interface for a burnwire port.
"""


class BurnwireProto:
    def burn(self, timeout_duration: float) -> bool:
        """Fires the burnwire for a specified amount of time

        :param float timeout_duration: The max amount of time to keep the burnwire on for.

        :return: A Boolean indicating whether the burn occurred successfully
        :rtype: bool

        :raises Exception: If there is an error toggling the burnwire pins.
        """
        ...
