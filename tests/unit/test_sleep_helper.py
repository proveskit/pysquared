"""Unit tests for the SleepHelper class.

This module contains unit tests for the `SleepHelper` class, which provides
functionality for safe sleep operations, including watchdog petting and handling
of sleep duration limits.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

from pysquared.config.config import Config
from pysquared.logger import Logger
from pysquared.watchdog import Watchdog

# Create mock modules for alarm and alarm.time before importing SleepHelper
mock_alarm = MagicMock()
mock_time_alarm = MagicMock()
sys.modules["alarm"] = mock_alarm
sys.modules["alarm.time"] = MagicMock()
sys.modules["alarm.time"].TimeAlarm = mock_time_alarm

# Now we can import SleepHelper
from pysquared.sleep_helper import SleepHelper  # noqa: E402


@pytest.fixture
def mock_logger() -> MagicMock:
    """Mocks the Logger class."""
    return MagicMock(spec=Logger)


@pytest.fixture
def mock_config() -> MagicMock:
    """Mocks the Config class with a predefined longest allowable sleep time."""
    config = MagicMock(spec=Config)
    config.longest_allowable_sleep_time = 100
    return config


@pytest.fixture
def mock_watchdog() -> MagicMock:
    """Mocks the Watchdog class."""
    return MagicMock(spec=Watchdog)


@pytest.fixture
def sleep_helper(
    mock_logger: MagicMock,
    mock_config: MagicMock,
    mock_watchdog: MagicMock,
) -> SleepHelper:
    """Provides a SleepHelper instance for testing."""
    return SleepHelper(mock_logger, mock_config, mock_watchdog)


def test_init(
    mock_logger: MagicMock,
    mock_config: MagicMock,
    mock_watchdog: MagicMock,
) -> None:
    """Tests SleepHelper initialization.

    Args:
        mock_logger: Mocked Logger instance.
        mock_config: Mocked Config instance.
        mock_watchdog: Mocked Watchdog instance.
    """
    sleep_helper = SleepHelper(mock_logger, mock_config, mock_watchdog)

    assert sleep_helper.logger is mock_logger
    assert sleep_helper.config is mock_config
    assert sleep_helper.watchdog is mock_watchdog


@patch("pysquared.sleep_helper.time")
def test_safe_sleep_within_limit(
    mock_time: MagicMock,
    sleep_helper: SleepHelper,
    mock_logger: MagicMock,
    mock_watchdog: MagicMock,
) -> None:
    """Tests safe_sleep with duration within the allowable limit.

    Args:
        mock_time: Mocked time module.
        sleep_helper: SleepHelper instance for testing.
        mock_logger: Mocked Logger instance.
        mock_watchdog: Mocked Watchdog instance.
    """
    # Reset mocks
    mock_alarm.reset_mock()
    mock_time_alarm.reset_mock()

    # Setup mock time to simulate a time sequence
    mock_time.monotonic = MagicMock()
    mock_time.monotonic.side_effect = [0.0, 0.0, 0.0, 0.0, 15.0]

    sleep_helper.safe_sleep(15)

    # Verify the watchdog was pet
    assert mock_watchdog.pet.call_count == 2

    # Verify no warning was logged
    mock_logger.warning.assert_not_called()

    # Verify debug log was called
    mock_logger.debug.assert_called_once_with("Setting Safe Sleep Mode", duration=15)

    # Verify TimeAlarm was created with correct parameters
    mock_time_alarm.assert_called_once_with(monotonic_time=15.0)

    # Verify light_sleep was called with the alarm
    mock_alarm.light_sleep_until_alarms.assert_called_once()


@patch("pysquared.sleep_helper.time")
def test_safe_sleep_exceeds_limit(
    mock_time: MagicMock,
    sleep_helper: SleepHelper,
    mock_logger: MagicMock,
    mock_config: MagicMock,
    mock_watchdog: MagicMock,
) -> None:
    """Tests safe_sleep with duration exceeding the allowable limit.

    Args:
        mock_time: Mocked time module.
        sleep_helper: SleepHelper instance for testing.
        mock_logger: Mocked Logger instance.
        mock_config: Mocked Config instance.
        mock_watchdog: Mocked Watchdog instance.
    """
    # Reset mocks
    mock_alarm.reset_mock()
    mock_time_alarm.reset_mock()

    # Setup mock time to simulate a time sequence
    mock_time.monotonic.side_effect = [0.0, 0.0, 0.0, 0.0, 115.0]

    # Requested duration exceeds the longest allowable sleep time (which is 100)
    sleep_helper.safe_sleep(150)

    # Verify the watchdog was pet
    mock_watchdog.pet.assert_called()

    # Verify warning was logged
    mock_logger.warning.assert_called_once_with(
        "Requested sleep duration exceeds longest allowable sleep time. "
        "Adjusting to longest allowable sleep time.",
        requested_duration=150,
        longest_allowable_sleep_time=100,
    )

    # Verify debug log was called with adjusted duration
    mock_logger.debug.assert_called_once_with("Setting Safe Sleep Mode", duration=100)

    # Verify TimeAlarm was created with correct parameters using adjusted duration
    mock_time_alarm.assert_called_once_with(monotonic_time=15.0)

    # Verify light_sleep was called with the alarm
    mock_alarm.light_sleep_until_alarms.assert_called_once()


@patch("pysquared.sleep_helper.time")
def test_safe_sleep_multiple_watchdog_pets(
    mock_time: MagicMock,
    sleep_helper: SleepHelper,
    mock_watchdog: MagicMock,
) -> None:
    """Tests safe_sleep with multiple watchdog pets during longer sleep.

    Args:
        mock_time: Mocked time module.
        sleep_helper: SleepHelper instance for testing.
        mock_watchdog: Mocked Watchdog instance.
    """
    # Reset mocks
    mock_alarm.reset_mock()
    mock_time_alarm.reset_mock()

    # Setup mock time to simulate a time sequence where we need multiple increments
    mock_time.monotonic.side_effect = [
        0.0,
        0.0,
        0.0,
        0.0,  # Initial
        15.0,
        15.0,
        15.0,  # First loop
        30.0,
        30.0,
        30.0,  # Second loop
        35.0,  # Last check and exit loop
    ]

    # Call safe_sleep with a duration that will require multiple watchdog pets
    sleep_helper.safe_sleep(35)

    # Verify watchdog was pet multiple times (once before sleeping + after each wake)
    assert mock_watchdog.pet.call_count == 4  # Once before loop + three times in loop

    # Verify TimeAlarm was created correctly for each increment
    mock_time_alarm.assert_any_call(monotonic_time=15.0)  # 0.0 + 15.0 (first increment)
    mock_time_alarm.assert_any_call(
        monotonic_time=30.0
    )  # 15.0 + 15.0 (second increment)
    mock_time_alarm.assert_any_call(monotonic_time=35.0)  # 30.0 + 5.0 (final increment)

    # Verify light_sleep was called multiple times
    assert mock_alarm.light_sleep_until_alarms.call_count == 3
