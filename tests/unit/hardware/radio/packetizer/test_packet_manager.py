from unittest.mock import MagicMock, call, patch

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
    radio.get_max_packet_size.return_value = 100  # Default packet size for tests
    return radio


def test_packet_manager_init(mock_logger, mock_radio):
    """Test PacketManager initialization."""
    license_str = "TEST_LICENSE"

    packet_manager = PacketManager(mock_logger, mock_radio, license_str, send_delay=0.5)

    assert packet_manager.logger is mock_logger
    assert packet_manager.radio is mock_radio
    assert packet_manager.license == license_str
    assert packet_manager.send_delay == 0.5
    assert packet_manager.header_size == 4
    assert packet_manager.payload_size == 96  # 100 - 4 header bytes


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
    assert len(packet) == len(test_data) + packet_manager.header_size

    # Check header
    sequence_number = int.from_bytes(packet[0:2], "big")
    total_packets = int.from_bytes(packet[2:4], "big")
    payload = packet[4:]

    assert sequence_number == 0
    assert total_packets == 1
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
        payload = packet[4:]

        assert sequence_number == i
        assert total_packets == 3
        reconstructed_data += payload

    # Verify the reconstructed data matches the original
    assert reconstructed_data == test_data


@patch("time.sleep")
def test_send_method_success(mock_sleep, mock_logger, mock_radio):
    """Test successful execution of send method."""
    license_str = "TEST"

    packet_manager = PacketManager(mock_logger, mock_radio, license_str, send_delay=0.1)

    # Create small test data
    test_data = b'{"message": "test beacon"}'
    _ = packet_manager.send(test_data)

    # The send method should prepend the license to the data
    expected_data = license_str.encode() + test_data

    # Calculate number of packets that would be created
    total_packets = (
        len(expected_data) + packet_manager.payload_size - 1
    ) // packet_manager.payload_size

    # Verify radio.send was called for each packet
    assert mock_radio.send.call_count == total_packets

    # Verify sleep was called between sends with correct delay
    assert mock_sleep.call_count == total_packets
    mock_sleep.assert_called_with(0.1)

    # Verify log messages
    mock_logger.info.assert_any_call("Sending packets...", num_packets=total_packets)
    mock_logger.info.assert_any_call(
        "Successfully sent all the packets!", num_packets=total_packets
    )


@patch("time.sleep")
def test_send_large_data_with_progress_logs(mock_sleep, mock_logger, mock_radio):
    """Test sending large data that triggers progress log messages."""
    license_str = "TEST"
    packet_manager = PacketManager(
        mock_logger, mock_radio, license_str, send_delay=0.01
    )

    # Create data large enough to generate multiple packets
    test_data = b"X" * 1000  # This will create multiple packets

    # Call the method
    _ = packet_manager.send(test_data)

    # Calculate expected number of packets
    licensed_data = license_str.encode() + test_data
    total_packets = (
        len(licensed_data) + packet_manager.payload_size - 1
    ) // packet_manager.payload_size

    # Check progress logs were called at the right intervals
    progress_log_calls = [
        call(
            "Making progress sending packets",
            current_packet=i,
            num_packets=total_packets,
        )
        for i in range(0, total_packets, 10)
    ]

    # Verify these calls exist in the mock_logger.info calls
    for log_call in progress_log_calls:
        assert log_call in mock_logger.info.call_args_list
