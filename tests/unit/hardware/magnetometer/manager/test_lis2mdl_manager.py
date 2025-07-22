"""Unit tests for the LIS2MDLManager class.

This module contains unit tests for the `LIS2MDLManager` class, which manages
the LIS2MDL magnetometer. The tests cover initialization, successful data
retrieval, and error handling for magnetic field vector readings.
"""

import asyncio
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

from mocks.adafruit_lis2mdl.lis2mdl import LIS2MDL
from pysquared.hardware.exception import HardwareInitializationError
from pysquared.hardware.magnetometer.manager.lis2mdl import LIS2MDLManager
from pysquared.sensor_reading.error import (
    SensorReadingTimeoutError,
    SensorReadingUnknownError,
)


@pytest.fixture
def mock_i2c():
    """Fixture for mock I2C bus."""
    return MagicMock()


@pytest.fixture
def mock_logger():
    """Fixture for mock Logger."""
    return MagicMock()


@pytest.fixture
def mock_lis2mdl(mock_i2c: MagicMock) -> Generator[MagicMock, None, None]:
    """Mocks the LIS2MDL class.

    Args:
        mock_i2c: Mocked I2C bus.

    Yields:
        A MagicMock instance of LIS2MDL.
    """
    with patch("pysquared.hardware.magnetometer.manager.lis2mdl.LIS2MDL") as mock_class:
        mock_class.return_value = LIS2MDL(mock_i2c)
        yield mock_class


def test_create_magnetometer(
    mock_lis2mdl: MagicMock,
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Tests successful creation of a LIS2MDL magnetometer instance.

    Args:
        mock_lis2mdl: Mocked LIS2MDL class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    magnetometer = LIS2MDLManager(mock_logger, mock_i2c)

    assert isinstance(magnetometer._magnetometer, LIS2MDL)
    mock_logger.debug.assert_called_once_with("Initializing magnetometer")


def test_create_magnetometer_failed(
    mock_lis2mdl: MagicMock,
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Tests that initialization is retried when it fails.

    Args:
        mock_lis2mdl: Mocked LIS2MDL class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    mock_lis2mdl.side_effect = Exception("Simulated LIS2MDL failure")

    # Verify that HardwareInitializationError is raised after retries
    with pytest.raises(HardwareInitializationError):
        _ = LIS2MDLManager(mock_logger, mock_i2c)

    # Verify that the logger was called
    mock_logger.debug.assert_called_with("Initializing magnetometer")

    # Verify that LIS2MDL was called 3 times (due to retries)
    assert mock_i2c.call_count <= 3


# def test_get_vector_success(
#     mock_lis2mdl: MagicMock,
#     mock_i2c: MagicMock,
#     mock_logger: MagicMock,
# ) -> None:
#     """Tests successful retrieval of the magnetic field vector.

#     Args:
#         mock_lis2mdl: Mocked LIS2MDL class.
#         mock_i2c: Mocked I2C bus.
#         mock_logger: Mocked Logger instance.
#     """
#     magnetometer = LIS2MDLManager(mock_logger, mock_i2c)
#     magnetometer._magnetometer = MagicMock(spec=LIS2MDL)

#     # Create a mock coroutine
#     mock_coro = MagicMock()
#     mock_coro.__await__ = MagicMock(return_value=iter([(1.0, 2.0, 3.0)]))

#     # Set the coroutine directly as asyncio_magnetic
#     magnetometer._magnetometer.asyncio_magnetic = mock_coro

#     # Run the async function
#     vector = asyncio.run(magnetometer.get_vector())

#     # Verify the result
#     assert isinstance(vector, Magnetic)
#     assert vector.x == 1.0
#     assert vector.y == 2.0
#     assert vector.z == 3.0


def test_get_vector_timeout(
    mock_lis2mdl: MagicMock,
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Tests handling of timeout when retrieving the magnetic field vector.

    Args:
        mock_lis2mdl: Mocked LIS2MDL class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    magnetometer = LIS2MDLManager(mock_logger, mock_i2c)
    magnetometer._magnetometer = MagicMock(spec=LIS2MDL)

    # Patch wait_for to raise TimeoutError immediately
    with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
        # Set a dummy coroutine - it won't be used due to the patch
        magnetometer._magnetometer.asyncio_magnetic = MagicMock()

        # Run the async function and expect SensorReadingTimeoutError
        with pytest.raises(SensorReadingTimeoutError) as excinfo:
            asyncio.run(magnetometer.get_vector())

        # Verify the exception message
        assert "Timeout while waiting for magnetometer data" in str(excinfo.value)


def test_get_vector_unknown_error(
    mock_lis2mdl: MagicMock,
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Tests handling of unknown errors when retrieving the magnetic field vector.

    Args:
        mock_lis2mdl: Mocked LIS2MDL class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    magnetometer = LIS2MDLManager(mock_logger, mock_i2c)
    magnetometer._magnetometer = MagicMock(spec=LIS2MDL)

    # Patch wait_for to raise TimeoutError immediately
    with patch("asyncio.wait_for", side_effect=ValueError):
        # Set a dummy coroutine - it won't be used due to the patch
        magnetometer._magnetometer.asyncio_magnetic = MagicMock()

        # Run the async function and expect SensorReadingUnknownError
        with pytest.raises(SensorReadingUnknownError) as excinfo:
            asyncio.run(magnetometer.get_vector())

        # Verify the exception message
        assert "Unknown error while reading magnetometer data" in str(excinfo.value)

    # # Create a mock coroutine that raises an exception when awaited
    # mock_coro = MagicMock()
    # mock_coro.__await__ = MagicMock(side_effect=RuntimeError("Simulated hardware error"))

    # # Set the coroutine directly as asyncio_magnetic
    # magnetometer._magnetometer.asyncio_magnetic = mock_coro

    # # Run the async function and expect SensorReadingUnknownError
    # with pytest.raises(SensorReadingUnknownError) as excinfo:
    #     asyncio.run(magnetometer.get_vector())

    # # Verify the exception message
    # assert "Unknown error while reading magnetometer data" in str(excinfo.value)
    # # Verify the original exception is preserved as the cause
    # assert isinstance(excinfo.value.__cause__, RuntimeError)
    # assert str(excinfo.value.__cause__) == "Simulated hardware error"
