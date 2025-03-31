from .logger import Logger
from .packet_manager import PacketManager
from .protos.radio import RadioProto

try:
    from typing import Union
except Exception:
    pass


class PacketSender:
    def __init__(
        self,
        logger: Logger,
        radio: RadioProto,
        packet_manager: PacketManager,
        ack_timeout: float = 2.0,
        max_retries: int = 3,
        send_delay: float = 0.2,
    ) -> None:
        """
        Initialize the packet sender with optimized timing
        """
        self.logger: Logger = logger
        self.radio: RadioProto = radio
        self.packet_manager: PacketManager = packet_manager
        self.ack_timeout: float = ack_timeout
        self.max_retries: int = max_retries
        self.send_delay: float = send_delay

    def wait_for_ack(self, expected_seq: int) -> bool:
        """
        Optimized ACK wait with early return
        """
        import time

        start_time: float = time.monotonic()

        # Minimal delay after sending
        time.sleep(self.send_delay)

        while (time.monotonic() - start_time) < self.ack_timeout:
            packet: bytearray = self.radio.radio.receive()

            if packet and self.packet_manager.is_ack_packet(packet):
                ack_seq: Union[int, None] = self.packet_manager.get_ack_seq_num(packet)
                if ack_seq == expected_seq:
                    # Got our ACK - only wait briefly for a duplicate then continue
                    time.sleep(0.2)
                    return True

            time.sleep(0.1)  # Small delay between checks

        return False

    def send_packet_with_retry(self, packet: bytes, seq_num: int) -> bool:
        """Optimized packet sending with minimal delays"""
        import time

        for attempt in range(self.max_retries):
            self.radio.send(packet)

            if self.wait_for_ack(seq_num):
                # Success - minimal delay before next packet
                time.sleep(0.2)
                return True

            if attempt < self.max_retries - 1:
                # Only short delay before retry
                time.sleep(1.0)

        return False

    def send_data(
        self, data: Union[str, bytearray], progress_interval: int = 10
    ) -> bool:
        """Send data with minimal progress updates"""
        packets: list[bytes] = self.packet_manager.pack_data(data)
        total_packets: int = len(packets)
        self.logger.info("Sending packets...", num_packets=total_packets)

        for i, packet in enumerate(packets):
            if i % progress_interval == 0:
                self.logger.info(
                    "Making progress sending packets",
                    current_packet=i,
                    num_packets=total_packets,
                )

            if not self.send_packet_with_retry(packet, i):
                self.logger.warning(
                    "Failed to send packet", current_packet=i, num_packets=total_packets
                )
                return False

        self.logger.info(
            "Successfully sent all the packets!", num_packets=total_packets
        )
        return True

    def handle_retransmit_request(
        self, packets: list[bytes], request_packet: list[str]
    ) -> bool:
        """Handle retransmit request by sending requested packets"""
        import time

        try:
            missing_packets: list[int] = self.packet_manager.parse_retransmit_request(
                request_packet
            )
            self.logger.info(
                "Retransmit request received for missing packets",
                num_missing_packets=len(missing_packets),
            )
            time.sleep(0.2)  # Small delay before retransmission

            for seq in missing_packets:
                if seq < len(packets):
                    self.logger.info("Retransmitting packet ", packet=seq)
                    self.radio.send(packets[seq])
                    time.sleep(0.2)  # Small delay between retransmitted packets
                    self.radio.send(packets[seq])
                    time.sleep(0.2)  # Small delay between retransmitted packets

            return True

        except Exception as e:
            self.logger.error("Error handling retransmit request", e)
            return False

    def fast_send_data(
        self,
        data: Union[str, bytearray],
        send_delay: float = 0.5,
        retransmit_wait: float = 15.0,
    ) -> bool:
        """Send data with improved retransmission handling"""
        import time

        packets: list[bytes] = self.packet_manager.pack_data(data)
        total_packets: int = len(packets)
        self.logger.info("Sending packets..", num_packets=total_packets)

        # Send first packet with retry until ACKed
        for attempt in range(self.max_retries):
            self.logger.info(
                "Sending first packet",
                attempt_num=attempt + 1,
                max_retries=self.max_retries,
            )
            self.radio.send(packets[0])

            if self.wait_for_ack(0):
                break
            else:
                if attempt < self.max_retries - 1:
                    time.sleep(1.0)
                else:
                    self.logger.warning("Failed to get ACK for first packet")
                    return False

        # Send remaining packets without waiting for ACKs
        self.logger.info("Sending remaining packets...")
        for i in range(1, total_packets):
            if i % 10 == 0:
                self.logger.info(
                    "Sending packet", current_packet=i, num_packets=total_packets
                )
            self.radio.send(packets[i])
            time.sleep(send_delay)

        self.logger.info("Waiting for retransmit requests...")
        retransmit_end_time: float = time.monotonic() + retransmit_wait

        while time.monotonic() < retransmit_end_time:
            packet: bytearray = self.radio.radio.receive()
            if not packet:
                break

            self.logger.info(
                "Received potential retransmit request:",
                packet=[hex(b) for b in packet],
            )

            if not self.packet_manager.is_retransmit_request(packet):
                break

            self.logger.info("Valid retransmit request received!")
            missing_packets = self.packet_manager.parse_retransmit_request(packet)
            self.logger.info("Retransmitting packets", missing_packets=missing_packets)

            # Add delay before retransmission to let receiver get ready
            time.sleep(1)

            for seq in missing_packets:
                if seq >= len(packets):
                    break

                self.logger.info("Retransmitting packet", packet=seq)
                self.radio.send(packets[seq])
                time.sleep(0.5)  # Longer delay between retransmitted packets
                self.logger.info("Retransmitting packet", packet=seq)
                self.radio.send(packets[seq])
                time.sleep(0.2)  # Longer delay between retransmitted packets

            # Reset timeout and add extra delay after retransmission
            time.sleep(1.0)
            retransmit_end_time: float = time.monotonic() + retransmit_wait

            time.sleep(0.1)

        self.logger.info("Finished sending all packets")
        return True
