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
