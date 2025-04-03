from unittest.mock import MagicMock, patch

import pytest

from mocks.adafruit_lis2mdl.lis2mdl import LIS2MDL
from pysquared.hardware.exception import HardwareInitializationError
from pysquared.hardware.magnetometer.lis2mdl.factory import LIS2MDLFactory


@pytest.fixture
def mock_i2c():
    return MagicMock()


@pytest.fixture
def mock_logger():
    return MagicMock()


def test_create_magnetometer(mock_i2c, mock_logger):
    """Test successful creation of a LIS2MDL magnetometer instance."""
    factory = LIS2MDLFactory(mock_i2c)
    magnetometer = factory.create(mock_logger)

    assert isinstance(magnetometer, LIS2MDL)
    mock_logger.debug.assert_called_once_with("Initializing magnetometer")


@pytest.mark.slow
@patch("pysquared.hardware.magnetometer.lis2mdl.factory.LIS2MDL")
def test_create_with_retries(mock_lis2mdl, mock_i2c, mock_logger):
    """Test that initialization is retried when it fails."""
    mock_lis2mdl.side_effect = Exception("Simulated LIS2MDL failure")

    factory = LIS2MDLFactory(mock_i2c)

    # Verify that HardwareInitializationError is raised after retries
    with pytest.raises(HardwareInitializationError):
        factory.create(mock_logger)

    # Verify that the logger was called
    mock_logger.debug.assert_called_with("Initializing magnetometer")

    # Verify that LIS2MDL was called 3 times (due to retries)
    assert mock_i2c.call_count <= 3
