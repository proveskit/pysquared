import random
from unittest.mock import MagicMock, patch

import pytest

from pysquared.hardware.radio.packetizer.packet_manager import PacketManager
from pysquared.logger import Logger
from pysquared.protos.radio import RadioProto


@pytest.fixture
def mock_logger() -> MagicMock:
    return MagicMock(spec=Logger)


@pytest.fixture
def mock_radio() -> MagicMock:
    radio = MagicMock(spec=RadioProto)
    radio.get_max_packet_size.return_value = 100  # Mock packet size for tests
    radio.get_rssi.return_value = 70  # Mock RSSI value
    return radio


def test_packet_manager_init(mock_logger, mock_radio):
    """Test PacketManager initialization."""
    license_str = "TEST_LICENSE"

    packet_manager = PacketManager(mock_logger, mock_radio, license_str, send_delay=0.5)

    assert packet_manager._logger is mock_logger
    assert packet_manager._radio is mock_radio
    assert packet_manager._license == license_str
    assert packet_manager._send_delay == 0.5
    assert packet_manager._header_size == 5
    assert packet_manager._payload_size == 95  # 100 - 5 header bytes


def test_pack_data_single_packet(mock_logger, mock_radio):
    """Test packing data that fits in a single packet."""
    license_str = "TEST"
    packet_manager = PacketManager(mock_logger, mock_radio, license_str)

    # Create test data that fits in a single packet
    test_data = b"Small test data"
    packets = packet_manager._pack_data(test_data)
    assert len(packets) == 1

    # Check packet structure
    packet = packets[0]
    assert len(packet) == len(test_data) + packet_manager._header_size

    # Check header
    sequence_number = int.from_bytes(packet[0:2], "big")
    total_packets = int.from_bytes(packet[2:4], "big")
    rssi = int.from_bytes(packet[4:5], "big")
    payload = packet[5:]

    assert sequence_number == 0
    assert total_packets == 1
    assert rssi == 70
    assert payload == test_data


def test_pack_data_multiple_packets(mock_logger, mock_radio):
    """Test packing data that requires multiple packets."""
    license_str = "TEST"
    packet_manager = PacketManager(mock_logger, mock_radio, license_str)

    # Create test data that requires multiple packets
    # With a payload size of 96, this will require 3 packets
    test_data = b"X" * 250
    packets = packet_manager._pack_data(test_data)
    assert len(packets) == 3

    # Check each packet
    reconstructed_data = b""

    for i, packet in enumerate(packets):
        sequence_number = int.from_bytes(packet[0:2], "big")
        total_packets = int.from_bytes(packet[2:4], "big")
        rssi = int.from_bytes(packet[4:5], "big")
        payload = packet[5:]

        assert sequence_number == i
        assert total_packets == 3
        assert rssi == 70
        reconstructed_data += payload

    # Verify the reconstructed data matches the original
    assert reconstructed_data == test_data


@patch("time.sleep")
def test_send_success(mock_sleep, mock_logger, mock_radio):
    """Test successful execution of send method."""
    license_str = "TEST"

    packet_manager = PacketManager(mock_logger, mock_radio, license_str, send_delay=0.1)

    # Create small test data
    test_data = b'{"message": "test beacon"}'
    _ = packet_manager.send(test_data)

    # Calculate number of packets that would be created
    total_packets = (
        len(test_data) + packet_manager._payload_size - 1
    ) // packet_manager._payload_size

    # Verify radio.send was called for each packet
    assert mock_radio.send.call_count == total_packets

    # Verify sleep was not called
    assert mock_sleep.call_count == 0

    # Verify log messages
    mock_logger.debug.assert_any_call("Sending packets...", num_packets=total_packets)
    mock_logger.debug.assert_any_call(
        "Successfully sent all the packets!", num_packets=total_packets
    )


@patch("time.sleep")
def test_send_success_multipacket(mock_sleep, mock_logger, mock_radio):
    """Test successful execution of send method."""
    license_str = "TEST"

    packet_manager = PacketManager(mock_logger, mock_radio, license_str, send_delay=0.1)

    # Create test data that requires multiple packets (> 252 bytes)
    test_data = bytes([random.randint(0, 255) for _ in range(300)])
    _ = packet_manager.send(test_data)

    # Calculate number of packets that would be created
    total_packets = (
        len(test_data) + packet_manager._payload_size - 1
    ) // packet_manager._payload_size

    # Verify radio.send was called for each packet
    assert mock_radio.send.call_count == total_packets

    # Verify sleep was called between packet sends with correct delay
    assert mock_sleep.call_count == total_packets
    mock_sleep.assert_called_with(0.1)

    # Verify log messages
    mock_logger.debug.assert_any_call("Sending packets...", num_packets=total_packets)
    mock_logger.debug.assert_any_call(
        "Successfully sent all the packets!", num_packets=total_packets
    )


