"""Unit tests for the LIS2MDLManager class.

This module contains unit tests for the `LIS2MDLManager` class, which manages
the LIS2MDL magnetometer. The tests cover initialization, successful data
retrieval, and error handling for magnetic field vector readings.
"""

from typing import Generator
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from pysquared.hardware.exception import HardwareInitializationError
from pysquared.hardware.magnetometer.manager.lis2mdl import LIS2MDLManager
from pysquared.sensor_reading.error import (
    SensorReadingUnknownError,
)
from pysquared.sensor_reading.magnetic import Magnetic


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
        mock_class.return_value = MagicMock()
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

    assert magnetometer._magnetometer == mock_lis2mdl.return_value
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


def test_get_magnetic_field_success(
    mock_lis2mdl: MagicMock,
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Tests successful retrieval of the magnetic field vector.

    Args:
        mock_lis2mdl: Mocked LIS2MDL class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    magnetometer = LIS2MDLManager(mock_logger, mock_i2c)
    magnetometer._magnetometer = MagicMock()

    def mock_magnetic():
        """Mock magnetic field vector."""
        return (1.0, 2.0, 3.0)

    magnetometer._magnetometer.magnetic = mock_magnetic()

    vector = magnetometer.get_magnetic_field()

    # Verify the result
    assert isinstance(vector, Magnetic)
    assert vector.x == 1.0
    assert vector.y == 2.0
    assert vector.z == 3.0


def test_get_magnetic_field_unknown_error(
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
    magnetometer._magnetometer = MagicMock()

    # Configure the magnetic property to raise an exception when accessed
    type(magnetometer._magnetometer).magnetic = PropertyMock(
        side_effect=Exception("test exception")
    )

    with pytest.raises(SensorReadingUnknownError) as excinfo:
        magnetometer.get_magnetic_field()

    # Verify the exception message
    assert "Unknown error while reading magnetometer data" in str(excinfo.value)
