"""Unit tests for the RV3028Manager class.

This module contains unit tests for the `RV3028Manager` class, which manages
the RV3028 Real-Time Clock (RTC). The tests cover initialization, successful
time setting, and error handling during time setting operations.
"""

from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from busio import I2C

from mocks.rv3028 import RV3028
from pysquared.hardware.exception import HardwareInitializationError
from pysquared.logger.logger_proto import LoggerProto
from pysquared.rtc.manager.rv3028 import RV3028Manager


@pytest.fixture
def mock_i2c() -> MagicMock:
    """Fixture for mock I2C bus."""
    return MagicMock(spec=I2C)


@pytest.fixture
def mock_logger() -> MagicMock:
    """Fixture for mock Logger."""
    return MagicMock(spec=LoggerProto)


@pytest.fixture
def mock_rv3028(mock_i2c: MagicMock) -> Generator[MagicMock, None, None]:
    """Mocks the RV3028 class.

    Args:
        mock_i2c: Mocked I2C bus.

    Yields:
        A MagicMock instance of RV3028.
    """
    with patch("pysquared.rtc.manager.rv3028.RV3028") as mock_class:
        mock_class.return_value = RV3028(mock_i2c)
        yield mock_class


def test_create_rtc(mock_rv3028, mock_i2c: MagicMock, mock_logger: MagicMock) -> None:
    """Tests successful creation of an RV3028 RTC instance.

    Args:
        mock_rv3028: Mocked RV3028 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    rtc_manager = RV3028Manager(mock_logger, mock_i2c)

    assert isinstance(rtc_manager._rtc, RV3028)
    mock_logger.debug.assert_called_once_with("Initializing RTC")


def test_create_rtc_failed(
    mock_rv3028: MagicMock,
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Tests that initialization is retried when it fails.

    Args:
        mock_rv3028: Mocked RV3028 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    mock_rv3028.side_effect = Exception("Simulated RV3028 failure")

    with pytest.raises(HardwareInitializationError):
        _ = RV3028Manager(mock_logger, mock_i2c)

    mock_logger.debug.assert_called_with("Initializing RTC")
    # Verify that RV3028 constructor was called up to 3 times (due to retries)
    assert mock_rv3028.call_count <= 3


def test_set_time_success(
    mock_rv3028, mock_i2c: MagicMock, mock_logger: MagicMock
) -> None:
    """Tests successful setting of the time.

    Args:
        mock_rv3028: Mocked RV3028 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    rtc_manager = RV3028Manager(mock_logger, mock_i2c)

    rtc_manager._rtc = MagicMock(spec=RV3028)
    rtc_manager._rtc.set_date = MagicMock()
    rtc_manager._rtc.set_time = MagicMock()

    year, month, date, hour, minute, second, weekday = 2025, 5, 4, 11, 30, 0, 5

    rtc_manager.set_time(year, month, date, hour, minute, second, weekday)

    rtc_manager._rtc.set_date.assert_called_once_with(year, month, date, weekday)
    rtc_manager._rtc.set_time.assert_called_once_with(hour, minute, second)
    mock_logger.error.assert_not_called()


def test_set_time_failure_set_date(
    mock_rv3028, mock_i2c: MagicMock, mock_logger: MagicMock
) -> None:
    """Tests handling of exceptions during set_date.

    Args:
        mock_rv3028: Mocked RV3028 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    rtc_manager = RV3028Manager(mock_logger, mock_i2c)
    rtc_manager._rtc = MagicMock(spec=RV3028)
    rtc_manager._rtc.set_date = MagicMock()
    rtc_manager._rtc.set_time = MagicMock()

    simulated_error = RuntimeError("Simulated set_date error")
    rtc_manager._rtc.set_date.side_effect = simulated_error

    year, month, date, hour, minute, second, weekday = 2025, 5, 4, 11, 30, 0, 5

    rtc_manager.set_time(year, month, date, hour, minute, second, weekday)

    rtc_manager._rtc.set_date.assert_called_once_with(year, month, date, weekday)
    rtc_manager._rtc.set_time.assert_not_called()  # Should not be called if set_date fails
    mock_logger.error.assert_called_once_with("Error setting RTC time", simulated_error)


def test_set_time_failure_set_time(
    mock_rv3028, mock_i2c: MagicMock, mock_logger: MagicMock
) -> None:
    """Tests handling of exceptions during set_time.

    Args:
        mock_rv3028: Mocked RV3028 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    rtc_manager = RV3028Manager(mock_logger, mock_i2c)
    rtc_manager._rtc = MagicMock(spec=RV3028)
    rtc_manager._rtc.set_date = MagicMock()
    rtc_manager._rtc.set_time = MagicMock()

    simulated_error = RuntimeError("Simulated set_time error")
    rtc_manager._rtc.set_time.side_effect = simulated_error

    year, month, date, hour, minute, second, weekday = 2025, 5, 4, 11, 30, 0, 5

    rtc_manager.set_time(year, month, date, hour, minute, second, weekday)

    rtc_manager._rtc.set_date.assert_called_once_with(year, month, date, weekday)
    rtc_manager._rtc.set_time.assert_called_once_with(hour, minute, second)
    mock_logger.error.assert_called_once_with("Error setting RTC time", simulated_error)
