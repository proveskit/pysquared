"""
Protocol defining the interface for a burnwire port.
"""


class BurnwireProto:
    def burn(self, timeout_duration: float, max_retries: int) -> bool:
        """Fires the burnwire for a specified amount of time

        :param float timeout_duration: The max amount of time to keep the burnwire on for.
        :param int max_retries: The maximum number of times the burnwire is allowed to retry before exiting.

        :return: A Boolean indicating whether the burn occurred successfully
        :rtype: bool

        :raises Exception: If there is an error toggling the burnwire pins.
        """
        ...
