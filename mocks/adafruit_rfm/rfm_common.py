"""Mock for the Adafruit RFM SPI interface.

This module provides a mock implementation of the Adafruit RFM SPI interface for
testing purposes. It allows for simulating the behavior of the RFM SPI interface
without the need for actual hardware.
"""

from typing import Optional

from circuitpython_typing import ReadableBuffer


class RFMSPI:
    """A mock RFM SPI interface."""

    node: int
    destination: int

    def send(
        self,
        data: ReadableBuffer,
        *,
        keep_listening: bool = False,
        destination: Optional[int] = None,
        node: Optional[int] = None,
        identifier: Optional[int] = None,
        flags: Optional[int] = None,
    ) -> bool:
        """Sends data over the radio.

        Args:
            data: The data to send.
            keep_listening: Whether to keep listening after sending.
            destination: The destination node address.
            node: The source node address.
            identifier: The packet identifier.
            flags: The packet flags.

        Returns:
            True if the data was sent successfully, False otherwise.
        """
        ...

    def read_u8(self, address: int) -> int:
        """Reads a byte from the given address.

        Args:
            address: The address to read from.

        Returns:
            The byte read from the address.
        """
        ...

    def receive(
        self,
        *,
        keep_listening: bool = True,
        with_header: bool = False,
        timeout: Optional[float] = None,
    ) -> Optional[bytearray]:
        """Receives data from the radio.

        Args:
            keep_listening: Whether to keep listening after receiving.
            with_header: Whether to include the header in the received data.
            timeout: The timeout for receiving data.

        Returns:
            The received data, or None if no data was received.
        """
        ...
