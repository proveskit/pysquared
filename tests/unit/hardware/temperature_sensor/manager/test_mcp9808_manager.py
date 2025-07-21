"""Tests for the MCP9808Manager class."""

from unittest.mock import MagicMock, patch

import pytest

from mocks.adafruit_mcp9808.mcp9808 import MCP9808
from pysquared.hardware.exception import HardwareInitializationError
from pysquared.hardware.temperature_sensor.manager.mcp9808 import MCP9808Manager
from pysquared.logger import Logger


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


class MockMCP9808WithError(MCP9808):
    """Mock MCP9808 that raises an exception when temperature is accessed."""

    def __init__(self, i2c, addr, error_to_raise):
        """Initialize the mock with I2C bus and address."""
        super().__init__(i2c, addr)
        self._error_to_raise = error_to_raise

    @property
    def temperature(self):
        """Raise the specified exception when accessed."""
        raise self._error_to_raise


class MockMCP9808WithTemperature(MCP9808):
    """Mock MCP9808 with configurable temperature value."""

    def __init__(self, i2c, addr, temperature_value):
        """Initialize the mock with I2C bus, address and temperature value."""
        super().__init__(i2c, addr)
        self._temperature_value = temperature_value

    @property
    def temperature(self):
        """Return the configured temperature value."""
        return self._temperature_value


