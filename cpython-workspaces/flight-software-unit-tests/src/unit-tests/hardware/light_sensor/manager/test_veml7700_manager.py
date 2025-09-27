"""Test the VEML7700Manager class."""

from typing import Generator
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from pysquared.hardware.exception import HardwareInitializationError
from pysquared.hardware.light_sensor.manager.veml7700 import VEML7700Manager
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
def mock_veml7700(mock_i2c: MagicMock) -> Generator[MagicMock, None, None]:
    """Mocks the VEML7700 class.

    Args:
        mock_i2c: Mocked I2C bus.

    Yields:
        A MagicMock instance of VEML7700.
    """
    with patch(
        "pysquared.hardware.light_sensor.manager.veml7700.VEML7700"
    ) as mock_class:
        mock_instance = MagicMock()
        mock_instance.light = 1000.0
        mock_instance.lux = 500.0
        mock_instance.autolux = 250.0
        mock_instance.light_integration_time = None
        mock_instance.light_shutdown = False
        mock_class.return_value = mock_instance
        yield mock_class


def test_create_light_sensor(mock_veml7700, mock_i2c, mock_logger):
    """Tests successful creation of a VEML7700 light sensor instance.

    Args:
        mock_veml7700: Mocked VEML7700 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    light_sensor = VEML7700Manager(mock_logger, mock_i2c)

    assert light_sensor._light_sensor is not None
    mock_logger.debug.assert_called_once_with("Initializing light sensor")


def test_create_light_sensor_failed(mock_veml7700, mock_i2c, mock_logger):
    """Tests that initialization fails when VEML7700 cannot be created.

    Args:
        mock_veml7700: Mocked VEML7700 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    mock_veml7700.side_effect = Exception("Simulated VEML7700 failure")

    # Verify that HardwareInitializationError is raised
    with pytest.raises(HardwareInitializationError):
        _ = VEML7700Manager(mock_logger, mock_i2c)

    # Verify that the logger was called
    mock_logger.debug.assert_called_with("Initializing light sensor")


def test_create_light_sensor_with_custom_integration_time(
    mock_veml7700, mock_i2c, mock_logger
):
    """Tests successful creation with custom integration time.

    Args:
        mock_veml7700: Mocked VEML7700 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    # Mock the VEML7700 class constant
    with patch(
        "pysquared.hardware.light_sensor.manager.veml7700.VEML7700"
    ) as mock_class:
        mock_class.ALS_100MS = 1
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance

        light_sensor = VEML7700Manager(mock_logger, mock_i2c, integration_time=1)

        assert light_sensor._light_sensor == mock_instance
        assert light_sensor._light_sensor.light_integration_time == 1
        mock_logger.debug.assert_called_once_with("Initializing light sensor")


def test_get_light_success(mock_veml7700, mock_i2c, mock_logger):
    """Tests successful retrieval of the light reading.

    Args:
        mock_veml7700: Mocked VEML7700 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    light_sensor = VEML7700Manager(mock_logger, mock_i2c)
    light_sensor._light_sensor = MagicMock()
    light_sensor._light_sensor.light = 1000.0

    light = light_sensor.get_light()
    assert isinstance(light, Light)
    assert light.value == pytest.approx(1000.0, rel=1e-6)


def test_get_light_failure(mock_veml7700, mock_i2c, mock_logger):
    """Tests handling of exceptions when retrieving the light reading.

    Args:
        mock_veml7700: Mocked VEML7700 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    light_sensor = VEML7700Manager(mock_logger, mock_i2c)

    # Configure the mock to raise an exception when accessing the light property
    mock_veml7700_instance = MagicMock()
    light_sensor._light_sensor = mock_veml7700_instance
    mock_veml7700_light_property = PropertyMock(
        side_effect=RuntimeError("Simulated retrieval error")
    )
    type(light_sensor._light_sensor).light = mock_veml7700_light_property

    with pytest.raises(SensorReadingUnknownError):
        light_sensor.get_light()


def test_get_lux_success(mock_veml7700, mock_i2c, mock_logger):
    """Tests successful retrieval of the lux reading.

    Args:
        mock_veml7700: Mocked VEML7700 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    light_sensor = VEML7700Manager(mock_logger, mock_i2c)
    light_sensor._light_sensor = MagicMock()
    light_sensor._light_sensor.lux = 500.0

    lux = light_sensor.get_lux()
    assert isinstance(lux, Lux)
    assert lux.value == pytest.approx(500.0, rel=1e-6)


