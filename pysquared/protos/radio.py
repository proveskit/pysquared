"""This protocol specifies the interface that any radio implementation must adhere
to, ensuring consistent behavior across different radio hardware.
"""

from ..hardware.radio.modulation import RadioModulation

# Type hinting only
try:
    from typing import Optional, Type
except ImportError:
    pass


class RadioProto:
    """Protocol defining the interface for a radio."""

    def send(self, data: bytes) -> bool:
        """Sends data over the radio.

        Args:
            data: The data to send.

        Returns:
            True if the send was successful, False otherwise.
        """
        ...

    def set_modulation(self, modulation: Type[RadioModulation]) -> None:
        """Requests a change in the radio modulation mode.

        This change might take effect immediately or after a reset, depending on
        implementation.

        Args:
            modulation: The desired modulation mode.
        """
        ...

    def get_modulation(self) -> Type[RadioModulation]:
        """Gets the currently configured or active radio modulation mode.

        Returns:
            The current modulation mode.
        """
        ...

    def receive(self, timeout: Optional[int] = None) -> Optional[bytes]:
        """Receives data from the radio.

        Args:
            timeout: Optional receive timeout in seconds. If None, use the default timeout.

        Returns:
            The received data as bytes, or None if no data was received.
        """
        ...

    def modify_config(self, key: str, value) -> None:
        """Modifies a specific radio configuration parameter.

        Args:
            key (str): The configuration parameter key to modify.
            value: The new value to set for the parameter.

        Raises:
            NotImplementedError: If not implemented by subclass.
        """

        ...

    def get_rssi(self) -> int:
        """Gets the RSSI of the last received packet.

        Returns:
            The RSSI value in dBm.

        Raises:
            NotImplementedError: If not implemented by subclass.
        """

        ...

    def get_max_packet_size(self) -> int:
        """Gets the maximum packet size supported by the radio.

        Returns:
            The maximum packet size in bytes.
        """
        ...
