"""This protocol specifies the interface that any burnwire implementation must adhere
to, ensuring consistent behavior across different burnwire hardware.
"""


class BurnwireProto:
    """Protocol defining the interface for a burnwire port."""

    def burn(self, timeout_duration: float) -> bool:
        """Fires the burnwire for a specified amount of time.

        Args:
            timeout_duration: The maximum amount of time to keep the burnwire on.

        Returns:
            True if the burn occurred successfully, False otherwise.

        Raises:
            Exception: If there is an error toggling the burnwire pins.
        """
        ...
