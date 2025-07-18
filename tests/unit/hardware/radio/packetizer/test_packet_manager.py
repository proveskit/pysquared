"""Unit tests for the PacketManager class.

This module contains unit tests for the `PacketManager` class, which handles
packetization, sending, and receiving of data over a radio. The tests cover
initialization, data packing, sending, listening for data, and acknowledgment
mechanisms.
"""

import random
from unittest.mock import MagicMock, patch

import pytest

from pysquared.hardware.radio.packetizer.packet_manager import PacketManager
from pysquared.logger import Logger
from pysquared.nvm.counter import Counter
from pysquared.protos.radio import RadioProto


@pytest.fixture
def mock_logger() -> MagicMock:
    """Mocks the Logger class."""
    return MagicMock(spec=Logger)


@pytest.fixture
def mock_radio() -> MagicMock:
    """Mocks the RadioProto class.

    Sets a default max packet size and RSSI value for testing.
    """
    radio = MagicMock(spec=RadioProto)
    radio.get_max_packet_size.return_value = 100  # Mock packet size for tests
    radio.get_rssi.return_value = -70  # Mock RSSI value
    return radio


@pytest.fixture
def mock_message_counter() -> MagicMock:
    """Mocks the Counter class"""
    counter = MagicMock(spec=Counter)
    counter.get.return_value = 1
    return counter


def test_packet_manager_init(mock_logger, mock_radio, mock_message_counter):
    """Tests PacketManager initialization.

    Args:
        mock_logger: Mocked Logger instance.
        mock_radio: Mocked RadioProto instance.
    """
    license_str = "TEST_LICENSE"

    packet_manager = PacketManager(
        mock_logger, mock_radio, license_str, mock_message_counter, send_delay=0.5
    )

    assert packet_manager._logger is mock_logger
    assert packet_manager._radio is mock_radio
    assert packet_manager._license == license_str
    assert packet_manager._message_counter is mock_message_counter
    assert packet_manager._send_delay == 0.5
    assert packet_manager._header_size == 6
    assert packet_manager._payload_size == 94  # 100 - 6 header bytes


def test_pack_data_single_packet(mock_logger, mock_radio, mock_message_counter):
    """Tests packing data that fits in a single packet.

    Args:
        mock_logger: Mocked Logger instance.
        mock_radio: Mocked RadioProto instance.
        mock_message_counter: Mocked Counter instance.
    """
    license_str = "TEST"
    packet_manager = PacketManager(
        mock_logger, mock_radio, license_str, mock_message_counter
    )

    # Create test data that fits in a single packet
    test_data = b"Small test data"
    packets = packet_manager._pack_data(test_data)
    assert len(packets) == 1

    # Check packet structure
    packet = packets[0]
    assert len(packet) == len(test_data) + packet_manager._header_size

    # Check header
    packet_identifier = int.from_bytes(packet[0:1], "big")
    sequence_number = int.from_bytes(packet[1:3], "big")
    total_packets = int.from_bytes(packet[3:5], "big")
    rssi = int.from_bytes(packet[5:6], "big")
    payload = packet[6:]

    assert packet_identifier == mock_message_counter.get()
    assert sequence_number == 0
    assert total_packets == 1
    assert rssi == 70
    assert payload == test_data


def test_pack_data_multiple_packets(mock_logger, mock_radio, mock_message_counter):
    """Tests packing data that requires multiple packets.

    Args:
        mock_logger: Mocked Logger instance.
        mock_radio: Mocked RadioProto instance.
        mock_message_counter: Mocked Counter instance.
    """
    license_str = "TEST"
    packet_manager = PacketManager(
        mock_logger, mock_radio, license_str, mock_message_counter
    )

    # Create test data that requires multiple packets
    # With a payload size of 94, this will require 3 packets
    test_data = b"X" * 250
    packets = packet_manager._pack_data(test_data)
    assert len(packets) == 3

    # Check each packet
    reconstructed_data = b""

    for i, packet in enumerate(packets):
        packet_identifier = int.from_bytes(packet[0:1], "big")
        sequence_number = int.from_bytes(packet[1:3], "big")
        total_packets = int.from_bytes(packet[3:5], "big")
        rssi = int.from_bytes(packet[5:6], "big")
        payload = packet[6:]

        assert packet_identifier == mock_message_counter.get()
        assert sequence_number == i
        assert total_packets == 3
        assert rssi == 70
        reconstructed_data += payload

    # Verify the reconstructed data matches the original
    assert reconstructed_data == test_data


