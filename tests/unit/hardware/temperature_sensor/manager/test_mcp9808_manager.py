"""Tests for the MCP9808Manager class."""

from typing import Generator
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from mocks.adafruit_mcp9808.mcp9808 import MCP9808
from pysquared.hardware.exception import HardwareInitializationError
from pysquared.hardware.temperature_sensor.manager.mcp9808 import MCP9808Manager
from pysquared.logger import Logger

address: int = 123


@pytest.fixture
def mock_logger():
    """Creates a mock logger for testing.

    Returns:
        MagicMock: A mock logger instance.
    """
    return MagicMock(spec=Logger)


@pytest.fixture
def mock_i2c():
    """Creates a mock I2C bus for testing.

    Returns:
        MagicMock: A mock I2C bus instance.
    """
    return MagicMock()


@pytest.fixture
def mock_mcp9808(mock_i2c: MagicMock) -> Generator[MagicMock, None, None]:
    """Mocks the MCP9808 class.

    Args:
        mock_i2c: Mocked I2C bus.

    Yields:
        A MagicMock instance of MCP9808.
    """
    with patch(
        "pysquared.hardware.temperature_sensor.manager.mcp9808.MCP9808"
    ) as mock_class:
        mock_class.return_value = MCP9808(mock_i2c, address)
        yield mock_class


def test_create_temperature_sensor(mock_mcp9808, mock_i2c, mock_logger):
    """Tests successful creation of an MCP9808 temperature sensor instance.

    Args:
        mock_mcp9808: Mocked MCP9808 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    temp_sensor = MCP9808Manager(mock_logger, mock_i2c, address)

    assert isinstance(temp_sensor._mcp9808, MCP9808)
    mock_logger.debug.assert_called_once_with("Initializing MCP9808 temperature sensor")


def test_create_temperature_sensor_failed(mock_mcp9808, mock_i2c, mock_logger):
    """Tests that initialization fails when MCP9808 cannot be created.

    Args:
        mock_mcp9808: Mocked MCP9808 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    mock_mcp9808.side_effect = Exception("Simulated MCP9808 failure")

    # Verify that HardwareInitializationError is raised
    with pytest.raises(HardwareInitializationError):
        _ = MCP9808Manager(mock_logger, mock_i2c, address)

    # Verify that the logger was called
    mock_logger.debug.assert_called_with("Initializing MCP9808 temperature sensor")


def test_create_temperature_sensor_with_custom_resolution(
    mock_mcp9808, mock_i2c, mock_logger
):
    """Tests successful creation with custom resolution.

    Args:
        mock_mcp9808: Mocked MCP9808 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    mock_instance = MagicMock(spec=MCP9808)
    mock_mcp9808.return_value = mock_instance

    temp_sensor = MCP9808Manager(mock_logger, mock_i2c, address, resolution=3)

    assert temp_sensor._mcp9808 == mock_instance
    assert temp_sensor._mcp9808.resolution == 3
    mock_logger.debug.assert_called_once_with("Initializing MCP9808 temperature sensor")


def test_get_temperature_success(mock_mcp9808, mock_i2c, mock_logger):
    """Tests successful retrieval of the temperature.

    Args:
        mock_mcp9808: Mocked MCP9808 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    temp_sensor = MCP9808Manager(mock_logger, mock_i2c, address)
    temp_sensor._mcp9808 = MagicMock(spec=MCP9808)
    temp_sensor._mcp9808.temperature = 25.5

    temperature = temp_sensor.get_temperature()
    assert temperature == pytest.approx(25.5, rel=1e-6)


def test_get_temperature_negative_value(mock_mcp9808, mock_i2c, mock_logger):
    """Tests successful retrieval of negative temperature.

    Args:
        mock_mcp9808: Mocked MCP9808 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    temp_sensor = MCP9808Manager(mock_logger, mock_i2c, address)
    temp_sensor._mcp9808 = MagicMock(spec=MCP9808)
    temp_sensor._mcp9808.temperature = -10.5

    temperature = temp_sensor.get_temperature()
    assert temperature == pytest.approx(-10.5, rel=1e-6)


def test_get_temperature_high_value(mock_mcp9808, mock_i2c, mock_logger):
    """Tests successful retrieval of high temperature value.

    Args:
        mock_mcp9808: Mocked MCP9808 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    temp_sensor = MCP9808Manager(mock_logger, mock_i2c, address)
    temp_sensor._mcp9808 = MagicMock(spec=MCP9808)
    temp_sensor._mcp9808.temperature = 85.0

    temperature = temp_sensor.get_temperature()
    assert temperature == pytest.approx(85.0, rel=1e-6)


def test_get_temperature_failure(mock_mcp9808, mock_i2c, mock_logger):
    """Tests handling of exceptions when retrieving the temperature.

    Args:
        mock_mcp9808: Mocked MCP9808 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    temp_sensor = MCP9808Manager(mock_logger, mock_i2c, address)

    # Configure the mock to raise an exception when accessing the temperature property
    mock_mcp9808_instance = MagicMock(spec=MCP9808)
    temp_sensor._mcp9808 = mock_mcp9808_instance
    mock_mcp9808_temperature_property = PropertyMock(
        side_effect=RuntimeError("Simulated retrieval error")
    )
    type(temp_sensor._mcp9808).temperature = mock_mcp9808_temperature_property

    temperature = temp_sensor.get_temperature()
    assert temperature is None
    mock_logger.error.assert_called_once()
