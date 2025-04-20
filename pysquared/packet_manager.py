from .logger import Logger


class PacketManager:
    def __init__(self, logger: Logger, max_packet_size: int = 128) -> None:
        """Initialize the packet manager with maximum packet size (default 128 bytes for typical LoRa)"""
        self.max_packet_size: int = max_packet_size
        self.header_size: int = 4  # 2 bytes for sequence number, 2 for total packets
        self.payload_size: int = max_packet_size - self.header_size
        self.logger: Logger = logger

    def create_retransmit_request(self, missing_packets: list[int]) -> bytes:
        """
        Create a packet requesting retransmission
        Format:
        - 2 bytes: 0xFFFF (special sequence number indicating retransmit request)
        - 2 bytes: Number of missing packets
        - Remaining bytes: Missing packet sequence numbers
        """
        header: bytes = b"\xff\xff" + len(missing_packets).to_bytes(2, "big")
        payload: bytes = b"".join(
            sequence_number.to_bytes(2, "big") for sequence_number in missing_packets
        )
        return header + payload

    def is_retransmit_request(self, packet: bytes) -> bool:
        """Check if packet is a retransmit request"""
        return len(packet) >= 4 and packet[:2] == b"\xff\xff"

    def parse_retransmit_request(self, packet: bytes) -> list[int]:
        """Extract missing packet numbers from retransmit request"""
        num_missing: int = int.from_bytes(packet[2:4], "big")
        missing: list[int] = []
        for i in range(num_missing):
            start_idx: int = 4 + (i * 2)
            sequence_number: int = int.from_bytes(
                packet[start_idx : start_idx + 2], "big"
            )
            missing.append(sequence_number)
        return missing

    def pack_data(self, data: object) -> list[bytes]:
        """
        Takes input data and returns a list of packets ready for transmission
        Each packet includes:
        - 2 bytes: sequence number (0-based)
        - 2 bytes: total number of packets
        - remaining bytes: payload
        """
        packed_data: bytes = bytes()

        # Convert data to bytes if it isn't already
        if not isinstance(data, bytes):
            if isinstance(data, str):
                packed_data = data.encode("utf-8")
            else:
                packed_data = str(data).encode("utf-8")

        # Calculate number of packets needed
        total_packets: int = (
            len(packed_data) + self.payload_size - 1
        ) // self.payload_size
        self.logger.info(
            "Packing data into packets",
            num_packets=total_packets,
            data_length=len(packed_data),
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
            payload: bytes = packed_data[start:end]

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

    def unpack_data(self, packets: list) -> bytes | None:
        """
        Takes a list of packets and reassembles the original data
        Returns None if packets are missing or corrupted
        """
        if not packets:
            return None

        # Sort packets by sequence number
        try:
            sorted_packets: list = sorted(
                packets, key=lambda p: int.from_bytes(p[:2], "big")
            )
        except Exception:
            return None

        # Verify all packets are present
        total_packets: int = int.from_bytes(sorted_packets[0][2:4], "big")
        if len(sorted_packets) != total_packets:
            return None

        # Verify sequence numbers are consecutive
        for i, packet in enumerate(sorted_packets):
            if int.from_bytes(packet[:2], "big") != i:
                return None

        # Combine payloads
        data: bytes = b"".join(packet[self.header_size :] for packet in sorted_packets)
        return data

    def create_ack_packet(self, sequence_number: int) -> bytes:
        """Creates an acknowledgment packet for a given sequence number"""
        return b"ACK" + sequence_number.to_bytes(2, "big")

    def is_ack_packet(self, packet: bytes) -> bool:
        """Checks if a packet is an acknowledgment packet"""
        return packet.startswith(b"ACK")

    def get_ack_seq_num(self, ack_packet: bytes) -> int | None:
        """Extracts sequence number from an acknowledgment packet"""
        if self.is_ack_packet(ack_packet):
            return int.from_bytes(ack_packet[3:5], "big")
        return None
