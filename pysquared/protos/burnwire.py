"""
Protocol defining the interface for a burnwire port.
"""


class BurnwireProto:
    def burn(self, timeout_duration: float, max_retries: int) -> bool:
        """Fires the burnwire for a specified ammount of time

        :param float timeout_duration: The max ammount of time to keep the burnwire on for.
        :param int max_retries: The maximum number of times the burnwire is allowed to retry before exitng.

        :return: A Boolean indicating whether the burn occured sucessfully
        :rtype: bool

        :raises Exception: If there is an error toggling the burnwire pins.
        """
        ...

    def smart_burn(self, max_retries: int, timeout_duration: float) -> bool:
        """Fires the burnwire and uses a deployment sensor

        :param int max_retries: The maximum number of times the burnwire is allowed to retry before exitng.
        :param float timeout_duration: The max time to keep the burnwire on for if the deployment sensor doesn't detect deployment.

        :return: A Boolean indicating whether the burn occured sucessfully
        :rtype: bool

        :raises Exception: If there is an error toggling the burnwire pins.
        """
        ...
