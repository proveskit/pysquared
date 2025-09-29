"""Unit tests for the digitalio module.

This module contains unit tests for the `digitalio` module, which provides
functionality for initializing digital input/output pins. The tests cover
successful initialization and failure scenarios.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

from mocks.circuitpython.digitalio import Direction as MockDirection
from pysquared.hardware.exception import HardwareInitializationError
from pysquared.logger import Logger

digitalio = MagicMock()
digitalio.Direction = MockDirection
sys.modules["digitalio"] = digitalio
from pysquared.hardware.digitalio import initialize_pin  # noqa: E402


@patch("pysquared.hardware.digitalio.DigitalInOut")
@patch("pysquared.hardware.digitalio.Pin")
def test_initialize_pin_success(mock_pin: MagicMock, mock_digital_in_out: MagicMock):
    """Tests successful initialization of a digital pin.

    Args:
        mock_pin: Mocked Pin class.
        mock_digital_in_out: Mocked DigitalInOut class.
    """
    # Mock the logger
    mock_logger = MagicMock(spec=Logger)

    # Mock pin and direction
    mock_direction = digitalio.Direction.OUTPUT
    initial_value = True

    # Mock DigitalInOut instance
    mock_dio = mock_digital_in_out.return_value

    # Call fn under test
    _ = initialize_pin(mock_logger, mock_pin, mock_direction, initial_value)

    # Assertions
    mock_digital_in_out.assert_called_once_with(mock_pin)
    assert mock_dio.direction == mock_direction
    assert mock_dio.value == initial_value
    mock_logger.debug.assert_called_once()


@patch("pysquared.hardware.digitalio.DigitalInOut")
@patch("pysquared.hardware.digitalio.Pin")
def test_initialize_pin_failure(mock_pin: MagicMock, mock_digital_in_out: MagicMock):
    """Tests digital pin initialization failure with retries.

    Args:
        mock_pin: Mocked Pin class.
        mock_digital_in_out: Mocked DigitalInOut class.
    """
    # Mock the logger
    mock_logger = MagicMock(spec=Logger)

    # Mock pin and direction
    mock_direction = digitalio.Direction.OUTPUT
    initial_value = True

    # Mock DigitalInOut to raise an exception
    mock_digital_in_out.side_effect = Exception("Simulated failure")

    # Call the function and assert exception
    with pytest.raises(HardwareInitializationError):
        initialize_pin(mock_logger, mock_pin, mock_direction, initial_value)

    # Assertions
    mock_digital_in_out.assert_called_once_with(mock_pin)
    mock_logger.debug.assert_called()
