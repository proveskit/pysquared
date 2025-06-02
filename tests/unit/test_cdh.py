"""
Unit tests for the CommandDataHandler class, specifically focusing on the update_config functionality.
"""

import sys
from unittest.mock import Mock

import pytest

from pysquared.cdh import CommandDataHandler
from pysquared.config.config import Config
from pysquared.logger import Logger
from pysquared.protos.radio import RadioProto

# Mock CircuitPython modules before any imports that might use them
sys.modules["alarm"] = Mock()
sys.modules["alarm.time"] = Mock()
sys.modules["alarm.time.TimeAlarm"] = Mock()
sys.modules["microcontroller"] = Mock()
sys.modules["pysquared.satellite"] = Mock()


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    return Mock(spec=Logger)


@pytest.fixture
def mock_radio():
    """Create a mock radio for testing."""
    return Mock(spec=RadioProto)


@pytest.fixture
def mock_config():
    """Create a mock config for testing using real configuration keys."""
    config = Mock(spec=Config)
    config.CONFIG_SCHEMA = {
        "cubesat_name": {"type": str, "min_length": 1, "max_length": 10},
        "sleep_duration": {"type": int, "min": 1, "max": 86400},
        "detumble_enable_z": {"type": bool, "allowed_values": [True, False]},
        "detumble_enable_x": {"type": bool, "allowed_values": [True, False]},
        "detumble_enable_y": {"type": bool, "allowed_values": [True, False]},
        "debug": {"type": bool, "allowed_values": [True, False]},
        "heating": {"type": bool, "allowed_values": [True, False]},
        "normal_temp": {"type": int, "min": 5, "max": 40},
        "normal_battery_temp": {"type": int, "min": 1, "max": 35},
        "normal_micro_temp": {"type": int, "min": 1, "max": 50},
        "normal_charge_current": {"type": float, "min": 0.0, "max": 2000.0},
        "normal_battery_voltage": {"type": float, "min": 6.0, "max": 8.4},
        "critical_battery_voltage": {"type": float, "min": 5.4, "max": 7.2},
        "reboot_time": {"type": int, "min": 3600, "max": 604800},
        "turbo_clock": {"type": bool, "allowed_values": [True, False]},
    }
    config.joke_reply = ["Joke 1", "Joke 2"]
    config.super_secret_code = "ABCD"
    config.repeat_code = "RP"
    config.radio = Mock()
    return config


@pytest.fixture
def cdh(mock_logger, mock_radio, mock_config):
    """Create a CommandDataHandler instance for testing."""
    return CommandDataHandler(config=mock_config, logger=mock_logger, radio=mock_radio)


class TestUpdateConfig:
    """Test cases for the update_config method."""

    def test_successful_temporary_update(self, cdh, mock_config):
        """Test successful temporary update of a config value."""
        # Arrange
        key = "sleep_duration"
        value = 60
        temporary = True

        # Act
        cdh.update_config(key, value, temporary)

        # Assert
        mock_config.update_config.assert_called_once_with(key, value, temporary)

    def test_successful_permanent_update(self, cdh, mock_config):
        """Test successful permanent update of a config value."""
        # Arrange
        key = "normal_temp"
        value = 25
        temporary = False

        # Act
        cdh.update_config(key, value, temporary)

        # Assert
        mock_config.update_config.assert_called_once_with(key, value, temporary)

    def test_key_error(self, cdh, mock_config, mock_logger):
        """Test KeyError when updating non-existent config key."""
        # Arrange
        key = "non_existent_key"
        value = 50
        temporary = False
        mock_config.update_config.side_effect = KeyError("Key not found")

        # Act
        cdh.update_config(key, value, temporary)

        # Assert
        mock_logger.error.assert_called_once()
        assert "Value not in config or immutable" in mock_logger.error.call_args[0][0]

    def test_type_error(self, cdh, mock_config, mock_logger):
        """Test TypeError when updating with wrong value type."""
        # Arrange
        key = "sleep_duration"
        value = "not_an_integer"  # Should be int
        temporary = False
        mock_config.update_config.side_effect = TypeError("Invalid type")

        # Act
        cdh.update_config(key, value, temporary)

        # Assert
        mock_logger.error.assert_called_once()
        assert "Value type incorrect" in mock_logger.error.call_args[0][0]

    def test_value_error(self, cdh, mock_config, mock_logger):
        """Test ValueError when updating with out-of-range value."""
        # Arrange
        key = "normal_temp"
        value = 150  # Outside max range of 40
        temporary = False
        mock_config.update_config.side_effect = ValueError("Value out of range")

        # Act
        cdh.update_config(key, value, temporary)

        # Assert
        mock_logger.error.assert_called_once()
        assert "Value not in acceptable range" in mock_logger.error.call_args[0][0]

    def test_empty_key_value(self, cdh, mock_config, mock_logger):
        """Test updating with empty key/value."""
        # Arrange
        key = ""
        value = 50
        temporary = False
        # Simulate KeyError for empty key
        mock_config.update_config.side_effect = KeyError("Key not in config")

        # Act
        cdh.update_config(key, value, temporary)

        # Assert
        mock_logger.error.assert_called_once()
        assert "Value not in config or immutable" in mock_logger.error.call_args[0][0]

    def test_none_values(self, cdh, mock_config, mock_logger):
        """Test updating with None values."""
        # Arrange
        key = None
        value = None
        temporary = False
        # Simulate KeyError for None key
        mock_config.update_config.side_effect = KeyError("Key not in config")

        # Act
        cdh.update_config(key, value, temporary)

        # Assert
        mock_logger.error.assert_called_once()
        assert "Value not in config or immutable" in mock_logger.error.call_args[0][0]

    def test_boundary_values(self, cdh, mock_config):
        """Test updating with maximum/minimum allowed values."""
        # Arrange
        key = "normal_temp"
        min_value = 5
        max_value = 40
        temporary = False

        # Act & Assert
        # Test minimum value
        cdh.update_config(key, min_value, temporary)
        mock_config.update_config.assert_called_with(key, min_value, temporary)

        # Test maximum value
        cdh.update_config(key, max_value, temporary)
        mock_config.update_config.assert_called_with(key, max_value, temporary)

    def test_multiple_updates(self, cdh, mock_config):
        """Test updating multiple values in sequence."""
        # Arrange
        updates = [
            ("sleep_duration", 60, False),
            ("cubesat_name", "TestSat", True),
            ("debug", True, False),
        ]

        # Act
        for key, value, temporary in updates:
            cdh.update_config(key, value, temporary)

        # Assert
        assert mock_config.update_config.call_count == len(updates)
        for i, (key, value, temporary) in enumerate(updates):
            assert mock_config.update_config.call_args_list[i] == (
                (key, value, temporary),
            )

    def test_radio_config_update(self, cdh, mock_config, mock_logger):
        """Test updating radio configuration values."""
        # Arrange
        key = "transmit_frequency"
        value = 437.5
        temporary = False

        # Simulate radio.validate being called inside update_config
        def update_config_side_effect(k, v, t):
            mock_config.radio.validate(k, v)

        mock_config.update_config.side_effect = update_config_side_effect

        # Act
        cdh.update_config(key, value, temporary)

        # Assert
        mock_config.radio.validate.assert_called_once_with(key, value)