class TestMCP9808Manager:
    """Test cases for the MCP9808Manager class."""

    def test_init_success(
        self,
        mock_logger: MagicMock,
        mock_i2c: MagicMock,
    ):
        """Tests successful initialization of MCP9808Manager.

        Args:
            mock_logger: Mocked Logger instance.
            mock_i2c: Mocked I2C bus.
        """
        with patch(
            "pysquared.hardware.temperature_sensor.manager.mcp9808.MCP9808"
        ) as mock_mcp9808_class:
            mock_mcp9808_instance = MCP9808(mock_i2c, 0x18)
            mock_mcp9808_class.return_value = mock_mcp9808_instance

            manager = MCP9808Manager(mock_logger, mock_i2c, 0x18)

            assert manager._log == mock_logger
            assert manager._mcp9808 == mock_mcp9808_instance
            mock_logger.debug.assert_called_once_with(
                "Initializing MCP9808 temperature sensor"
            )
            mock_mcp9808_class.assert_called_once_with(mock_i2c, 0x18)

    def test_init_default_address(
        self,
        mock_logger: MagicMock,
        mock_i2c: MagicMock,
    ):
        """Tests initialization with default I2C address.

        Args:
            mock_logger: Mocked Logger instance.
            mock_i2c: Mocked I2C bus.
        """
        with patch(
            "pysquared.hardware.temperature_sensor.manager.mcp9808.MCP9808"
        ) as mock_mcp9808_class:
            mock_mcp9808_instance = MCP9808(mock_i2c, 0x18)
            mock_mcp9808_class.return_value = mock_mcp9808_instance

            _ = MCP9808Manager(mock_logger, mock_i2c)

            mock_mcp9808_class.assert_called_once_with(mock_i2c, 0x18)

    def test_init_failure(
        self,
        mock_logger: MagicMock,
        mock_i2c: MagicMock,
    ):
        """Tests initialization failure handling.

        Args:
            mock_logger: Mocked Logger instance.
            mock_i2c: Mocked I2C bus.
        """
        with patch(
            "pysquared.hardware.temperature_sensor.manager.mcp9808.MCP9808"
        ) as mock_mcp9808_class:
            init_error = RuntimeError("I2C communication failed")
            mock_mcp9808_class.side_effect = init_error

            with pytest.raises(HardwareInitializationError) as exc_info:
                MCP9808Manager(mock_logger, mock_i2c, 0x18)

            assert "Failed to initialize MCP9808 temperature sensor" in str(
                exc_info.value
            )
            assert exc_info.value.__cause__ == init_error

    def test_get_temperature_success(
        self,
        mock_logger: MagicMock,
        mock_i2c: MagicMock,
    ):
        """Tests successful temperature reading.

        Args:
            mock_logger: Mocked Logger instance.
            mock_i2c: Mocked I2C bus.
        """
        expected_temperature = 25.5

        with patch(
            "pysquared.hardware.temperature_sensor.manager.mcp9808.MCP9808"
        ) as mock_mcp9808_class:
            mock_mcp9808_instance = MCP9808(mock_i2c, 0x18)
            mock_mcp9808_instance.temperature = expected_temperature
            mock_mcp9808_class.return_value = mock_mcp9808_instance

            manager = MCP9808Manager(mock_logger, mock_i2c, 0x18)
            temperature = manager.get_temperature()

        assert temperature == expected_temperature

    def test_get_temperature_exception(
        self,
        mock_logger: MagicMock,
        mock_i2c: MagicMock,
    ):
        """Tests temperature reading exception handling.

        Args:
            mock_logger: Mocked Logger instance.
            mock_i2c: Mocked I2C bus.
        """
        read_error = RuntimeError("Sensor read failed")

        with patch(
            "pysquared.hardware.temperature_sensor.manager.mcp9808.MCP9808"
        ) as mock_mcp9808_class:
            mock_mcp9808_instance = MockMCP9808WithError(mock_i2c, 0x18, read_error)
            mock_mcp9808_class.return_value = mock_mcp9808_instance

            manager = MCP9808Manager(mock_logger, mock_i2c, 0x18)
            temperature = manager.get_temperature()

        assert temperature is None
        mock_logger.error.assert_called_once_with(
            "Error retrieving MCP9808 temperature sensor values", read_error
        )

    def test_get_temperature_none_value(
        self,
        mock_logger: MagicMock,
        mock_i2c: MagicMock,
    ):
        """Tests temperature reading when sensor returns None.

        Args:
            mock_logger: Mocked Logger instance.
            mock_i2c: Mocked I2C bus.
        """
        with patch(
            "pysquared.hardware.temperature_sensor.manager.mcp9808.MCP9808"
        ) as mock_mcp9808_class:
            mock_mcp9808_instance = MockMCP9808WithTemperature(mock_i2c, 0x18, None)
            mock_mcp9808_class.return_value = mock_mcp9808_instance

            manager = MCP9808Manager(mock_logger, mock_i2c, 0x18)
            temperature = manager.get_temperature()

        assert temperature is None

    def test_get_temperature_negative_value(
        self,
        mock_logger: MagicMock,
        mock_i2c: MagicMock,
    ):
        """Tests temperature reading with negative temperature value.

        Args:
            mock_logger: Mocked Logger instance.
            mock_i2c: Mocked I2C bus.
        """
        expected_temperature = -10.5

        with patch(
            "pysquared.hardware.temperature_sensor.manager.mcp9808.MCP9808"
        ) as mock_mcp9808_class:
            mock_mcp9808_instance = MockMCP9808WithTemperature(
                mock_i2c, 0x18, expected_temperature
            )
            mock_mcp9808_class.return_value = mock_mcp9808_instance

            manager = MCP9808Manager(mock_logger, mock_i2c, 0x18)
            temperature = manager.get_temperature()

        assert temperature == expected_temperature

    def test_get_temperature_high_value(
        self,
        mock_logger: MagicMock,
        mock_i2c: MagicMock,
    ):
        """Tests temperature reading with high temperature value.

        Args:
            mock_logger: Mocked Logger instance.
            mock_i2c: Mocked I2C bus.
        """
        expected_temperature = 85.0

        with patch(
            "pysquared.hardware.temperature_sensor.manager.mcp9808.MCP9808"
        ) as mock_mcp9808_class:
            mock_mcp9808_instance = MockMCP9808WithTemperature(
                mock_i2c, 0x18, expected_temperature
            )
            mock_mcp9808_class.return_value = mock_mcp9808_instance

            manager = MCP9808Manager(mock_logger, mock_i2c, 0x18)
            temperature = manager.get_temperature()

        assert temperature == expected_temperature
