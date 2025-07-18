"""This module provides a PacketManager for sending and receiving data over a radio.

This module handles the fragmentation and reassembly of data into packets for
transmission over a radio. It also provides methods for sending and receiving
acknowledgments.

**Usage:**
```python
logger = Logger()
radio = RFM9xManager(logger, radio_config, spi, cs, reset)
packet_manager = PacketManager(logger, radio, "my_license_key")
packet_manager.send(b"Hello world!")
received_data = packet_manager.listen()
```
"""

import math
import time

from ....logger import Logger
from ....nvm.counter import Counter
from ....protos.radio import RadioProto

try:
    from typing import Optional
except ImportError:
    pass


class PacketManager:
    """Manages the sending and receiving of data packets over a radio."""

    def __init__(
        self,
        logger: Logger,
        radio: RadioProto,
        license: str,
        message_counter: Counter,
        send_delay: float = 0.2,
    ) -> None:
        """Initializes the PacketManager.

        Args:
            logger: The logger to use.
            radio: The radio instance to use for communication.
            license: The license key for sending data.
            send_delay: The delay between sending packets.
        """
        self._logger: Logger = logger
        self._radio: RadioProto = radio
        self._send_delay: float = send_delay
        self._license: str = license
        # 1 byte for packet identifier, 2 bytes for sequence number, 2 for total packets, 1 for rssi
        self._header_size: int = 6
        self._payload_size: int = radio.get_max_packet_size() - self._header_size
        self._message_counter: Counter = message_counter

    def send(self, data: bytes) -> bool:
        """Sends data over the radio.

        Args:
            data: The data to send.

        Returns:
            True if the data was sent successfully, False otherwise.
        """
        if self._license == "":
            self._logger.warning("License is required to send data")
            return False

        packets: list[bytes] = self._pack_data(data)
        total_packets: int = len(packets)
        self._logger.debug("Sending packets...", num_packets=total_packets)

        for packet in packets:
            self._radio.send(packet)

            # Only add send delay if there are multiple packets
            if len(packets) > 1:
                time.sleep(self._send_delay)

        self._logger.debug(
            "Successfully sent all the packets!", num_packets=total_packets
        )
        return True

    def _pack_data(self, data: bytes) -> list[bytes]:
        """Packs input data into a list of packets ready for transmission.

        Each packet includes:
        - 1 byte: packet identifier
        - 2 bytes: sequence number (0-based)
        - 2 bytes: total number of packets
        - 1 byte: RSSI
        - remaining bytes: payload

        Args:
            data: The data to pack.

        Returns:
            A list of packets.
        """
        # Calculate number of packets needed
        total_packets: int = math.ceil(len(data) / self._payload_size)
        self._logger.debug(
            "Packing data into packets",
            num_packets=total_packets,
            data_length=len(data),
        )

        packet_identifier: int = self._get_packet_identifier()

        packets: list[bytes] = []
        for sequence_number in range(total_packets):
            # Create header
            header: bytes = (
                packet_identifier.to_bytes(1, "big")
                + sequence_number.to_bytes(2, "big")
                + total_packets.to_bytes(2, "big")
                + abs(self._radio.get_rssi()).to_bytes(1, "big")
            )

            # Get payload slice for this packet
            start: int = sequence_number * self._payload_size
            end: int = start + self._payload_size
            payload: bytes = data[start:end]

            # Combine header and payload
            packet: bytes = header + payload
            packets.append(packet)

        return packets

    def listen(self, timeout: Optional[int] = None) -> bytes | None:
        """Listens for data from the radio.

        Args:
            timeout: Optional receive timeout in seconds. If None, use the default timeout.

        Returns:
            The received data as bytes, or None if no data was received.
        """
        _timeout = timeout if timeout is not None else 10

        self._logger.debug("Listening for data...", timeout=_timeout)

        start_time = time.time()
        received_packets = []

        # Keep receiving until timeout or we have all packets
        while True:
            # Stop listening if timeout is reached
            if time.time() - start_time > _timeout:
                self._logger.debug(
                    "Listen timeout reached",
                    elapsed=time.time() - start_time,
                )
                return

            # Try to receive a packet
            packet = self._radio.receive(_timeout)

            # If no packet received, continue waiting
            if packet is None:
                continue

            packet_identifier, _, total_packets, _ = self._get_header(packet)

            # Log received packets
            self._logger.debug(
                "Received packet",
                packet_length=len(packet),
                header=self._get_header(packet),
                payload=self._get_payload(packet),
            )

            if received_packets:
                (
                    first_packet_identifier,
                    _,
                    _,
                    _,
                ) = self._get_header(received_packets[0])
                if packet_identifier != first_packet_identifier:
                    continue

            received_packets.append(packet)

            # Check if we have all packets
            if total_packets == len(received_packets):
                self._logger.debug(
                    "Received all expected packets", received=total_packets
                )
                break

        # Attempt to unpack the data
        return self._unpack_data(received_packets)

    def send_acknowledgement(self) -> None:
        """Sends an acknowledgment to the radio."""
        self.send(b"ACK")
        self._logger.debug("Sent acknowledgment packet")

    def _unpack_data(self, packets: list[bytes]) -> bytes:
        """Unpacks a list of packets and reassembles the original data.

        Args:
            packets: A list of packets.

        Returns:
            The reassembled data.
        """
        sorted_packets: list = sorted(
            packets, key=lambda p: int.from_bytes(p[1:3], "big")
        )

        return b"".join(self._get_payload(packet) for packet in sorted_packets)

    def _get_header(self, packet: bytes) -> tuple[int, int, int, int]:
        """Returns the sequence number, total packets, and RSSI stored in the header.

        Args:
            packet: The packet to extract the header from.

        Returns:
            A tuple containing the sequence number, total packets, and RSSI.
        """
        return (
            int.from_bytes(packet[0:1], "big"),  # packet identifier
            int.from_bytes(packet[1:3], "big"),  # sequence number
            int.from_bytes(packet[3:5], "big"),  # total packets
            -int.from_bytes(packet[5:6], "big"),  # RSSI
        )

    def _get_payload(self, packet: bytes) -> bytes:
        """Returns the payload of the packet.

        Args:
            packet: The packet to extract the payload from.

        Returns:
            The payload of the packet.
        """
        return packet[self._header_size :]

    def _get_packet_identifier(self) -> int:
        """Increments message_counter and returns the current identifier for a packet"""
        self._message_counter.increment()
        return self._message_counter.get()
