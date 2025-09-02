"""Unit tests for the INA219Manager class.

This module contains unit tests for the `INA219Manager` class, which manages
the INA219 power monitor. The tests cover initialization, successful data
retrieval, and error handling for bus voltage, shunt voltage, and current readings.
"""

# pyright: reportAttributeAccessIssue=false, reportOptionalMemberAccess=false, reportReturnType=false

from typing import Generator
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from mocks.adafruit_ina219.ina219 import INA219
from pysquared.hardware.exception import HardwareInitializationError
from pysquared.hardware.power_monitor.manager.ina219 import INA219Manager
from pysquared.sensor_reading.current import Current
from pysquared.sensor_reading.error import SensorReadingUnknownError
from pysquared.sensor_reading.voltage import Voltage

address: int = 123


@pytest.fixture
def mock_i2c():
    """Fixture for mock I2C bus."""
    return MagicMock()


@pytest.fixture
def mock_logger():
    """Fixture for mock Logger."""
    return MagicMock()


@pytest.fixture
def mock_ina219(mock_i2c: MagicMock) -> Generator[MagicMock, None, None]:
    """Mocks the INA219 class.

    Args:
        mock_i2c: Mocked I2C bus.

    Yields:
        A MagicMock instance of INA219.
    """
    with patch("pysquared.hardware.power_monitor.manager.ina219.INA219") as mock_class:
        mock_class.return_value = INA219(mock_i2c, address)
        yield mock_class


def test_create_power_monitor(mock_ina219, mock_i2c, mock_logger):
    """Tests successful creation of an INA219 power monitor instance.

    Args:
        mock_ina219: Mocked INA219 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    power_monitor = INA219Manager(mock_logger, mock_i2c, address, do_calibration=False)

    assert isinstance(power_monitor._ina219, INA219)
    mock_logger.debug.assert_called_once_with("Initializing INA219 power monitor")


def test_create_power_monitor_failed(mock_ina219, mock_i2c, mock_logger):
    """Tests that initialization is retried when it fails.

    Args:
        mock_ina219: Mocked INA219 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    mock_ina219.side_effect = Exception("Simulated INA219 failure")

    # Verify that HardwareInitializationError is raised after retries
    with pytest.raises(HardwareInitializationError):
        _ = INA219Manager(mock_logger, mock_i2c, address, do_calibration=False)

    # Verify that the logger was called
    mock_logger.debug.assert_called_with("Initializing INA219 power monitor")

    # Verify that INA219 was called 3 times (due to retries)
    assert mock_i2c.call_count <= 3


def test_get_bus_voltage_success(mock_ina219, mock_i2c, mock_logger):
    """Tests successful retrieval of the bus voltage.

    Args:
        mock_ina219: Mocked INA219 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    power_monitor = INA219Manager(mock_logger, mock_i2c, address, do_calibration=False)
    power_monitor._ina219 = MagicMock(spec=INA219)
    power_monitor._ina219.bus_voltage = MagicMock()
    power_monitor._ina219.bus_voltage = 3.3

    voltage = power_monitor.get_bus_voltage()
    assert isinstance(voltage, Voltage)
    assert voltage.value == pytest.approx(3.3, rel=1e-6)


def test_get_bus_voltage_failure(mock_ina219, mock_i2c, mock_logger):
    """Tests handling of exceptions when retrieving the bus voltage.

    Args:
        mock_ina219: Mocked INA219 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    power_monitor = INA219Manager(mock_logger, mock_i2c, address, do_calibration=False)

    # Configure the mock to raise an exception when accessing the bus_voltage property
    mock_ina219_instance = MagicMock(spec=INA219)
    power_monitor._ina219 = mock_ina219_instance
    mock_ina219_bus_voltage_property = PropertyMock(
        side_effect=RuntimeError("Simulated retrieval error")
    )
    type(power_monitor._ina219).bus_voltage = mock_ina219_bus_voltage_property

    with pytest.raises(SensorReadingUnknownError):
        power_monitor.get_bus_voltage()


def test_get_shunt_voltage_success(mock_ina219, mock_i2c, mock_logger):
    """Tests successful retrieval of the shunt voltage.

    Args:
        mock_ina219: Mocked INA219 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    power_monitor = INA219Manager(mock_logger, mock_i2c, address, do_calibration=False)
    power_monitor._ina219 = MagicMock(spec=INA219)
    power_monitor._ina219.shunt_voltage = MagicMock()
    power_monitor._ina219.shunt_voltage = 0.1

    voltage = power_monitor.get_shunt_voltage()
    assert isinstance(voltage, Voltage)
    assert voltage.value == pytest.approx(0.1, rel=1e-6)


def test_get_shunt_voltage_failure(mock_ina219, mock_i2c, mock_logger):
    """Tests handling of exceptions when retrieving the shunt voltage.

    Args:
        mock_ina219: Mocked INA219 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    power_monitor = INA219Manager(mock_logger, mock_i2c, address, do_calibration=False)

    # Configure the mock to raise an exception when accessing the shunt_voltage property
    mock_ina219_instance = MagicMock(spec=INA219)
    power_monitor._ina219 = mock_ina219_instance
    mock_ina219_shunt_voltage_property = PropertyMock(
        side_effect=RuntimeError("Simulated retrieval error")
    )
    type(power_monitor._ina219).shunt_voltage = mock_ina219_shunt_voltage_property

    with pytest.raises(SensorReadingUnknownError):
        power_monitor.get_shunt_voltage()


def test_get_current_success(mock_ina219, mock_i2c, mock_logger):
    """Tests successful retrieval of the current.

    Args:
        mock_ina219: Mocked INA219 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    power_monitor = INA219Manager(mock_logger, mock_i2c, address, do_calibration=False)
    power_monitor._ina219 = MagicMock(spec=INA219)
    power_monitor._ina219.current = MagicMock()
    power_monitor._ina219.current = 0.5

    current = power_monitor.get_current()
    assert isinstance(current, Current)
    assert current.value == pytest.approx(0.5, rel=1e-6)


def test_get_current_failure(mock_ina219, mock_i2c, mock_logger):
    """Tests handling of exceptions when retrieving the current.

    Args:
        mock_ina219: Mocked INA219 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    power_monitor = INA219Manager(mock_logger, mock_i2c, address, do_calibration=False)

    # Configure the mock to raise an exception when accessing the current property
    mock_ina219_instance = MagicMock(spec=INA219)
    power_monitor._ina219 = mock_ina219_instance
    mock_ina219_current_property = PropertyMock(
        side_effect=RuntimeError("Simulated retrieval error")
    )
    type(power_monitor._ina219).current = mock_ina219_current_property

    with pytest.raises(SensorReadingUnknownError):
        power_monitor.get_current()
