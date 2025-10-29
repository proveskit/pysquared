"""Tests for TMP112Manager."""

from typing import Generator
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from pysquared.hardware.exception import HardwareInitializationError
from pysquared.hardware.temperature_sensor.manager.tmp112 import TMP112Manager
from pysquared.logger import Logger
from pysquared.sensor_reading.error import SensorReadingUnknownError
from pysquared.sensor_reading.temperature import Temperature


@pytest.fixture
def mock_i2c():
    """Fixture providing a mocked I2C bus."""
    return MagicMock()


@pytest.fixture
def mock_logger():
    """Fixture providing a mocked Logger."""
    return MagicMock(Logger)


@pytest.fixture
def mock_tmp112(mock_i2c: MagicMock) -> Generator[MagicMock, None, None]:
    """Patch the internal driver class used by the manager."""
    with patch(
        "pysquared.hardware.temperature_sensor.manager.tmp112._TMP112"
    ) as mock_class:
        mock_instance = MagicMock()
        mock_instance.temperature = 25.0
        mock_class.return_value = mock_instance
        yield mock_class


def test_create_temperature_sensor(mock_tmp112, mock_i2c, mock_logger):
    """Manager constructs the driver and logs initialization."""
    mgr = TMP112Manager(mock_logger, mock_i2c)
    assert mgr._sensor is not None
    mock_logger.debug.assert_called_once_with("Initializing temperature sensor")


def test_create_temperature_sensor_failed(mock_tmp112, mock_i2c, mock_logger):
    """Driver init errors are surfaced as HardwareInitializationError."""
    mock_tmp112.side_effect = Exception("Simulated TMP112 failure")
    with pytest.raises(HardwareInitializationError):
        _ = TMP112Manager(mock_logger, mock_i2c)
    mock_logger.debug.assert_called_with("Initializing temperature sensor")


def test_get_temperature_success(mock_tmp112, mock_i2c, mock_logger):
    """Successful temperature read returns Temperature reading."""
    mgr = TMP112Manager(mock_logger, mock_i2c)
    mgr._sensor = MagicMock()
    type(mgr._sensor).temperature = PropertyMock(return_value=36.5)

    temp = mgr.get_temperature()
    assert isinstance(temp, Temperature)
    assert temp.value == pytest.approx(36.5, rel=1e-6)


def test_get_temperature_failure(mock_tmp112, mock_i2c, mock_logger):
    """Errors while reading are wrapped as SensorReadingUnknownError."""
    mgr = TMP112Manager(mock_logger, mock_i2c)
    sensor = MagicMock()
    type(sensor).temperature = PropertyMock(side_effect=RuntimeError("read error"))
    mgr._sensor = sensor

    with pytest.raises(SensorReadingUnknownError):
        mgr.get_temperature()
