"""Unit tests for the BaseRadioManager class.

This module contains unit tests for the `BaseRadioManager` class, focusing on
ensuring that abstract methods raise `NotImplementedError` as expected and that
the default `get_max_packet_size` returns the correct value.
"""

import pytest
from pysquared.hardware.radio.manager.base import BaseRadioManager
from pysquared.hardware.radio.modulation import LoRa


def test_initialize_radio_not_implemented():
    """Tests that the _initialize_radio method raises NotImplementedError.

    This test verifies that the abstract `_initialize_radio` method in the
    `BaseRadioManager` correctly raises a `NotImplementedError` when called
    directly, as it is intended to be overridden by subclasses.
    """
    # Create a mock instance of the BaseRadioManager
    mock_manager = BaseRadioManager.__new__(BaseRadioManager)

    # Check that calling _initialize_radio raises NotImplementedError
    with pytest.raises(NotImplementedError):
        mock_manager._initialize_radio(LoRa)


def test_receive_not_implemented():
    """Tests that the receive method raises NotImplementedError.

    This test verifies that the abstract `receive` method in the
    `BaseRadioManager` correctly raises a `NotImplementedError` when called
    directly, as it is intended to be overridden by subclasses.
    """
    # Create a mock instance of the BaseRadioManager
    mock_manager = BaseRadioManager.__new__(BaseRadioManager)

    # Check that calling _initialize_radio raises NotImplementedError
    with pytest.raises(NotImplementedError):
        mock_manager.receive()


def test_send_internal_not_implemented():
    """Tests that the _send_internal method raises NotImplementedError.

    This test verifies that the abstract `_send_internal` method in the
    `BaseRadioManager` correctly raises a `NotImplementedError` when called
    directly, as it is intended to be overridden by subclasses.
    """
    # Create a mock instance of the BaseRadioManager
    mock_manager = BaseRadioManager.__new__(BaseRadioManager)

    # Check that calling _initialize_radio raises NotImplementedError
    with pytest.raises(NotImplementedError):
        mock_manager._send_internal(b"blah")


def test_get_modulation_not_implemented():
    """Tests that the get_modulation method raises NotImplementedError.

    This test verifies that the abstract `get_modulation` method in the
    `BaseRadioManager` correctly raises a `NotImplementedError` when called
    directly, as it is intended to be overridden by subclasses.
    """
    # Create a mock instance of the BaseRadioManager
    mock_manager = BaseRadioManager.__new__(BaseRadioManager)

    # Check that calling get_modulation raises NotImplementedError
    with pytest.raises(NotImplementedError):
        mock_manager.get_modulation()


def test_get_max_packet_size():
    """Tests that the get_max_packet_size method returns the default value.

    This test verifies that the `get_max_packet_size` method in the
    `BaseRadioManager` returns the default packet size, as it provides a
    concrete implementation that can be overridden by subclasses.
    """
    # Create a mock instance of the BaseRadioManager
    mock_manager = BaseRadioManager.__new__(BaseRadioManager)

    # Check that get_max_packet_size returns the default packet size
    assert mock_manager.get_max_packet_size() == 128  # Default value


def test_send_oversized_packet_truncates():
    """Tests that oversized packets are truncated and a warning is logged.

    This test verifies that when a packet larger than max_packet_size is sent,
    the BaseRadioManager logs a warning and truncates the data to max_packet_size
    before sending.
    """
    from unittest.mock import MagicMock

    # Create a mock instance of the BaseRadioManager
    mock_manager = BaseRadioManager.__new__(BaseRadioManager)
    mock_manager._log = MagicMock()
    mock_manager._radio_config = MagicMock()
    mock_manager._radio_config.license = "test_license"

    # Mock get_max_packet_size to return a small value for testing
    mock_manager.get_max_packet_size = MagicMock(return_value=10)

    # Mock _send_internal to capture what data is actually sent
    sent_data = []

    def capture_send(data: bytes) -> bool:
        sent_data.append(data)
        return True

    mock_manager._send_internal = capture_send

    # Create data larger than max packet size
    oversized_data = b"This is a message that is longer than 10 bytes"

    # Send the oversized data
    result = mock_manager.send(oversized_data)

    # Verify that send was successful
    assert result is True

    # Verify that a warning was logged
    mock_manager._log.warning.assert_called_once()
    warning_call = mock_manager._log.warning.call_args
    assert warning_call[0][0] == "Data exceeds max packet size, truncating"
    assert warning_call[1]["data_length"] == len(oversized_data)
    assert warning_call[1]["max_packet_size"] == 10

    # Verify that the data was truncated to max_packet_size
    assert len(sent_data) == 1
    assert sent_data[0] == oversized_data[:10]
    assert len(sent_data[0]) == 10


def test_send_exact_size_packet_no_warning():
    """Tests that packets at exactly max_packet_size do not trigger a warning.

    This test verifies that when a packet of exactly max_packet_size is sent,
    no warning is logged and the data is sent as-is.
    """
    from unittest.mock import MagicMock

    # Create a mock instance of the BaseRadioManager
    mock_manager = BaseRadioManager.__new__(BaseRadioManager)
    mock_manager._log = MagicMock()
    mock_manager._radio_config = MagicMock()
    mock_manager._radio_config.license = "test_license"

    # Mock get_max_packet_size to return a small value for testing
    mock_manager.get_max_packet_size = MagicMock(return_value=10)

    # Mock _send_internal to capture what data is actually sent
    sent_data = []

    def capture_send(data: bytes) -> bool:
        sent_data.append(data)
        return True

    mock_manager._send_internal = capture_send

    # Create data exactly at max packet size
    exact_size_data = b"0123456789"  # Exactly 10 bytes

    # Send the data
    result = mock_manager.send(exact_size_data)

    # Verify that send was successful
    assert result is True

    # Verify that no warning was logged about truncation
    mock_manager._log.warning.assert_not_called()

    # Verify that the data was sent as-is
    assert len(sent_data) == 1
    assert sent_data[0] == exact_size_data
    assert len(sent_data[0]) == 10
