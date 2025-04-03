from unittest.mock import MagicMock, patch

import pytest

from mocks.adafruit_ina219.ina219 import INA219
from pysquared.hardware.exception import HardwareInitializationError
from pysquared.hardware.power_monitor.ina219.factory import INA219Factory

@pytest.fixture
def mock_i2c():
    """Mock I2C bus."""
    return MagicMock()

@pytest.fixture
def mock_address():
    """Mock I2C address."""
    return MagicMock()

@pytest.fixture
def mock_logger():
    """Mock logger."""
    return MagicMock()

def test_create_power_monitor(mock_i2c, mock_logger):
    """Test creating INA219 instance."""
    ina219_factory = INA219Factory(mock_i2c, mock_address)
    ina219 = ina219_factory.create(mock_logger)

    assert isinstance(ina219, INA219)
    assert ina219.i2c == mock_i2c
    assert ina219.addr == mock_address
    mock_logger.debug.assert_called_once_with("Creating INA219 instance")

@pytest.mark.slow
@patch("pysquared.hardware.power_monitor.ina219.factory.INA219")
def test_create_hardware_initialization_with_retries(mock_ina219, mock_i2c, mock_logger):
    """Test creating INA219 instance with retries."""
    mock_ina219.side_effect = HardwareInitializationError("Failed to initialize INA219")
    ina219_factory = INA219Factory(mock_i2c, mock_address)

    with pytest.raises(HardwareInitializationError):
        ina219_factory.create(mock_logger)

    mock_logger.debug.assert_called_with("Creating INA219 instance")
    assert mock_ina219.call_count <= 3