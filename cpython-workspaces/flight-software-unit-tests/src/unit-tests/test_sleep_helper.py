"""Unit tests for the SleepHelper class.

This module contains unit tests for the `SleepHelper` class, which provides
functionality for safe sleep operations, including watchdog petting and handling
of sleep duration limits.
"""

from unittest.mock import MagicMock, patch

import pytest
from pysquared.config.config import Config
from pysquared.logger import Logger
from pysquared.sleep_helper import SleepHelper
from pysquared.watchdog import Watchdog


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
    # Setup mock time to simulate the while loop behavior
    # The loop checks: while time.monotonic() < end_sleep_time
    mock_time.monotonic.side_effect = [
        0.0,  # Initial call for end_sleep_time calculation
        0.0,  # First while loop check (0.0 < 15.0 = True)
        0.0,  # min() calculation for time_increment
        15.0,  # Second while loop check (15.0 < 15.0 = False, exit loop)
    ]
    mock_time.sleep = MagicMock()

    sleep_helper.safe_sleep(15)

    # Verify the watchdog was pet twice (once before loop, once after sleep)
    assert mock_watchdog.pet.call_count == 2

    # Verify time.sleep was called with the correct increment
    mock_time.sleep.assert_called_once_with(15.0)

    # Verify no warning was logged
    mock_logger.warning.assert_not_called()

    # Verify debug log was called
    mock_logger.debug.assert_called_once_with("Setting Safe Sleep Mode", duration=15)


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
    # Setup mock time to simulate the while loop behavior with adjusted duration
    mock_time.monotonic.side_effect = [
        0.0,  # Initial call for end_sleep_time calculation
        0.0,  # First while loop check (0.0 < 100.0 = True)
        0.0,  # min() calculation for time_increment
        100.0,  # Second while loop check (100.0 < 100.0 = False, exit loop)
    ]
    mock_time.sleep = MagicMock()

    # Requested duration exceeds the longest allowable sleep time (which is 100)
    sleep_helper.safe_sleep(150)

    # Verify the watchdog was pet
    assert mock_watchdog.pet.call_count == 2

    # Verify warning was logged
    mock_logger.warning.assert_called_once_with(
        "Requested sleep duration exceeds longest allowable sleep time. "
        "Adjusting to longest allowable sleep time.",
        requested_duration=150,
        longest_allowable_sleep_time=100,
    )

    # Verify debug log was called with adjusted duration
    mock_logger.debug.assert_called_once_with("Setting Safe Sleep Mode", duration=100)

    # Verify time.sleep was called with the adjusted duration
    mock_time.sleep.assert_called_once_with(15)


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
    # Setup mock time to simulate multiple sleep increments
    mock_time.monotonic.side_effect = [
        0.0,  # Initial call for end_sleep_time calculation
        0.0,  # First while loop check (0.0 < 35.0 = True)
        0.0,  # First min() calculation (35.0 - 0.0, 15) = 15.0
        15.0,  # Second while loop check (15.0 < 35.0 = True)
        15.0,  # Second min() calculation (35.0 - 15.0, 15) = 15.0
        30.0,  # Third while loop check (30.0 < 35.0 = True)
        30.0,  # Third min() calculation (35.0 - 30.0, 15) = 5.0
        35.0,  # Fourth while loop check (35.0 < 35.0 = False, exit loop)
    ]
    mock_time.sleep = MagicMock()

    # Call safe_sleep with a duration that will require multiple watchdog pets
    sleep_helper.safe_sleep(35)

    # Verify watchdog was pet multiple times (once before loop + after each sleep)
    assert (
        mock_watchdog.pet.call_count == 4
    )  # Once before loop + three times after each sleep

    # Verify time.sleep was called multiple times with correct increments
    expected_calls = [
        ((15.0,),),  # First increment: 15 seconds
        ((15.0,),),  # Second increment: 15 seconds
        ((5.0,),),  # Third increment: 5 seconds (remaining time)
    ]
    assert mock_time.sleep.call_args_list == expected_calls


@patch("pysquared.sleep_helper.time")
def test_safe_sleep_custom_watchdog_timeout(
    mock_time: MagicMock,
    sleep_helper: SleepHelper,
    mock_watchdog: MagicMock,
) -> None:
    """Tests safe_sleep with custom watchdog timeout.

    Args:
        mock_time: Mocked time module.
        sleep_helper: SleepHelper instance for testing.
        mock_watchdog: Mocked Watchdog instance.
    """
    # Setup mock time to simulate behavior with custom timeout
    mock_time.monotonic.side_effect = [
        0.0,  # Initial call for end_sleep_time calculation
        0.0,  # First while loop check (0.0 < 20.0 = True)
        0.0,  # First min() calculation (20.0 - 0.0, 10) = 10.0
        10.0,  # Second while loop check (10.0 < 20.0 = True)
        10.0,  # Second min() calculation (20.0 - 10.0, 10) = 10.0
        20.0,  # Third while loop check (20.0 < 20.0 = False, exit loop)
    ]
    mock_time.sleep = MagicMock()

    # Call safe_sleep with custom watchdog timeout
    sleep_helper.safe_sleep(20, watchdog_timeout=10)

    # Verify watchdog was pet correct number of times
    assert (
        mock_watchdog.pet.call_count == 3
    )  # Once before loop + twice after each sleep

    # Verify time.sleep was called with custom timeout intervals
    expected_calls = [
        ((10.0,),),  # First increment: 10 seconds (custom timeout)
        ((10.0,),),  # Second increment: 10 seconds (custom timeout)
    ]
    assert mock_time.sleep.call_args_list == expected_calls
