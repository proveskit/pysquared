"""Test the VEML7700Manager class."""

import sys
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from pysquared.hardware.exception import HardwareInitializationError
from pysquared.hardware.light_sensor.manager.veml7700 import VEML7700Manager


@pytest.fixture
def mock_veml7700():
    """Fixture to mock the VEML7700 sensor."""
    mock = MagicMock()
    mock.light = 1000.0
    mock.lux = 500.0
    mock.autolux = 250.0
    return mock


@pytest.fixture
def mock_i2c():
    """Fixture to mock the I2C bus."""
    return MagicMock()


@pytest.fixture
def mock_logger():
    """Fixture to mock the logger."""
    return MagicMock()


def test_veml7700_manager_initialization(mock_logger, mock_i2c):
    """Test the initialization of the VEML7700Manager."""
    with patch(
        "pysquared.hardware.light_sensor.manager.veml7700.VEML7700",
        return_value=MagicMock(),
    ) as mock_sensor:
        manager = VEML7700Manager(mock_logger, mock_i2c)
        mock_sensor.assert_called_once_with(mock_i2c)
        assert manager._light_sensor.light_integration_time is not None
        mock_logger.debug.assert_called_with("Initializing light sensor")


def test_veml7700_manager_initialization_error(mock_logger, mock_i2c):
    """Test the initialization of the VEML7700Manager with a hardware error."""
    with patch(
        "pysquared.hardware.light_sensor.manager.veml7700.VEML7700",
        side_effect=Exception("I2C Error"),
    ):
        with pytest.raises(HardwareInitializationError) as excinfo:
            VEML7700Manager(mock_logger, mock_i2c)
        assert "Failed to initialize light sensor" in str(excinfo.value)


def test_get_light(mock_logger, mock_i2c, mock_veml7700):
    """Test the get_light method."""
    with patch(
        "pysquared.hardware.light_sensor.manager.veml7700.VEML7700",
        return_value=mock_veml7700,
    ):
        manager = VEML7700Manager(mock_logger, mock_i2c)
        assert manager.get_light() == 1000.0
        mock_veml7700.light = 0.0
        assert manager.get_light() == 0.0


def test_get_light_error(mock_logger, mock_i2c, mock_veml7700):
    """Test the get_light method with an error."""
    type(mock_veml7700).light = PropertyMock(side_effect=Exception("Sensor Error"))
    with patch(
        "pysquared.hardware.light_sensor.manager.veml7700.VEML7700",
        return_value=mock_veml7700,
    ):
        manager = VEML7700Manager(mock_logger, mock_i2c)
        assert manager.get_light() is None
        mock_logger.error.assert_called_once()


def test_get_lux(mock_logger, mock_i2c, mock_veml7700):
    """Test the get_lux method."""
    with patch(
        "pysquared.hardware.light_sensor.manager.veml7700.VEML7700",
        return_value=mock_veml7700,
    ):
        manager = VEML7700Manager(mock_logger, mock_i2c)
        assert manager.get_lux() == 500.0


def test_get_lux_error(mock_logger, mock_i2c, mock_veml7700):
    """Test the get_lux method with an error."""
    type(mock_veml7700).lux = PropertyMock(side_effect=Exception("Sensor Error"))
    with patch(
        "pysquared.hardware.light_sensor.manager.veml7700.VEML7700",
        return_value=mock_veml7700,
    ):
        manager = VEML7700Manager(mock_logger, mock_i2c)
        assert manager.get_lux() is None
        mock_logger.error.assert_called_once()


def test_get_auto_lux(mock_logger, mock_i2c, mock_veml7700):
    """Test the get_auto_lux method."""
    with patch(
        "pysquared.hardware.light_sensor.manager.veml7700.VEML7700",
        return_value=mock_veml7700,
    ):
        manager = VEML7700Manager(mock_logger, mock_i2c)
        assert manager.get_auto_lux() == 250.0