@patch("time.sleep")
def test_send_success(mock_sleep, mock_logger, mock_radio, mock_message_counter):
    """Tests successful execution of send method.

    Args:
        mock_sleep: Mocked time.sleep function.
        mock_logger: Mocked Logger instance.
        mock_radio: Mocked RadioProto instance.
        mock_message_counter: Mocked Counter instance.
    """
    license_str = "TEST"

    packet_manager = PacketManager(
        mock_logger, mock_radio, license_str, mock_message_counter, send_delay=0.1
    )

    # Create small test data
    test_data = b"""{"message": "test beacon"}"""
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
def test_send_success_multipacket(
    mock_sleep, mock_logger, mock_radio, mock_message_counter
):
    """Tests successful execution of send method with multiple packets.

    Args:
        mock_sleep: Mocked time.sleep function.
        mock_logger: Mocked Logger instance.
        mock_radio: Mocked RadioProto instance.
        mock_message_counter: Mocked Counter instance.
    """
    license_str = "TEST"

    packet_manager = PacketManager(
        mock_logger, mock_radio, license_str, mock_message_counter, send_delay=0.1
    )

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


def test_send_unlicensed(mock_logger, mock_radio, mock_message_counter):
    """Tests unlicensed execution of send method.

    Args:
        mock_logger: Mocked Logger instance.
        mock_radio: Mocked RadioProto instance.
        mock_message_counter: Mocked Counter instance.
    """
    license_str = ""

    packet_manager = PacketManager(
        mock_logger, mock_radio, license_str, mock_message_counter, send_delay=0.1
    )

    test_data = b"hello world"
    _ = packet_manager.send(test_data)

    # Verify log messages
    mock_logger.warning.assert_any_call("License is required to send data")


