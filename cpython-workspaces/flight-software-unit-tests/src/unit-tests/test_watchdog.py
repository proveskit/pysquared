"""Unit tests for the Watchdog class.

This module contains unit tests for the `Watchdog` class, which provides
functionality for petting a watchdog timer to prevent system resets.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest
from mocks.circuitpython.digitalio import Direction as MockDirection

from pysquared.logger import Logger

digitalio = MagicMock()
digitalio.Direction = MockDirection
sys.modules["digitalio"] = digitalio
from pysquared.watchdog import Watchdog  # noqa: E402


@pytest.fixture
def mock_pin() -> MagicMock:
    """Mocks a microcontroller Pin."""
    return MagicMock()


@pytest.fixture
def mock_logger() -> MagicMock:
    """Mocks the Logger class."""
    return MagicMock(spec=Logger)


@patch("pysquared.watchdog.initialize_pin")
def test_watchdog_init(
    mock_initialize_pin: MagicMock, mock_logger: MagicMock, mock_pin: MagicMock
) -> None:
    """Tests Watchdog initialization.

    Args:
        mock_initialize_pin: Mocked initialize_pin function.
        mock_logger: Mocked Logger instance.
        mock_pin: Mocked Pin instance.
    """
    mock_digital_in_out = MagicMock()
    mock_initialize_pin.return_value = mock_digital_in_out

    watchdog = Watchdog(mock_logger, mock_pin)

    mock_initialize_pin.assert_called_once_with(
        mock_logger,
        mock_pin,
        digitalio.Direction.OUTPUT,
        False,
    )
    assert watchdog._digital_in_out is mock_digital_in_out


@patch("pysquared.watchdog.time.sleep")
@patch("pysquared.watchdog.initialize_pin")
def test_watchdog_pet(
    mock_initialize_pin: MagicMock,
    mock_sleep: MagicMock,
    mock_logger: MagicMock,
    mock_pin: MagicMock,
) -> None:
    """Tests Watchdog pet method using side_effect on sleep.

    Args:
        mock_initialize_pin: Mocked initialize_pin function.
        mock_sleep: Mocked time.sleep function.
        mock_logger: Mocked Logger instance.
        mock_pin: Mocked Pin instance.
    """
    mock_digital_in_out = MagicMock()
    mock_initialize_pin.return_value = mock_digital_in_out

    # Inject a side effect to the sleep function
    # to capture the state of the mock pin when sleep is called
    value_during_sleep = None

    def check_value_and_sleep(_: float) -> None:
        """Check the pin value and set it during sleep."""
        nonlocal value_during_sleep
        value_during_sleep = mock_digital_in_out.value

    mock_sleep.side_effect = check_value_and_sleep

    watchdog = Watchdog(mock_logger, mock_pin)
    watchdog.pet()

    mock_sleep.assert_called_once_with(0.01)
    assert value_during_sleep, "Watchdog pin value should be True when sleep is called"
    assert mock_digital_in_out.value is False, (
        "Watchdog pin value should be False after pet() finishes"
    )
