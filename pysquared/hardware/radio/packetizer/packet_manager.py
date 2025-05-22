import time

from ....logger import Logger
from ....protos.radio import RadioProto


class PacketManager:
    def __init__(
        self,
        logger: Logger,
        radio: RadioProto,
        license: str,
        send_delay: float = 0.2,
    ) -> None:
        """Initialize the packet manager with maximum packet size"""
        self.logger: Logger = logger
        self.radio: RadioProto = radio
        self.send_delay: float = send_delay
        self.license: str = license
        self.header_size: int = 4  # 2 bytes for sequence number, 2 for total packets
        self.payload_size: int = radio.get_max_packet_size() - self.header_size

    def send(self, data: bytes) -> bool:
        """Send data"""
        licensed_data: bytes = self.license.encode() + data
        packets: list[bytes] = self._pack_data(licensed_data)
        total_packets: int = len(packets)
        self.logger.info("Sending packets...", num_packets=total_packets)

        for i, packet in enumerate(packets):
            if i % 10 == 0:
                self.logger.info(
                    "Making progress sending packets",
                    current_packet=i,
                    num_packets=total_packets,
                )

            self.radio.send(packet)
            time.sleep(self.send_delay)

        self.logger.info(
            "Successfully sent all the packets!", num_packets=total_packets
        )
        return True

    def _pack_data(self, data: bytes) -> list[bytes]:
        """
        Takes input data and returns a list of packets ready for transmission
        Each packet includes:
        - 2 bytes: sequence number (0-based)
        - 2 bytes: total number of packets
        - remaining bytes: payload
        """
        # Calculate number of packets needed
        total_packets: int = (len(data) + self.payload_size - 1) // self.payload_size
        self.logger.info(
            "Packing data into packets",
            num_packets=total_packets,
            data_length=len(data),
        )

        packets: list[bytes] = []
        for sequence_number in range(total_packets):
            # Create header
            header: bytes = sequence_number.to_bytes(2, "big") + total_packets.to_bytes(
                2, "big"
            )
            self.logger.info("Created header", header=[hex(b) for b in header])

            # Get payload slice for this packet
            start: int = sequence_number * self.payload_size
            end: int = start + self.payload_size
            payload: bytes = data[start:end]

            # Combine header and payload
            packet: bytes = header + payload
            self.logger.info(
                "Combining the header and payload to form a Packet",
                packet=sequence_number,
                packet_length=len(packet),
                header=[hex(b) for b in header],
            )
            packets.append(packet)

        return packets

    # I don't think this will work because it doesn't gather packet, it only listens for a small time
    # needs to expect a total number of packets and wait for them
    # def receive(self) -> bytes | None:
    #     """Receive data and reassemble it from packets"""
    #     self.logger.info("Receiving data...")
    #     packets: list[bytes] = []

    #     attempts: int = 0
    #     while attempts < 5:
    #         packet: bytes | None = self.radio.receive()
    #         if packet is None:
    #             break
    #         packets.append(packet)

    #     data: bytes | None = self._unpack_data(packets)
    #     if data is None:
    #         self.logger.warning("Failed to unpack data from received packets")
    #         return None

    #     self.logger.info("Successfully unpacked data", data_length=len(data))
    #     return data

    # def _unpack_data(self, packets: list[bytes]) -> bytes | None:
    #     """
    #     Takes a list of packets and reassembles the original data
    #     Returns None if packets are missing or corrupted
    #     """
    #     if not packets:
    #         return None

    #     # Sort packets by sequence number
    #     try:
    #         sorted_packets: list = sorted(
    #             packets, key=lambda p: int.from_bytes(p[:2], "big")
    #         )
    #     except Exception:
    #         return None

    #     # Verify all packets are present
    #     total_packets: int = int.from_bytes(sorted_packets[0][2:4], "big")
    #     if len(sorted_packets) != total_packets:
    #         return None

    #     # Verify sequence numbers are consecutive
    #     for i, packet in enumerate(sorted_packets):
    #         if int.from_bytes(packet[:2], "big") != i:
    #             return None

    #     # Combine payloads
    #     data: bytes = b"".join(packet[self.header_size :] for packet in sorted_packets)
    #     return data