def test_get_lux_failure(mock_veml7700, mock_i2c, mock_logger):
    """Tests handling of exceptions when retrieving the lux reading.

    Args:
        mock_veml7700: Mocked VEML7700 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    light_sensor = VEML7700Manager(mock_logger, mock_i2c)

    # Configure the mock to raise an exception when accessing the lux property
    mock_veml7700_instance = MagicMock()
    light_sensor._light_sensor = mock_veml7700_instance
    mock_veml7700_lux_property = PropertyMock(
        side_effect=RuntimeError("Simulated retrieval error")
    )
    type(light_sensor._light_sensor).lux = mock_veml7700_lux_property

    with pytest.raises(SensorReadingUnknownError):
        light_sensor.get_lux()


def test_get_auto_lux_success(mock_veml7700, mock_i2c, mock_logger):
    """Tests successful retrieval of the auto lux reading.

    Args:
        mock_veml7700: Mocked VEML7700 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    light_sensor = VEML7700Manager(mock_logger, mock_i2c)
    light_sensor._light_sensor = MagicMock()
    light_sensor._light_sensor.autolux = 250.0

    autolux = light_sensor.get_auto_lux()
    assert isinstance(autolux, Lux)
    assert autolux.value == pytest.approx(250.0, rel=1e-6)


def test_get_auto_lux_failure(mock_veml7700, mock_i2c, mock_logger):
    """Tests handling of exceptions when retrieving the auto lux reading.

    Args:
        mock_veml7700: Mocked VEML7700 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    light_sensor = VEML7700Manager(mock_logger, mock_i2c)

    # Configure the mock to raise an exception when accessing the autolux property
    mock_veml7700_instance = MagicMock()
    light_sensor._light_sensor = mock_veml7700_instance
    mock_veml7700_autolux_property = PropertyMock(
        side_effect=RuntimeError("Simulated retrieval error")
    )
    type(light_sensor._light_sensor).autolux = mock_veml7700_autolux_property

    with pytest.raises(SensorReadingUnknownError):
        light_sensor.get_auto_lux()


def test_reset_success(mock_veml7700, mock_i2c, mock_logger):
    """Tests successful reset of the light sensor.

    Args:
        mock_veml7700: Mocked VEML7700 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    with patch("time.sleep"):
        light_sensor = VEML7700Manager(mock_logger, mock_i2c)
        light_sensor._light_sensor = MagicMock()

        light_sensor.reset()

        # Verify the reset sequence
        assert light_sensor._light_sensor.light_shutdown is False
        mock_logger.debug.assert_called_with("Light sensor reset successfully")


def test_reset_failure(mock_veml7700, mock_i2c, mock_logger):
    """Tests handling of exceptions during reset.

    Args:
        mock_veml7700: Mocked VEML7700 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    light_sensor = VEML7700Manager(mock_logger, mock_i2c)

    # Configure the mock to raise an exception when setting light_shutdown
    mock_veml7700_instance = MagicMock()
    light_sensor._light_sensor = mock_veml7700_instance
    mock_veml7700_shutdown_property = PropertyMock(
        side_effect=RuntimeError("Simulated reset error")
    )
    type(light_sensor._light_sensor).light_shutdown = mock_veml7700_shutdown_property

    light_sensor.reset()
    mock_logger.error.assert_called_once()


def test_get_lux_zero_reading(mock_veml7700, mock_i2c, mock_logger):
    """Tests handling of zero lux reading (should raise SensorReadingValueError).

    Args:
        mock_veml7700: Mocked VEML7700 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    light_sensor = VEML7700Manager(mock_logger, mock_i2c)
    light_sensor._light_sensor = MagicMock()
    light_sensor._light_sensor.lux = 0.0

    with pytest.raises(SensorReadingValueError):
        light_sensor.get_lux()


def test_get_lux_none_reading(mock_veml7700, mock_i2c, mock_logger):
    """Tests handling of None lux reading (should raise SensorReadingValueError).

    Args:
        mock_veml7700: Mocked VEML7700 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    light_sensor = VEML7700Manager(mock_logger, mock_i2c)
    light_sensor._light_sensor = MagicMock()
    light_sensor._light_sensor.lux = None

    with pytest.raises(SensorReadingValueError):
        light_sensor.get_lux()


def test_get_auto_lux_zero_reading(mock_veml7700, mock_i2c, mock_logger):
    """Tests handling of zero auto lux reading (should raise SensorReadingValueError).

    Args:
        mock_veml7700: Mocked VEML7700 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    light_sensor = VEML7700Manager(mock_logger, mock_i2c)
    light_sensor._light_sensor = MagicMock()
    light_sensor._light_sensor.autolux = 0.0

    with pytest.raises(SensorReadingValueError):
        light_sensor.get_auto_lux()


def test_get_auto_lux_none_reading(mock_veml7700, mock_i2c, mock_logger):
    """Tests handling of None auto lux reading (should raise SensorReadingValueError).

    Args:
        mock_veml7700: Mocked VEML7700 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    light_sensor = VEML7700Manager(mock_logger, mock_i2c)
    light_sensor._light_sensor = MagicMock()
    light_sensor._light_sensor.autolux = None

    with pytest.raises(SensorReadingValueError):
        light_sensor.get_auto_lux()
