"""
Protocol defining the interface for a radio.
"""

from ..config.radio import RadioConfig
from ..hardware.radio.modulation import RadioModulation

# Type hinting only
try:
    from typing import Optional, Type
except ImportError:
    pass


class RadioProto:
    def send(self, data: bytes) -> bool:
        """Send data over the radio.

        :param bytes data: The data to send.
        :return: True if the send was successful.
        :rtype: bool
        """
        ...

    def set_modulation(self, modulation: Type[RadioModulation]) -> None:
        """Request a change in the radio modulation mode.
        This change might take effect immediately or after a reset, depending on implementation.

        :param RadioModulation modulation: The desired modulation mode.
        """
        ...

    def get_modulation(self) -> Type[RadioModulation]:
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

    def modify_config(self, radio_config: RadioConfig) -> None:
        """Modify the radio configuration. This will apply any new configuration options during runtime.

        :param RadioConfig radio_config: The new radio configuration.
        """
        ...

    def get_max_packet_size(self) -> int:
        """Get the maximum packet size supported by the radio.

        :return: The maximum packet size in bytes.
        :rtype: int
        """
        ...
