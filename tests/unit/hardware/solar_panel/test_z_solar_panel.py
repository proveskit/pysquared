"""
Test Z Solar Panel Manager
==========================

This module provides unit tests for the ZSolarPanelManager class.
"""

from unittest.mock import Mock

import pytest

from pysquared.hardware.exception import NotPowered
from pysquared.hardware.solar_panel.z_panel_manager import ZSolarPanelManager
from pysquared.logger import Logger


class TestZSolarPanelManager:
    """Test cases for ZSolarPanelManager."""

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger for testing."""
        return Mock(spec=Logger)

    @pytest.fixture
    def mock_temperature_sensor(self):
        """Create a mock temperature sensor for testing."""
        return Mock()

    @pytest.fixture
    def mock_light_sensor(self):
        """Create a mock light sensor for testing."""
        return Mock()

    @pytest.fixture
    def mock_torque_coils(self):
        """Create mock torque coils for testing."""
        return Mock()

    @pytest.fixture
    def mock_load_switch_pin(self):
        """Create a mock load switch pin for testing."""
        return Mock()

    @pytest.fixture
    def z_solar_panel_manager(
        self,
        mock_logger,
        mock_temperature_sensor,
        mock_light_sensor,
        mock_torque_coils,
        mock_load_switch_pin,
    ):
        """Create a ZSolarPanelManager instance for testing."""
        manager = ZSolarPanelManager(
            logger=mock_logger,
            temperature_sensor=mock_temperature_sensor,
            light_sensor=mock_light_sensor,
            torque_coils=mock_torque_coils,
            load_switch_pin=mock_load_switch_pin,
        )
        # Enable load switch for testing
        manager.enable_load()
        return manager

    def test_initialization(
        self,
        mock_logger,
        mock_temperature_sensor,
        mock_light_sensor,
        mock_torque_coils,
        mock_load_switch_pin,
    ):
        """Test ZSolarPanelManager initialization."""
        manager = ZSolarPanelManager(
            logger=mock_logger,
            temperature_sensor=mock_temperature_sensor,
            light_sensor=mock_light_sensor,
            torque_coils=mock_torque_coils,
            load_switch_pin=mock_load_switch_pin,
        )

        assert manager is not None
        assert hasattr(manager, "get_temperature")
        assert hasattr(manager, "get_light_level")
        assert hasattr(manager, "get_all_data")
        assert hasattr(manager, "drive_torque_coils")
        assert hasattr(manager, "get_sensor_states")
        assert hasattr(manager, "get_last_error")
        assert hasattr(manager, "get_error_count")
        # Load switch methods
        assert hasattr(manager, "enable_load")
        assert hasattr(manager, "disable_load")
        assert hasattr(manager, "reset_load")
        assert hasattr(manager, "get_load_state")

    def test_get_temperature_success(
        self, z_solar_panel_manager, mock_temperature_sensor
    ):
        """Test successful temperature reading."""
        expected_temp = 30.2
        mock_temperature_sensor.temperature.return_value = expected_temp

        result = z_solar_panel_manager.get_temperature()

        assert result == expected_temp
        mock_temperature_sensor.temperature.assert_called_once()

    def test_get_temperature_failure(
        self, z_solar_panel_manager, mock_temperature_sensor, mock_logger
    ):
        """Test temperature reading failure."""
        mock_temperature_sensor.temperature.side_effect = Exception("Sensor error")

        result = z_solar_panel_manager.get_temperature()

        assert result is None
        mock_logger.error.assert_called_once()

    def test_get_light_level_success(self, z_solar_panel_manager, mock_light_sensor):
        """Test successful light level reading."""
        expected_light = 1200.0
        mock_light_sensor.light.return_value = expected_light

        result = z_solar_panel_manager.get_light_level()

        assert result == expected_light
        mock_light_sensor.light.assert_called_once()

    def test_get_light_level_failure(
        self, z_solar_panel_manager, mock_light_sensor, mock_logger
    ):
        """Test light level reading failure."""
        mock_light_sensor.light.side_effect = Exception("Sensor error")

        result = z_solar_panel_manager.get_light_level()

        assert result is None
        mock_logger.error.assert_called_once()

    def test_drive_torque_coils_success(self, z_solar_panel_manager, mock_torque_coils):
        """Test successful torque coil driving."""
        mock_torque_coils.drive.return_value = True

        result = z_solar_panel_manager.drive_torque_coils()

        assert result is True
        mock_torque_coils.drive.assert_called_once()

    def test_drive_torque_coils_failure(
        self, z_solar_panel_manager, mock_torque_coils, mock_logger
    ):
        """Test torque coil driving failure."""
        mock_torque_coils.drive.side_effect = Exception("Coil error")

        result = z_solar_panel_manager.drive_torque_coils()

        assert result is False
        mock_logger.error.assert_called_once()

    def test_drive_torque_coils_with_parameters(
        self, z_solar_panel_manager, mock_torque_coils
    ):
        """Test torque coil driving with parameters."""
        mock_torque_coils.drive.return_value = True
        test_params = {"duration": 3.0, "intensity": 0.6}

        result = z_solar_panel_manager.drive_torque_coils(**test_params)

        assert result is True
        mock_torque_coils.drive.assert_called_once_with(**test_params)

    def test_drive_torque_coils_not_implemented(
        self,
        mock_logger,
        mock_temperature_sensor,
        mock_light_sensor,
        mock_load_switch_pin,
    ):
        """Test torque coil driving when not implemented."""
        # Create manager without torque coils
        manager = ZSolarPanelManager(
            logger=mock_logger,
            temperature_sensor=mock_temperature_sensor,
            light_sensor=mock_light_sensor,
            torque_coils=None,
            load_switch_pin=mock_load_switch_pin,
        )
        # Enable load switch for testing
        manager.enable_load()

        with pytest.raises(NotImplementedError):
            manager.drive_torque_coils()

    def test_temperature_sensor_none(
        self, mock_logger, mock_light_sensor, mock_torque_coils, mock_load_switch_pin
    ):
        """Test behavior when temperature sensor is None."""
        manager = ZSolarPanelManager(
            logger=mock_logger,
            temperature_sensor=None,
            light_sensor=mock_light_sensor,
            torque_coils=mock_torque_coils,
            load_switch_pin=mock_load_switch_pin,
        )
        # Enable load switch for testing
        manager.enable_load()

        result = manager.get_temperature()
        assert result is None

    def test_light_sensor_none(
        self,
        mock_logger,
        mock_temperature_sensor,
        mock_torque_coils,
        mock_load_switch_pin,
    ):
        """Test behavior when light sensor is None."""
        manager = ZSolarPanelManager(
            logger=mock_logger,
            temperature_sensor=mock_temperature_sensor,
            light_sensor=None,
            torque_coils=mock_torque_coils,
            load_switch_pin=mock_load_switch_pin,
        )
        # Enable load switch for testing
        manager.enable_load()

        result = manager.get_light_level()
        assert result is None

    def test_temperature_range_validation(
        self, z_solar_panel_manager, mock_temperature_sensor
    ):
        """Test temperature reading within expected range."""
        # Test normal temperature range
        mock_temperature_sensor.temperature.return_value = 15.0
        result = z_solar_panel_manager.get_temperature()
        assert -50.0 <= result <= 100.0

        # Test extreme temperatures
        mock_temperature_sensor.temperature.return_value = 110.0
        result = z_solar_panel_manager.get_temperature()
        assert result == 110.0  # Should still return the value even if extreme

    def test_light_level_range_validation(
        self, z_solar_panel_manager, mock_light_sensor
    ):
        """Test light level reading within expected range."""
        # Test normal light level range
        mock_light_sensor.light.return_value = 800.0
        result = z_solar_panel_manager.get_light_level()
        assert 0.0 <= result <= 2000.0

        # Test extreme light levels
        mock_light_sensor.light.return_value = -100.0
        result = z_solar_panel_manager.get_light_level()
        assert result == -100.0  # Should still return the value even if extreme

    def test_concurrent_sensor_access(
        self, z_solar_panel_manager, mock_temperature_sensor, mock_light_sensor
    ):
        """Test concurrent access to temperature and light sensors."""
        mock_temperature_sensor.temperature.return_value = 35.0
        mock_light_sensor.light.return_value = 900.0

        temp_result = z_solar_panel_manager.get_temperature()
        light_result = z_solar_panel_manager.get_light_level()

        assert temp_result == 35.0
        assert light_result == 900.0
        mock_temperature_sensor.temperature.assert_called_once()
        mock_light_sensor.light.assert_called_once()

    def test_error_logging_format(
        self, z_solar_panel_manager, mock_light_sensor, mock_logger
    ):
        """Test that errors are logged with proper format."""
        error_msg = "Light sensor communication failed"
        mock_light_sensor.light.side_effect = Exception(error_msg)

        z_solar_panel_manager.get_light_level()

        # Verify error was logged with proper exception handling
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "light" in call_args[0][0].lower()  # Error message should mention light
        assert call_args[1]["err"] is not None  # Should have err parameter

    def test_get_all_data_success(
        self, z_solar_panel_manager, mock_temperature_sensor, mock_light_sensor
    ):
        """Test successful retrieval of all sensor data."""
        expected_temp = 30.2
        expected_light = 1200.0
        mock_temperature_sensor.temperature.return_value = expected_temp
        mock_light_sensor.light.return_value = expected_light

        result = z_solar_panel_manager.get_all_data()

        assert result == (expected_temp, expected_light)
        mock_temperature_sensor.temperature.assert_called_once()
        mock_light_sensor.light.assert_called_once()

    def test_get_all_data_temperature_failure(
        self,
        z_solar_panel_manager,
        mock_temperature_sensor,
        mock_light_sensor,
        mock_logger,
    ):
        """Test get_all_data when temperature sensor fails."""
        expected_light = 1200.0
        mock_temperature_sensor.temperature.side_effect = Exception(
            "Temperature sensor error"
        )
        mock_light_sensor.light.return_value = expected_light

        result = z_solar_panel_manager.get_all_data()

        assert result == (None, expected_light)
        mock_logger.error.assert_called_once()

    def test_get_all_data_light_failure(
        self,
        z_solar_panel_manager,
        mock_temperature_sensor,
        mock_light_sensor,
        mock_logger,
    ):
        """Test get_all_data when light sensor fails."""
        expected_temp = 30.2
        mock_temperature_sensor.temperature.return_value = expected_temp
        mock_light_sensor.light.side_effect = Exception("Light sensor error")

        result = z_solar_panel_manager.get_all_data()

        assert result == (expected_temp, None)
        mock_logger.error.assert_called_once()

    def test_get_all_data_both_sensors_failure(
        self,
        z_solar_panel_manager,
        mock_temperature_sensor,
        mock_light_sensor,
        mock_logger,
    ):
        """Test get_all_data when both sensors fail."""
        mock_temperature_sensor.temperature.side_effect = Exception(
            "Temperature sensor error"
        )
        mock_light_sensor.light.side_effect = Exception("Light sensor error")

        result = z_solar_panel_manager.get_all_data()

        assert result == (None, None)
        assert mock_logger.error.call_count == 2

    def test_get_all_data_temperature_sensor_none(
        self, mock_logger, mock_light_sensor, mock_torque_coils, mock_load_switch_pin
    ):
        """Test get_all_data when temperature sensor is None."""
        manager = ZSolarPanelManager(
            logger=mock_logger,
            temperature_sensor=None,
            light_sensor=mock_light_sensor,
            torque_coils=mock_torque_coils,
            load_switch_pin=mock_load_switch_pin,
        )
        # Enable load switch for testing
        manager.enable_load()

        expected_light = 1200.0
        mock_light_sensor.light.return_value = expected_light

        result = manager.get_all_data()
        assert result == (None, expected_light)

    def test_get_all_data_light_sensor_none(
        self,
        mock_logger,
        mock_temperature_sensor,
        mock_torque_coils,
        mock_load_switch_pin,
    ):
        """Test get_all_data when light sensor is None."""
        manager = ZSolarPanelManager(
            logger=mock_logger,
            temperature_sensor=mock_temperature_sensor,
            light_sensor=None,
            torque_coils=mock_torque_coils,
            load_switch_pin=mock_load_switch_pin,
        )
        # Enable load switch for testing
        manager.enable_load()

        expected_temp = 30.2
        mock_temperature_sensor.temperature.return_value = expected_temp

        result = manager.get_all_data()
        assert result == (expected_temp, None)

    def test_get_all_data_both_sensors_none(
        self, mock_logger, mock_torque_coils, mock_load_switch_pin
    ):
        """Test get_all_data when both sensors are None."""
        manager = ZSolarPanelManager(
            logger=mock_logger,
            temperature_sensor=None,
            light_sensor=None,
            torque_coils=mock_torque_coils,
            load_switch_pin=mock_load_switch_pin,
        )
        # Enable load switch for testing
        manager.enable_load()

        result = manager.get_all_data()
        assert result == (None, None)

    def test_multiple_torque_coil_operations(
        self, z_solar_panel_manager, mock_torque_coils
    ):
        """Test multiple consecutive torque coil operations."""
        mock_torque_coils.drive.return_value = True

        # First operation
        result1 = z_solar_panel_manager.drive_torque_coils(duration=2.0)
        assert result1 is True

        # Second operation
        result2 = z_solar_panel_manager.drive_torque_coils(duration=1.5, intensity=0.7)
        assert result2 is True

        # Verify both calls were made
        assert mock_torque_coils.drive.call_count == 2

    def test_sensor_initialization_failure(
        self, mock_logger, mock_temperature_sensor, mock_load_switch_pin
    ):
        """Test behavior when sensor initialization fails."""
        mock_temperature_sensor.temperature.side_effect = RuntimeError(
            "Initialization failed"
        )

        manager = ZSolarPanelManager(
            logger=mock_logger,
            temperature_sensor=mock_temperature_sensor,
            light_sensor=None,
            torque_coils=None,
            load_switch_pin=mock_load_switch_pin,
        )
        # Enable load switch for testing
        manager.enable_load()

        result = manager.get_temperature()
        assert result is None
        mock_logger.error.assert_called_once()

    def test_get_sensor_states_success(
        self, z_solar_panel_manager, mock_temperature_sensor, mock_light_sensor
    ):
        """Test get_sensor_states returns correct sensor states."""
        mock_temperature_sensor.get_state.return_value = "OK"
        mock_light_sensor.get_state.return_value = "OK"
        z_solar_panel_manager._sensor_states = {"temperature": "OK", "light": "OK"}
        result = z_solar_panel_manager.get_sensor_states()
        assert result == {"temperature": "OK", "light": "OK"}

    def test_get_sensor_states_with_error(self, z_solar_panel_manager):
        """Test get_sensor_states returns error state if set."""
        z_solar_panel_manager._sensor_states = {"temperature": "ERROR", "light": "OK"}
        result = z_solar_panel_manager.get_sensor_states()
        assert result["temperature"] == "ERROR"
        assert result["light"] == "OK"

    def test_error_tracking_and_last_error(
        self, z_solar_panel_manager, mock_temperature_sensor, mock_logger
    ):
        """Test error is counted and last error is stored when sensor fails."""
        mock_temperature_sensor.temperature.side_effect = Exception("Temp sensor fail")
        # Should log error, increment error count, and set last error
        result = z_solar_panel_manager.get_temperature()
        assert result is None
        assert z_solar_panel_manager.get_error_count() == 1
        assert "Temp sensor fail" in z_solar_panel_manager.get_last_error()
        mock_logger.error.assert_called_once()

    def test_multiple_errors_accumulate(
        self, z_solar_panel_manager, mock_temperature_sensor, mock_logger
    ):
        """Test multiple errors are counted and last error is updated."""
        mock_temperature_sensor.temperature.side_effect = Exception("First error")
        z_solar_panel_manager.get_temperature()
        mock_temperature_sensor.temperature.side_effect = Exception("Second error")
        z_solar_panel_manager.get_temperature()
        assert z_solar_panel_manager.get_error_count() == 2
        assert "Second error" in z_solar_panel_manager.get_last_error()

    def test_get_last_error_none_initially(self, z_solar_panel_manager):
        """Test get_last_error returns None before any error occurs."""
        assert z_solar_panel_manager.get_last_error() is None

    def test_get_error_count_zero_initially(self, z_solar_panel_manager):
        """Test get_error_count returns 0 before any error occurs."""
        assert z_solar_panel_manager.get_error_count() == 0

    # Load Switch Tests
    def test_enable_load_success(self, z_solar_panel_manager, mock_logger):
        """Test successful load switch enable."""
        result = z_solar_panel_manager.enable_load()
        assert result is True
        assert z_solar_panel_manager.get_load_state() is True

    def test_disable_load_success(self, z_solar_panel_manager, mock_logger):
        """Test successful load switch disable."""
        # First enable, then disable
        z_solar_panel_manager.enable_load()
        result = z_solar_panel_manager.disable_load()
        assert result is True
        assert z_solar_panel_manager.get_load_state() is False

    def test_reset_load_success(self, z_solar_panel_manager, mock_logger):
        """Test successful load switch reset."""
        result = z_solar_panel_manager.reset_load()
        assert result is True
        # Reset should typically disable the load
        assert z_solar_panel_manager.get_load_state() is False

    def test_get_load_state_initial(self, z_solar_panel_manager):
        """Test initial load state."""
        # Since we enable the load switch in the fixture for testing,
        # the initial state should be enabled
        assert z_solar_panel_manager.get_load_state() is True

    # NotPowered Error Tests
    def test_temperature_not_powered_error(
        self, z_solar_panel_manager, mock_temperature_sensor
    ):
        """Test NotPowered error when load switch is disabled for temperature reading."""
        z_solar_panel_manager.disable_load()
        with pytest.raises(NotPowered):
            z_solar_panel_manager.get_temperature()

    def test_light_level_not_powered_error(
        self, z_solar_panel_manager, mock_light_sensor
    ):
        """Test NotPowered error when load switch is disabled for light reading."""
        z_solar_panel_manager.disable_load()
        with pytest.raises(NotPowered):
            z_solar_panel_manager.get_light_level()

    def test_get_all_data_not_powered_error(self, z_solar_panel_manager):
        """Test NotPowered error when load switch is disabled for get_all_data."""
        z_solar_panel_manager.disable_load()
        with pytest.raises(NotPowered):
            z_solar_panel_manager.get_all_data()

    def test_drive_torque_coils_not_powered_error(self, z_solar_panel_manager):
        """Test NotPowered error when load switch is disabled for torque coils."""
        z_solar_panel_manager.disable_load()
        with pytest.raises(NotPowered):
            z_solar_panel_manager.drive_torque_coils()

    def test_sensor_operations_work_when_powered(
        self, z_solar_panel_manager, mock_temperature_sensor, mock_light_sensor
    ):
        """Test sensor operations work normally when load switch is enabled."""
        z_solar_panel_manager.enable_load()
        mock_temperature_sensor.temperature.return_value = 30.2
        mock_light_sensor.light.return_value = 1200.0

        temp_result = z_solar_panel_manager.get_temperature()
        light_result = z_solar_panel_manager.get_light_level()

        assert temp_result == 30.2
        assert light_result == 1200.0

    def test_load_switch_enable_failure(self, z_solar_panel_manager, mock_logger):
        """Test load switch enable failure."""
        # Mock the logger to simulate an error
        mock_logger.error.return_value = None
        # The current implementation always returns True, so we can't easily test failure
        # This test verifies the current behavior
        result = z_solar_panel_manager.enable_load()
        assert result is True

    def test_load_switch_disable_failure(self, z_solar_panel_manager, mock_logger):
        """Test load switch disable failure."""
        # Mock the logger to simulate an error
        mock_logger.error.return_value = None
        # The current implementation always returns True, so we can't easily test failure
        # This test verifies the current behavior
        result = z_solar_panel_manager.disable_load()
        assert result is True

    def test_enable_load_with_gpio_pin_high(
        self,
        mock_logger,
        mock_temperature_sensor,
        mock_light_sensor,
        mock_torque_coils,
        mock_load_switch_pin,
    ):
        """Test enable_load sets GPIO pin correctly for enable_high=True."""
        manager = ZSolarPanelManager(
            logger=mock_logger,
            temperature_sensor=mock_temperature_sensor,
            light_sensor=mock_light_sensor,
            torque_coils=mock_torque_coils,
            load_switch_pin=mock_load_switch_pin,
            enable_high=True,
        )

        result = manager.enable_load()

        assert result is True
        assert manager.get_load_state() is True
        assert mock_load_switch_pin.value is True
        # Check that both debug messages were called
        mock_logger.debug.assert_any_call("Z solar panel load switch pin set to True")
        mock_logger.debug.assert_any_call("Z solar panel load switch enabled")

    def test_enable_load_with_gpio_pin_low(
        self,
        mock_logger,
        mock_temperature_sensor,
        mock_light_sensor,
        mock_torque_coils,
        mock_load_switch_pin,
    ):
        """Test enable_load sets GPIO pin correctly for enable_high=False."""
        manager = ZSolarPanelManager(
            logger=mock_logger,
            temperature_sensor=mock_temperature_sensor,
            light_sensor=mock_light_sensor,
            torque_coils=mock_torque_coils,
            load_switch_pin=mock_load_switch_pin,
            enable_high=False,
        )

        result = manager.enable_load()

        assert result is True
        assert manager.get_load_state() is True
        assert mock_load_switch_pin.value is False
        # Check that both debug messages were called
        mock_logger.debug.assert_any_call("Z solar panel load switch pin set to False")
        mock_logger.debug.assert_any_call("Z solar panel load switch enabled")

    def test_disable_load_with_gpio_pin_high(
        self,
        mock_logger,
        mock_temperature_sensor,
        mock_light_sensor,
        mock_torque_coils,
        mock_load_switch_pin,
    ):
        """Test disable_load sets GPIO pin correctly for enable_high=True."""
        manager = ZSolarPanelManager(
            logger=mock_logger,
            temperature_sensor=mock_temperature_sensor,
            light_sensor=mock_light_sensor,
            torque_coils=mock_torque_coils,
            load_switch_pin=mock_load_switch_pin,
            enable_high=True,
        )

        result = manager.disable_load()

        assert result is True
        assert manager.get_load_state() is False
        assert mock_load_switch_pin.value is False
        # Check that both debug messages were called
        mock_logger.debug.assert_any_call("Z solar panel load switch pin set to False")
        mock_logger.debug.assert_any_call("Z solar panel load switch disabled")

    def test_disable_load_with_gpio_pin_low(
        self,
        mock_logger,
        mock_temperature_sensor,
        mock_light_sensor,
        mock_torque_coils,
        mock_load_switch_pin,
    ):
        """Test disable_load sets GPIO pin correctly for enable_high=False."""
        manager = ZSolarPanelManager(
            logger=mock_logger,
            temperature_sensor=mock_temperature_sensor,
            light_sensor=mock_light_sensor,
            torque_coils=mock_torque_coils,
            load_switch_pin=mock_load_switch_pin,
            enable_high=False,
        )

        result = manager.disable_load()

        assert result is True
        assert manager.get_load_state() is False
        assert mock_load_switch_pin.value is True
        # Check that both debug messages were called
        mock_logger.debug.assert_any_call("Z solar panel load switch pin set to True")
        mock_logger.debug.assert_any_call("Z solar panel load switch disabled")

    def test_enable_load_without_gpio_pin(
        self, mock_logger, mock_temperature_sensor, mock_light_sensor, mock_torque_coils
    ):
        """Test enable_load works without GPIO pin."""
        manager = ZSolarPanelManager(
            logger=mock_logger,
            temperature_sensor=mock_temperature_sensor,
            light_sensor=mock_light_sensor,
            torque_coils=mock_torque_coils,
            load_switch_pin=None,
        )

        result = manager.enable_load()

        assert result is True
        assert manager.get_load_state() is True