def test_get_auto_lux_error(mock_logger, mock_i2c, mock_veml7700):
    """Test the get_auto_lux method with an error."""
    type(mock_veml7700).autolux = PropertyMock(side_effect=Exception("Sensor Error"))
    with patch(
        "pysquared.hardware.light_sensor.manager.veml7700.VEML7700",
        return_value=mock_veml7700,
    ):
        manager = VEML7700Manager(mock_logger, mock_i2c)
        assert manager.get_auto_lux() is None
        mock_logger.error.assert_called_once()


def test_self_test_pass(mock_logger, mock_i2c, mock_veml7700):
    """Test the self_test method for a pass case."""
    with patch(
        "pysquared.hardware.light_sensor.manager.veml7700.VEML7700",
        return_value=mock_veml7700,
    ):
        manager = VEML7700Manager(mock_logger, mock_i2c)
        assert manager.self_test() is True
        assert manager.is_valid is True
        mock_logger.debug.assert_called_with("Light sensor self-test passed")


def test_self_test_fail_reading_zero(mock_logger, mock_i2c, mock_veml7700):
    """Test the self_test method for a fail case with a zero reading."""
    mock_veml7700.autolux = 0.0
    with patch(
        "pysquared.hardware.light_sensor.manager.veml7700.VEML7700",
        return_value=mock_veml7700,
    ):
        manager = VEML7700Manager(mock_logger, mock_i2c)
        assert manager.self_test() is False
        assert manager.is_valid is False
        mock_logger.warning.assert_called_with(
            "Light sensor self-test failed: No valid reading"
        )


def test_self_test_fail_reading_none(mock_logger, mock_i2c, mock_veml7700):
    """Test the self_test method for a fail case with a None reading."""
    mock_veml7700.autolux = None
    with (
        patch(
            "pysquared.hardware.light_sensor.manager.veml7700.VEML7700",
            return_value=mock_veml7700,
        ),
        patch(
            "pysquared.hardware.light_sensor.manager.veml7700.VEML7700Manager.get_auto_lux",
            return_value=None,
        ),
    ):
        manager = VEML7700Manager(mock_logger, mock_i2c)
        assert manager.self_test() is False
        assert manager.is_valid is False
        mock_logger.warning.assert_called_with(
            "Light sensor self-test failed: No valid reading"
        )


def test_self_test_fail_exception(mock_logger, mock_i2c, mock_veml7700):
    """Test the self_test method for a fail case with an exception."""
    with patch(
        "pysquared.hardware.light_sensor.manager.veml7700.VEML7700Manager.get_auto_lux",
        return_value=None,
    ):
        manager = VEML7700Manager(mock_logger, mock_i2c)
        assert not manager.self_test()
        mock_logger.warning.assert_called_with(
            "Light sensor self-test failed: No valid reading"
        )


def test_reset(mock_logger, mock_i2c, mock_veml7700):
    """Test the reset method."""
    with (
        patch(
            "pysquared.hardware.light_sensor.manager.veml7700.VEML7700",
            return_value=mock_veml7700,
        ),
        patch("time.sleep"),
    ):
        manager = VEML7700Manager(mock_logger, mock_i2c)
        manager.reset()
        assert mock_veml7700.light_shutdown is False
        mock_logger.debug.assert_called_with("Light sensor reset successfully")


def test_reset_error(mock_logger, mock_i2c, mock_veml7700):
    """Test the reset method with an error."""
    type(mock_veml7700).light_shutdown = PropertyMock(
        side_effect=Exception("Reset Error")
    )
    with patch(
        "pysquared.hardware.light_sensor.manager.veml7700.VEML7700",
        return_value=mock_veml7700,
    ):
        manager = VEML7700Manager(mock_logger, mock_i2c)
        manager.reset()
        mock_logger.error.assert_called_once()
        (
            (
                error_msg,
                exception_arg,
            ),
            _,
        ) = mock_logger.error.call_args
        assert error_msg == "Failed to reset light sensor:"
        assert isinstance(exception_arg, Exception)
        assert str(exception_arg) == "Reset Error"


sys.modules["adafruit_veml7700"] = MagicMock()