@patch("time.time")
def test_unpack_data(mock_time, mock_logger, mock_radio, mock_message_counter):
    """Tests unpacking data from received packets.

    Args:
        mock_time: Mocked time.time function.
        mock_logger: Mocked Logger instance.
        mock_radio: Mocked RadioProto instance.
        mock_message_counter: Mocked Counter instance.
    """
    packet_manager = PacketManager(mock_logger, mock_radio, "", mock_message_counter)

    # Create test packets with proper headers
    packet1 = (
        (1).to_bytes(1, "big")
        + (0).to_bytes(2, "big")
        + (3).to_bytes(2, "big")
        + (70).to_bytes(1, "big")
        + b"first"
    )
    packet2 = (
        (1).to_bytes(1, "big")
        + (1).to_bytes(2, "big")
        + (3).to_bytes(2, "big")
        + (70).to_bytes(1, "big")
        + b" second"
    )
    packet3 = (
        (1).to_bytes(1, "big")
        + (2).to_bytes(2, "big")
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
def test_receive_success(mock_time, mock_logger, mock_radio, mock_message_counter):
    """Tests successfully receiving all packets.

    Args:
        mock_time: Mocked time.time function.
        mock_logger: Mocked Logger instance.
        mock_radio: Mocked RadioProto instance.
        mock_message_counter: Mocked Counter instance.
    """
    packet_manager = PacketManager(mock_logger, mock_radio, "", mock_message_counter)

    # Set up mock time to control the flow
    mock_time.side_effect = [10.0, 10.1, 10.2, 10.3, 10.4]

    # Create test packets
    packet1 = (
        (1).to_bytes(1, "big")
        + (0).to_bytes(2, "big")
        + (2).to_bytes(2, "big")
        + (70).to_bytes(1, "big")
        + b"first"
    )
    packet2 = None
    packet3 = (
        (1).to_bytes(1, "big")
        + (1).to_bytes(2, "big")
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
        header=(1, 0, 2, -70),
        payload=b"first",
    )
    mock_logger.debug.assert_any_call("Received all expected packets", received=2)


@patch("time.time")
def test_receive_timeout(mock_time, mock_logger, mock_radio, mock_message_counter):
    """Tests timeout during reception.

    Args:
        mock_time: Mocked time.time function.
        mock_logger: Mocked Logger instance.
        mock_radio: Mocked RadioProto instance.
        mock_message_counter: Mocked Counter instance.
    """
    packet_manager = PacketManager(mock_logger, mock_radio, "", mock_message_counter)

    # Set up mock time to simulate timeout
    # We need at least 3 values:
    # 1. Initial start_time
    # 2. Time check for timeout condition
    # 3. Time for calculating elapsed time in the log message
    # Simulate a timeout after 11 seconds
    mock_time.side_effect = [10.0, 21.0, 21.0]

    # Configure radio to return a packet (this doesn't matter for timeout test)
    mock_radio.receive.return_value = None

    # Call the receive method with default timeout (10 seconds)
    result = packet_manager.listen()

    # Check that we got None due to timeout
    assert result is None

    # Verify listen timeout was logged
    mock_logger.debug.assert_called_with("Listen timeout reached", elapsed=11.0)


def test_get_header_and_payload(mock_logger, mock_radio, mock_message_counter):
    """Tests _get_header and _get_payload helper methods.

    Args:
        mock_logger: Mocked Logger instance.
        mock_radio: Mocked RadioProto instance.
        mock_message_counter: Mocked Counter instance.
    """
    packet_manager = PacketManager(mock_logger, mock_radio, "", mock_message_counter)

    # Create a test packet
    packet_identifier = 1
    sequence_num = 42
    total_packets = 100
    rssi = -70
    payload = b"Test payload data"

    header = (
        packet_identifier.to_bytes(1, "big")
        + sequence_num.to_bytes(2, "big")
        + total_packets.to_bytes(2, "big")
        + abs(rssi).to_bytes(1, "big")
    )
    test_packet = header + payload

    # Test _get_header
    p_id, seq, total, signal = packet_manager._get_header(test_packet)
    assert p_id == packet_identifier
    assert seq == sequence_num
    assert total == total_packets
    assert signal == rssi

    # Test _get_payload
    extracted_payload = packet_manager._get_payload(test_packet)
    assert extracted_payload == payload


def test_send_acknowledgement(mock_logger, mock_radio, mock_message_counter):
    """Tests sending acknowledgment packet.

    Args:
        mock_logger: Mocked Logger instance.
        mock_radio: Mocked RadioProto instance.
        mock_message_counter: Mocked Counter instance.
    """
    packet_manager = PacketManager(
        mock_logger, mock_radio, "TEST", mock_message_counter
    )

    # Call the send_acknowledgement method
    packet_manager.send_acknowledgement()

    # Verify that send was called with ACK message
    mock_radio.send.assert_called()

    # Verify that the acknowledgment message was logged
    mock_logger.debug.assert_called_with("Sent acknowledgment packet")


def test_get_packet_identifier(mock_logger, mock_radio, mock_message_counter):
    """Test _get_packet_identifier helper method.

    Args:
        mock_logger: Mocked Logger instance.
        mock_radio: Mocked RadioProto instance.
        mock_message_counter: Mocked Counter instance.
    """
    packet_manager = PacketManager(mock_logger, mock_radio, "", mock_message_counter)

    # Call the _get_packet_identifier method
    result = packet_manager._get_packet_identifier()

    # Verify that the message counter was incremented
    mock_message_counter.increment.assert_called_once()

    # Verify that the result is the value from the counter
    assert result == mock_message_counter.get()


@patch("time.time")
def test_listen_ignores_mismatched_packet_ids(
    mock_time, mock_logger, mock_radio, mock_message_counter
):
    """Test that listen ignores packets with mismatched packet identifiers.

    Args:
        mock_time: Mocked time.time function.
        mock_logger: Mocked Logger instance.
        mock_radio: Mocked RadioProto instance.
        mock_message_counter: Mocked Counter instance.
    """
    packet_manager = PacketManager(mock_logger, mock_radio, "", mock_message_counter)

    # Set up mock time to control the flow
    mock_time.side_effect = [10.0, 10.1, 10.2, 21.0, 21.0]

    # Create two packets with different packet identifiers
    packet1 = (
        (1).to_bytes(1, "big")
        + (0).to_bytes(2, "big")
        + (2).to_bytes(2, "big")
        + (70).to_bytes(1, "big")
        + b"first"
    )
    packet2 = (
        (2).to_bytes(1, "big")
        + (0).to_bytes(2, "big")
        + (1).to_bytes(2, "big")
        + (70).to_bytes(1, "big")
        + b"second"
    )

    # Configure mock_radio.receive to return the two packets
    mock_radio.receive.side_effect = [packet1, packet2]

    # Call the listen method
    result = packet_manager.listen()

    # Assert that the result is None, as the second packet should be ignored
    assert result is None

    # Verify that the timeout message was logged
    mock_logger.debug.assert_any_call("Listen timeout reached", elapsed=11.0)
