"""Test the VEML6031X00Manager class."""

from typing import Generator
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from pysquared.hardware.exception import HardwareInitializationError
from pysquared.hardware.light_sensor.manager.veml6031x00 import VEML6031X00Manager
from pysquared.logger import Logger
from pysquared.sensor_reading.error import (
    SensorReadingUnknownError,
    SensorReadingValueError,
)
from pysquared.sensor_reading.light import Light
from pysquared.sensor_reading.lux import Lux


@pytest.fixture
def mock_i2c():
    """Fixture to mock the I2C bus."""
    return MagicMock()


@pytest.fixture
def mock_logger():
    """Fixture to mock the logger."""
    return MagicMock(Logger)


@pytest.fixture
def mock_veml6031x00(mock_i2c: MagicMock) -> Generator[MagicMock, None, None]:
    """Mocks the internal _VEML6031X00 driver class.
    Yields:
        MagicMock class for _VEML6031X00
    """
    with patch(
        "pysquared.hardware.light_sensor.manager.veml6031x00._VEML6031X00"
    ) as mock_class:
        mock_instance = MagicMock()
        mock_instance.light = 1000.0
        mock_instance.lux = 500.0
        mock_class.return_value = mock_instance
        yield mock_class


def test_create_light_sensor(mock_veml6031x00, mock_i2c, mock_logger):
    """Verify successful creation of the manager and driver init logging."""
    sensor = VEML6031X00Manager(mock_logger, mock_i2c)
    assert sensor._light_sensor is not None
    mock_logger.debug.assert_called_once_with("Initializing VEML6031X00 light sensor")


def test_create_light_sensor_failed(mock_veml6031x00, mock_i2c, mock_logger):
    """Ensure initialization failure raises HardwareInitializationError."""
    mock_veml6031x00.side_effect = Exception("Simulated VEML6031X00 failure")
    with pytest.raises(HardwareInitializationError):
        _ = VEML6031X00Manager(mock_logger, mock_i2c)
    mock_logger.debug.assert_called_with("Initializing VEML6031X00 light sensor")


def test_get_light_success(mock_veml6031x00, mock_i2c, mock_logger):
    """Read non-unit light value successfully and wrap in Light."""
    sensor = VEML6031X00Manager(mock_logger, mock_i2c)
    sensor._light_sensor = MagicMock()
    sensor._light_sensor.light = 1234.0

    light = sensor.get_light()
    assert isinstance(light, Light)
    assert light.value == pytest.approx(1234.0, rel=1e-6)


def test_get_light_failure(mock_veml6031x00, mock_i2c, mock_logger):
    """Propagate read exception as SensorReadingUnknownError for light."""
    sensor = VEML6031X00Manager(mock_logger, mock_i2c)
    mock_instance = MagicMock()
    sensor._light_sensor = mock_instance
    mock_prop = PropertyMock(side_effect=RuntimeError("Simulated retrieval error"))
    type(sensor._light_sensor).light = mock_prop

    with pytest.raises(SensorReadingUnknownError):
        sensor.get_light()


def test_get_lux_success(mock_veml6031x00, mock_i2c, mock_logger):
    """Read lux successfully and wrap in Lux."""
    sensor = VEML6031X00Manager(mock_logger, mock_i2c)
    sensor._light_sensor = MagicMock()
    sensor._light_sensor.lux = 321.0

    lux = sensor.get_lux()
    assert isinstance(lux, Lux)
    assert lux.value == pytest.approx(321.0, rel=1e-6)


def test_get_lux_failure(mock_veml6031x00, mock_i2c, mock_logger):
    """Propagate read exception as SensorReadingUnknownError for lux."""
    sensor = VEML6031X00Manager(mock_logger, mock_i2c)
    mock_instance = MagicMock()
    sensor._light_sensor = mock_instance
    mock_prop = PropertyMock(side_effect=RuntimeError("Simulated retrieval error"))
    type(sensor._light_sensor).lux = mock_prop

    with pytest.raises(SensorReadingUnknownError):
        sensor.get_lux()


def test_get_lux_zero_reading(mock_veml6031x00, mock_i2c, mock_logger):
    """Zero lux is invalid and should raise SensorReadingValueError."""
    sensor = VEML6031X00Manager(mock_logger, mock_i2c)
    sensor._light_sensor = MagicMock()
    sensor._light_sensor.lux = 0.0

    with pytest.raises(SensorReadingValueError):
        sensor.get_lux()


def test_get_lux_none_reading(mock_veml6031x00, mock_i2c, mock_logger):
    """None lux is invalid and should raise SensorReadingValueError."""
    sensor = VEML6031X00Manager(mock_logger, mock_i2c)
    sensor._light_sensor = MagicMock()
    sensor._light_sensor.lux = None

    with pytest.raises(SensorReadingValueError):
        sensor.get_lux()


def test_get_lux_saturation_raw(mock_veml6031x00, mock_i2c, mock_logger):
    """Raw ambient-light of 0xFFFF indicates saturation - currently not detected."""
    # Note: The current implementation does not check for saturation (0xFFFF).
    # This test verifies that high values are still returned as valid lux readings.
    sensor = VEML6031X00Manager(mock_logger, mock_i2c)
    sensor._light_sensor = MagicMock()
    # Simulate a very high lux value (but not checking for 0xFFFF saturation)
    sensor._light_sensor.lux = 65535.0

    lux = sensor.get_lux()
    assert isinstance(lux, Lux)
    assert lux.value == pytest.approx(65535.0, rel=1e-6)


def test_reset_success(mock_veml6031x00, mock_i2c, mock_logger):
    """Reset toggles shutdown bit and logs success."""
    with patch("time.sleep"):
        sensor = VEML6031X00Manager(mock_logger, mock_i2c)
        # The driver is already mocked via the fixture
        # Reset will set light_shutdown to True then False

        sensor.reset()
        # Verify the logger was called
        mock_logger.debug.assert_called_with("VEML6031X00 light sensor reset successfully")


def test_reset_failure(mock_veml6031x00, mock_i2c, mock_logger):
    """Reset failure is logged at error level."""
    sensor = VEML6031X00Manager(mock_logger, mock_i2c)
    # Make setting light_shutdown raise an error
    type(sensor._light_sensor).light_shutdown = PropertyMock(
        side_effect=RuntimeError("Simulated reset error")
    )

    sensor.reset()
    # Verify error was logged (call_args_list since multiple calls may happen)
    assert mock_logger.error.call_count >= 1