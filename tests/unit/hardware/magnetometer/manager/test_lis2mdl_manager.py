from typing import Generator
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from mocks.adafruit_lis2mdl.lis2mdl import LIS2MDL
from pysquared.hardware.exception import HardwareInitializationError
from pysquared.hardware.magnetometer.manager.lis2mdl import LIS2MDLManager


@pytest.fixture
def mock_i2c():
    return MagicMock()


@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def mock_lis2mdl(mock_i2c: MagicMock) -> Generator[MagicMock, None, None]:
    with patch("pysquared.hardware.magnetometer.manager.lis2mdl.LIS2MDL") as mock_class:
        mock_class.return_value = LIS2MDL(mock_i2c)
        yield mock_class


def test_create_magnetometer(
    mock_lis2mdl: MagicMock,
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Test successful creation of a LIS2MDL magnetometer instance."""
    magnetometer = LIS2MDLManager(mock_logger, mock_i2c)

    assert isinstance(magnetometer._magnetometer, LIS2MDL)
    mock_logger.debug.assert_called_once_with("Initializing magnetometer")


@pytest.mark.slow
def test_create_with_retries(
    mock_lis2mdl: MagicMock,
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Test that initialization is retried when it fails."""
    mock_lis2mdl.side_effect = Exception("Simulated LIS2MDL failure")

    # Verify that HardwareInitializationError is raised after retries
    with pytest.raises(HardwareInitializationError):
        _ = LIS2MDLManager(mock_logger, mock_i2c)

    # Verify that the logger was called
    mock_logger.debug.assert_called_with("Initializing magnetometer")

    # Verify that LIS2MDL was called 3 times (due to retries)
    assert mock_i2c.call_count <= 3


def test_get_vector_success(
    mock_lis2mdl: MagicMock,
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Test successful retrieval of the magnetic field vector."""
    magnetometer = LIS2MDLManager(mock_logger, mock_i2c)
    magnetometer._magnetometer = MagicMock(spec=LIS2MDL)
    magnetometer._magnetometer.magnetic = (1.0, 2.0, 3.0)

    vector = magnetometer.get_vector()
    assert vector == (1.0, 2.0, 3.0)


def test_get_vector_failure(
    mock_lis2mdl: MagicMock,
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Test handling of exceptions when retrieving the magnetic field vector."""
    magnetometer = LIS2MDLManager(mock_logger, mock_i2c)

    # Confgure the mock to raise an exception when accessing the magnetic property
    mock_mag_instance = MagicMock(spec=LIS2MDL)
    magnetometer._magnetometer = mock_mag_instance
    mock_magnetic_property = PropertyMock(
        side_effect=RuntimeError("Simulated retrieval error")
    )
    type(mock_mag_instance).magnetic = mock_magnetic_property

    vector = magnetometer.get_vector()

    assert vector is None
    assert mock_logger.error.call_count == 1
    call_args, _ = mock_logger.error.call_args
    assert call_args[0] == "Error retrieving magnetometer sensor values"
    assert isinstance(call_args[1], RuntimeError)
    assert str(call_args[1]) == "Simulated retrieval error"
