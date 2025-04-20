from typing import Generator
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from mocks.adafruit_ina219.ina219 import INA219
from pysquared.hardware.exception import HardwareInitializationError
from pysquared.hardware.power_monitor.manager.ina219 import INA219Manager

address: int = 123


@pytest.fixture
def mock_i2c():
    return MagicMock()


@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def mock_ina219(mock_i2c: MagicMock) -> Generator[MagicMock, None, None]:
    with patch("pysquared.hardware.power_monitor.manager.ina219.INA219") as mock_class:
        mock_class.return_value = INA219(mock_i2c, address)
        yield mock_class


def test_create_power_monitor(mock_ina219, mock_i2c, mock_logger):
    """Test successful creation of an INA219 power monitor instance."""
    power_monitor = INA219Manager(mock_logger, mock_i2c, address)

    assert isinstance(power_monitor._ina219, INA219)
    mock_logger.debug.assert_called_once_with("Initializing INA219 power monitor")


@pytest.mark.slow
def test_create_with_retries(mock_ina219, mock_i2c, mock_logger):
    """Test that initialization is retried when it fails."""
    mock_ina219.side_effect = Exception("Simulated INA219 failure")

    # Verify that HardwareInitializationError is raised after retries
    with pytest.raises(HardwareInitializationError):
        _ = INA219Manager(mock_logger, mock_i2c, address)

    # Verify that the logger was called
    mock_logger.debug.assert_called_with("Initializing INA219 power monitor")

    # Verify that INA219 was called 3 times (due to retries)
    assert mock_i2c.call_count <= 3


def test_get_bus_voltage_success(mock_ina219, mock_i2c, mock_logger):
    """Test successful retrieval of the bus voltage."""
    power_monitor = INA219Manager(mock_logger, mock_i2c, address)
    power_monitor._ina219 = MagicMock(spec=INA219)
    power_monitor._ina219.bus_voltage = MagicMock()
    power_monitor._ina219.bus_voltage = 3.3

    voltage = power_monitor.get_bus_voltage()
    assert voltage == pytest.approx(3.3, rel=1e-6)


def test_get_bus_voltage_failure(mock_ina219, mock_i2c, mock_logger):
    """Test handling of exceptions when retrieving the bus voltage."""
    power_monitor = INA219Manager(mock_logger, mock_i2c, address)

    # Configure the mock to raise an exception when accessing the bus_voltage property
    mock_ina219_instance = MagicMock(spec=INA219)
    power_monitor._ina219 = mock_ina219_instance
    mock_ina219_bus_voltage_property = PropertyMock(
        side_effect=RuntimeError("Simulated retrieval error")
    )
    type(power_monitor._ina219).bus_voltage = mock_ina219_bus_voltage_property

    voltage = power_monitor.get_bus_voltage()
    assert voltage is None


def test_get_shunt_voltage_success(mock_ina219, mock_i2c, mock_logger):
    """Test successful retrieval of the shunt voltage."""
    power_monitor = INA219Manager(mock_logger, mock_i2c, address)
    power_monitor._ina219 = MagicMock(spec=INA219)
    power_monitor._ina219.shunt_voltage = MagicMock()
    power_monitor._ina219.shunt_voltage = 0.1

    voltage = power_monitor.get_shunt_voltage()
    assert voltage == pytest.approx(0.1, rel=1e-6)


def test_get_shunt_voltage_failure(mock_ina219, mock_i2c, mock_logger):
    """Test handling of exceptions when retrieving the shunt voltage."""
    power_monitor = INA219Manager(mock_logger, mock_i2c, address)

    # Configure the mock to raise an exception when accessing the shunt_voltage property
    mock_ina219_instance = MagicMock(spec=INA219)
    power_monitor._ina219 = mock_ina219_instance
    mock_ina219_shunt_voltage_property = PropertyMock(
        side_effect=RuntimeError("Simulated retrieval error")
    )
    type(power_monitor._ina219).shunt_voltage = mock_ina219_shunt_voltage_property

    voltage = power_monitor.get_shunt_voltage()
    assert voltage is None


def test_get_current_success(mock_ina219, mock_i2c, mock_logger):
    """Test successful retrieval of the current."""
    power_monitor = INA219Manager(mock_logger, mock_i2c, address)
    power_monitor._ina219 = MagicMock(spec=INA219)
    power_monitor._ina219.current = MagicMock()
    power_monitor._ina219.current = 0.5

    current = power_monitor.get_current()
    assert current == pytest.approx(0.5, rel=1e-6)


def test_get_current_failure(mock_ina219, mock_i2c, mock_logger):
    """Test handling of exceptions when retrieving the current."""
    power_monitor = INA219Manager(mock_logger, mock_i2c, address)

    # Configure the mock to raise an exception when accessing the current property
    mock_ina219_instance = MagicMock(spec=INA219)
    power_monitor._ina219 = mock_ina219_instance
    mock_ina219_current_property = PropertyMock(
        side_effect=RuntimeError("Simulated retrieval error")
    )
    type(power_monitor._ina219).current = mock_ina219_current_property

    current = power_monitor.get_current()
    assert current is None