def test_send_unlicensed(mock_logger, mock_radio):
    """Test unlicensed execution of send method."""
    license_str = ""

    packet_manager = PacketManager(mock_logger, mock_radio, license_str, send_delay=0.1)

    test_data = b"hello world"
    _ = packet_manager.send(test_data)

    # Verify log messages
    mock_logger.warning.assert_any_call("License is required to send data")


@patch("time.time")
def test_unpack_data(mock_time, mock_logger, mock_radio):
    """Test unpacking data from received packets."""
    packet_manager = PacketManager(mock_logger, mock_radio, "")

    # Create test packets with proper headers
    packet1 = (
        (0).to_bytes(2, "big")
        + (3).to_bytes(2, "big")
        + (70).to_bytes(1, "big")
        + b"first"
    )
    packet2 = (
        (1).to_bytes(2, "big")
        + (3).to_bytes(2, "big")
        + (70).to_bytes(1, "big")
        + b" second"
    )
    packet3 = (
        (2).to_bytes(2, "big")
        + (3).to_bytes(2, "big")
        + (70).to_bytes(1, "big")
        + b" third"
    )

    # Mix up the order to test sorting
    packets = [packet2, packet3, packet1]

    # Call _unpack_data directly
    result = packet_manager._unpack_data(packets)

    # Verify correct data reassembly
    expected_data = b"first second third"
    assert result == expected_data


@patch("time.time")
def test_receive_success(mock_time, mock_logger, mock_radio):
    """Test successfully receiving all packets."""
    packet_manager = PacketManager(mock_logger, mock_radio, "")

    # Set up mock time to control the flow
    mock_time.side_effect = [10.0, 10.1, 10.2, 10.3, 10.4]

    # Create test packets
    packet1 = (
        (0).to_bytes(2, "big")
        + (2).to_bytes(2, "big")
        + (70).to_bytes(1, "big")
        + b"first"
    )
    packet2 = None
    packet3 = (
        (1).to_bytes(2, "big")
        + (2).to_bytes(2, "big")
        + (70).to_bytes(1, "big")
        + b" second"
    )

    # Configure mock_radio.receive to return packets then None
    mock_radio.receive.side_effect = [packet1, packet2, packet3]

    # Call the receive method
    result = packet_manager.listen()

    # Check the result
    expected_data = b"first second"
    assert result == expected_data

    # Verify proper logging
    mock_logger.debug.assert_any_call("Listening for data...", timeout=10)
    mock_logger.debug.assert_any_call(
        "Received packet",
        packet_length=len(packet1),
        header=(0, 2, 70),
        payload=b"first",
    )
    mock_logger.debug.assert_any_call("Received all expected packets", received=2)


@patch("time.time")
def test_receive_timeout(mock_time, mock_logger, mock_radio):
    """Test timeout during reception."""
    packet_manager = PacketManager(mock_logger, mock_radio, "")

    # Set up mock time to simulate timeout
    # We need at least 3 values:
    # 1. Initial start_time
    # 2. Time check for timeout condition
    # 3. Time for calculating elapsed time in the log message
    mock_time.side_effect = [10.0, 21.0, 21.0]  # Simulate a timeout after 11 seconds

    # Configure radio to return a packet (this doesn't matter for timeout test)
    mock_radio.receive.return_value = None

    # Call the receive method with default timeout (10 seconds)
    result = packet_manager.listen()

    # Check that we got None due to timeout
    assert result is None

    # Verify listen timeout was logged
    mock_logger.debug.assert_called_with("Listen timeout reached", elapsed=11.0)


def test_get_header_and_payload(mock_logger, mock_radio):
    """Test _get_header and _get_payload helper methods."""
    packet_manager = PacketManager(mock_logger, mock_radio, "")

    # Create a test packet
    sequence_num = 42
    total_packets = 100
    rssi = 70
    payload = b"Test payload data"

    header = (
        sequence_num.to_bytes(2, "big")
        + total_packets.to_bytes(2, "big")
        + rssi.to_bytes(1, "big")
    )
    test_packet = header + payload

    # Test _get_header
    seq, total, signal = packet_manager._get_header(test_packet)
    assert seq == sequence_num
    assert total == total_packets
    assert signal == rssi

    # Test _get_payload
    extracted_payload = packet_manager._get_payload(test_packet)
    assert extracted_payload == payload


def test_send_acknowledgement(mock_logger, mock_radio):
    """Test sending acknowledgment packet."""
    packet_manager = PacketManager(mock_logger, mock_radio, "TEST")

    # Call the send_acknowledgement method
    packet_manager.send_acknowledgement()

    # Verify that send was called with ACK message
    mock_radio.send.assert_called()

    # Verify that the acknowledgment message was logged
    mock_logger.debug.assert_called_with("Sent acknowledgment packet")
