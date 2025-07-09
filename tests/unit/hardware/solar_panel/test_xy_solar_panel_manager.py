"""
Test XY Solar Panel Manager
===========================

This module provides unit tests for the XYSolarPanelManager class.
"""

from unittest.mock import Mock

import pytest

from pysquared.hardware.solar_panel.xy_panel_manager import XYSolarPanelManager
from pysquared.logger import Logger


class TestXYSolarPanelManager:
    """Test cases for XYSolarPanelManager."""

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
    def xy_solar_panel_manager(
        self, mock_logger, mock_temperature_sensor, mock_light_sensor, mock_torque_coils
    ):
        """Create a XYSolarPanelManager instance for testing."""
        return XYSolarPanelManager(
            logger=mock_logger,
            temperature_sensor=mock_temperature_sensor,
            light_sensor=mock_light_sensor,
            torque_coils=mock_torque_coils,
        )

    def test_initialization(
        self, mock_logger, mock_temperature_sensor, mock_light_sensor, mock_torque_coils
    ):
        """Test XYSolarPanelManager initialization."""
        manager = XYSolarPanelManager(
            logger=mock_logger,
            temperature_sensor=mock_temperature_sensor,
            light_sensor=mock_light_sensor,
            torque_coils=mock_torque_coils,
        )

        assert manager is not None
        assert hasattr(manager, "get_temperature")
        assert hasattr(manager, "get_light_level")
        assert hasattr(manager, "drive_torque_coils")

    def test_get_temperature_success(
        self, xy_solar_panel_manager, mock_temperature_sensor
    ):
        """Test successful temperature reading."""
        expected_temp = 25.5
        mock_temperature_sensor.get_temperature.return_value = expected_temp

        result = xy_solar_panel_manager.get_temperature()

        assert result == expected_temp
        mock_temperature_sensor.get_temperature.assert_called_once()

    def test_get_temperature_failure(
        self, xy_solar_panel_manager, mock_temperature_sensor, mock_logger
    ):
        """Test temperature reading failure."""
        mock_temperature_sensor.get_temperature.side_effect = Exception("Sensor error")

        result = xy_solar_panel_manager.get_temperature()

        assert result is None
        mock_logger.error.assert_called_once()

    def test_get_light_level_success(self, xy_solar_panel_manager, mock_light_sensor):
        """Test successful light level reading."""
        expected_light = 1000.0
        mock_light_sensor.get_light_level.return_value = expected_light

        result = xy_solar_panel_manager.get_light_level()

        assert result == expected_light
        mock_light_sensor.get_light_level.assert_called_once()

    def test_get_light_level_failure(
        self, xy_solar_panel_manager, mock_light_sensor, mock_logger
    ):
        """Test light level reading failure."""
        mock_light_sensor.get_light_level.side_effect = Exception("Sensor error")

        result = xy_solar_panel_manager.get_light_level()

        assert result is None
        mock_logger.error.assert_called_once()

    def test_drive_torque_coils_success(
        self, xy_solar_panel_manager, mock_torque_coils
    ):
        """Test successful torque coil driving."""
        mock_torque_coils.drive.return_value = True

        result = xy_solar_panel_manager.drive_torque_coils()

        assert result is True
        mock_torque_coils.drive.assert_called_once()

    def test_drive_torque_coils_failure(
        self, xy_solar_panel_manager, mock_torque_coils, mock_logger
    ):
        """Test torque coil driving failure."""
        mock_torque_coils.drive.side_effect = Exception("Coil error")

        result = xy_solar_panel_manager.drive_torque_coils()

        assert result is False
        mock_logger.error.assert_called_once()

    def test_drive_torque_coils_with_parameters(
        self, xy_solar_panel_manager, mock_torque_coils
    ):
        """Test torque coil driving with parameters."""
        mock_torque_coils.drive.return_value = True
        test_params = {"duration": 5.0, "intensity": 0.8}

        result = xy_solar_panel_manager.drive_torque_coils(**test_params)

        assert result is True
        mock_torque_coils.drive.assert_called_once_with(**test_params)

    def test_drive_torque_coils_not_implemented(
        self, mock_logger, mock_temperature_sensor, mock_light_sensor
    ):
        """Test torque coil driving when not implemented."""
        # Create manager without torque coils
        manager = XYSolarPanelManager(
            logger=mock_logger,
            temperature_sensor=mock_temperature_sensor,
            light_sensor=mock_light_sensor,
            torque_coils=None,
        )

        with pytest.raises(NotImplementedError):
            manager.drive_torque_coils()

    def test_temperature_sensor_none(
        self, mock_logger, mock_light_sensor, mock_torque_coils
    ):
        """Test behavior when temperature sensor is None."""
        manager = XYSolarPanelManager(
            logger=mock_logger,
            temperature_sensor=None,
            light_sensor=mock_light_sensor,
            torque_coils=mock_torque_coils,
        )

        result = manager.get_temperature()
        assert result is None

    def test_light_sensor_none(
        self, mock_logger, mock_temperature_sensor, mock_torque_coils
    ):
        """Test behavior when light sensor is None."""
        manager = XYSolarPanelManager(
            logger=mock_logger,
            temperature_sensor=mock_temperature_sensor,
            light_sensor=None,
            torque_coils=mock_torque_coils,
        )

        result = manager.get_light_level()
        assert result is None

    def test_temperature_range_validation(
        self, xy_solar_panel_manager, mock_temperature_sensor
    ):
        """Test temperature reading within expected range."""
        # Test normal temperature range
        mock_temperature_sensor.get_temperature.return_value = 20.0
        result = xy_solar_panel_manager.get_temperature()
        assert -50.0 <= result <= 100.0

        # Test extreme temperatures
        mock_temperature_sensor.get_temperature.return_value = -60.0
        result = xy_solar_panel_manager.get_temperature()
        assert result == -60.0  # Should still return the value even if extreme

    def test_light_level_range_validation(
        self, xy_solar_panel_manager, mock_light_sensor
    ):
        """Test light level reading within expected range."""
        # Test normal light level range
        mock_light_sensor.get_light_level.return_value = 500.0
        result = xy_solar_panel_manager.get_light_level()
        assert 0.0 <= result <= 2000.0

        # Test extreme light levels
        mock_light_sensor.get_light_level.return_value = 2500.0
        result = xy_solar_panel_manager.get_light_level()
        assert result == 2500.0  # Should still return the value even if extreme

    def test_concurrent_sensor_access(
        self, xy_solar_panel_manager, mock_temperature_sensor, mock_light_sensor
    ):
        """Test concurrent access to temperature and light sensors."""
        mock_temperature_sensor.get_temperature.return_value = 25.0
        mock_light_sensor.get_light_level.return_value = 750.0

        temp_result = xy_solar_panel_manager.get_temperature()
        light_result = xy_solar_panel_manager.get_light_level()

        assert temp_result == 25.0
        assert light_result == 750.0
        mock_temperature_sensor.get_temperature.assert_called_once()
        mock_light_sensor.get_light_level.assert_called_once()

    def test_error_logging_format(
        self, xy_solar_panel_manager, mock_temperature_sensor, mock_logger
    ):
        """Test that errors are logged with proper format."""
        error_msg = "Sensor communication failed"
        mock_temperature_sensor.get_temperature.side_effect = Exception(error_msg)

        xy_solar_panel_manager.get_temperature()

        # Verify error was logged with proper exception handling
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert (
            "temperature" in call_args[0][0].lower()
        )  # Error message should mention temperature
        assert call_args[1]["err"] is not None  # Should have err parameter
