"""
Protocol defining the interface for a radio.
"""

# Type hinting only
try:
    from typing import Any, Optional

    from ..hardware.radio.modulation import RadioModulation
except ImportError:
    pass


class RadioProto:
    async def send(self, data: Any) -> bool:
        """Send data over the radio.

        :param Any data: The data to send.
        :return: True if the send was successful (e.g., ACK received if applicable), False otherwise.
        :rtype: bool
        """
        ...

    def set_modulation(self, modulation: RadioModulation) -> None:
        """Request a change in the radio modulation mode.
        This change might take effect immediately or after a reset, depending on implementation.

        :param RadioModulation modulation: The desired modulation mode.
        """
        ...

    def get_modulation(self) -> RadioModulation:
        """Get the currently configured or active radio modulation mode.

        :return: The current modulation mode.
        :rtype: RadioModulation
        """
        ...

    def receive(self, timeout: Optional[int] = None) -> Optional[bytes]:
        """Receive data from the radio.

        :param int | None timeout: Optional receive timeout in seconds. If None, use the default timeout.
        :return: The received data as bytes, or None if no data was received.
        :rtype: Optional[bytes]
        """
        ...
