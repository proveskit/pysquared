from unittest.mock import MagicMock, patch

import pytest

from mocks.rv3028 import RV3028  # Mock RTC class
from pysquared.hardware.exception import HardwareInitializationError
from pysquared.rtc.rv3028.factory import RV3028Factory

# Type hinting only
try:
    from busio import I2C

    from pysquared.logger import Logger
except ImportError:
    pass


@pytest.fixture
def mock_i2c() -> MagicMock:
    """Fixture for mock I2C bus."""
    return MagicMock(spec=I2C)


@pytest.fixture
def mock_logger() -> MagicMock:
    """Fixture for mock Logger."""
    return MagicMock(spec=Logger)


def test_create_rtc(mock_i2c: MagicMock, mock_logger: MagicMock) -> None:
    """Test successful creation of an RV3028 RTC instance."""
    rtc_factory = RV3028Factory(mock_logger, mock_i2c)

    assert isinstance(rtc_factory._rtc, RV3028)
    mock_logger.debug.assert_called_once_with("Initializing RTC")


@pytest.mark.slow
@patch("pysquared.rtc.rv3028.factory.RV3028")
def test_create_with_retries(
    mock_rv3028: MagicMock,
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Test that initialization is retried when it fails."""
    mock_rv3028.side_effect = Exception("Simulated RV3028 failure")

    with pytest.raises(HardwareInitializationError):
        _ = RV3028Factory(mock_logger, mock_i2c)

    mock_logger.debug.assert_called_with("Initializing RTC")
    # Verify that RV3028 constructor was called up to 3 times (due to retries)
    assert mock_rv3028.call_count <= 3


def test_set_time_success(mock_i2c: MagicMock, mock_logger: MagicMock) -> None:
    """Test successful setting of the time."""
    rtc_factory = RV3028Factory(mock_logger, mock_i2c)

    rtc_factory._rtc = MagicMock(spec=RV3028)
    rtc_factory._rtc.set_date = MagicMock()
    rtc_factory._rtc.set_time = MagicMock()

    year, month, date, hour, minute, second, weekday = 2025, 5, 4, 11, 30, 0, 5

    rtc_factory.set_time(year, month, date, hour, minute, second, weekday)

    rtc_factory._rtc.set_date.assert_called_once_with(year, month, date, weekday)
    rtc_factory._rtc.set_time.assert_called_once_with(hour, minute, second)
    mock_logger.error.assert_not_called()


def test_set_time_failure_set_date(mock_i2c: MagicMock, mock_logger: MagicMock) -> None:
    """Test handling of exceptions during set_date."""
    rtc_factory = RV3028Factory(mock_logger, mock_i2c)
    rtc_factory._rtc = MagicMock(spec=RV3028)
    rtc_factory._rtc.set_date = MagicMock()
    rtc_factory._rtc.set_time = MagicMock()

    simulated_error = RuntimeError("Simulated set_date error")
    rtc_factory._rtc.set_date.side_effect = simulated_error

    year, month, date, hour, minute, second, weekday = 2025, 5, 4, 11, 30, 0, 5

    rtc_factory.set_time(year, month, date, hour, minute, second, weekday)

    rtc_factory._rtc.set_date.assert_called_once_with(year, month, date, weekday)
    rtc_factory._rtc.set_time.assert_not_called()  # Should not be called if set_date fails
    mock_logger.error.assert_called_once_with("Error setting RTC time", simulated_error)


def test_set_time_failure_set_time(mock_i2c: MagicMock, mock_logger: MagicMock) -> None:
    """Test handling of exceptions during set_time."""
    rtc_factory = RV3028Factory(mock_logger, mock_i2c)
    rtc_factory._rtc = MagicMock(spec=RV3028)
    rtc_factory._rtc.set_date = MagicMock()
    rtc_factory._rtc.set_time = MagicMock()

    simulated_error = RuntimeError("Simulated set_time error")
    rtc_factory._rtc.set_time.side_effect = simulated_error

    year, month, date, hour, minute, second, weekday = 2025, 5, 4, 11, 30, 0, 5

    rtc_factory.set_time(year, month, date, hour, minute, second, weekday)

    rtc_factory._rtc.set_date.assert_called_once_with(year, month, date, weekday)
    rtc_factory._rtc.set_time.assert_called_once_with(hour, minute, second)
    mock_logger.error.assert_called_once_with("Error setting RTC time", simulated_error)
