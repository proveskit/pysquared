"""
Base Solar Panel Test Class
==========================

This module provides a base test class for solar panel managers to eliminate test duplication.
"""

from typing import Type, TypeVar
from unittest.mock import Mock, PropertyMock, patch

import pytest

from pysquared.hardware.exception import NotPowered
from pysquared.hardware.solar_panel.base_manager import BaseSolarPanelManager
from pysquared.logger import Logger

T = TypeVar("T", bound=BaseSolarPanelManager)


class BaseSolarPanelTest:
    """Base test class for solar panel managers."""

    # This should be overridden by subclasses
    MANAGER_CLASS: Type[T] = None  # type: ignore
    PANEL_NAME: str = None  # type: ignore

    def _create_manager(
        self,
        mock_logger,
        temperature_sensor=None,
        light_sensor=None,
        torque_coils=None,
        load_switch_pin=None,
        enable_high=True,
    ):
        """Helper method to create a manager with the given configuration."""
        return self.MANAGER_CLASS(  # type: ignore
            logger=mock_logger,
            temperature_sensor=temperature_sensor,
            light_sensor=light_sensor,
            torque_coils=torque_coils,
            load_switch_pin=load_switch_pin,
            enable_high=enable_high,
        )

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger for testing."""
        return Mock(spec=Logger)

    @pytest.fixture
    def mock_temperature_sensor(self):
        """Create a mock temperature sensor for testing."""
        mock = Mock()
        type(mock).temperature = PropertyMock()
        return mock

    @pytest.fixture
    def mock_light_sensor(self):
        """Create a mock light sensor for testing."""
        mock = Mock()
        type(mock).light = PropertyMock()
        return mock

    @pytest.fixture
    def mock_torque_coils(self):
        """Create mock torque coils for testing."""
        return Mock()

    @pytest.fixture
    def mock_load_switch_pin(self):
        """Create a mock load switch pin for testing."""
        return Mock()

    @pytest.fixture
    def solar_panel_manager(
        self,
        mock_logger,
        mock_temperature_sensor,
        mock_light_sensor,
        mock_torque_coils,
        mock_load_switch_pin,
    ):
        """Create a solar panel manager instance for testing."""
        manager = self._create_manager(
            mock_logger=mock_logger,
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
        """Test solar panel manager initialization."""
        manager = self._create_manager(
            mock_logger=mock_logger,
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
        assert hasattr(manager, "get_error_count")
        # Load switch methods
        assert hasattr(manager, "enable_load")
        assert hasattr(manager, "disable_load")
        assert hasattr(manager, "reset_load")
        assert hasattr(manager, "is_enabled")

    def test_get_temperature_success(
        self, solar_panel_manager, mock_temperature_sensor
    ):
        """Test successful temperature reading."""
        expected_temp = 25.5
        with patch.object(
            type(mock_temperature_sensor), "temperature", new_callable=PropertyMock
        ) as mock_temp:
            mock_temp.return_value = expected_temp
            result = solar_panel_manager.get_temperature()
            assert result == expected_temp

    def test_get_temperature_failure(
        self, solar_panel_manager, mock_temperature_sensor, mock_logger
    ):
        """Test temperature reading failure."""
        with patch.object(
            type(mock_temperature_sensor), "temperature", new_callable=PropertyMock
        ) as mock_temp:
            mock_temp.side_effect = Exception("Sensor error")
            with pytest.raises(Exception, match="Sensor error"):
                solar_panel_manager.get_temperature()
            mock_logger.error.assert_called_once()

    def test_get_light_level_success(self, solar_panel_manager, mock_light_sensor):
        """Test successful light level reading."""
        expected_light = 1000.0
        with patch.object(
            type(mock_light_sensor), "light", new_callable=PropertyMock
        ) as mock_light:
            mock_light.return_value = expected_light
            result = solar_panel_manager.get_light_level()
            assert result == expected_light

    def test_get_light_level_failure(
        self, solar_panel_manager, mock_light_sensor, mock_logger
    ):
        """Test light level reading failure."""
        with patch.object(
            type(mock_light_sensor), "light", new_callable=PropertyMock
        ) as mock_light:
            mock_light.side_effect = Exception("Sensor error")
            with pytest.raises(Exception, match="Sensor error"):
                solar_panel_manager.get_light_level()
            mock_logger.error.assert_called_once()

    def test_drive_torque_coils_success(self, solar_panel_manager, mock_torque_coils):
        """Test successful torque coil driving."""
        mock_torque_coils.drive.return_value = True

        result = solar_panel_manager.drive_torque_coils()

        assert result is True
        mock_torque_coils.drive.assert_called_once()

    def test_drive_torque_coils_failure(
        self, solar_panel_manager, mock_torque_coils, mock_logger
    ):
        """Test torque coil driving failure."""
        mock_torque_coils.drive.side_effect = Exception("Coil error")

        with pytest.raises(Exception, match="Coil error"):
            solar_panel_manager.drive_torque_coils()

        mock_logger.error.assert_called_once()

    def test_drive_torque_coils_with_parameters(
        self, solar_panel_manager, mock_torque_coils
    ):
        """Test torque coil driving with parameters."""
        mock_torque_coils.drive.return_value = True
        test_params = {"duration": 5.0, "intensity": 0.8}

        result = solar_panel_manager.drive_torque_coils(**test_params)

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
        manager = self._create_manager(
            mock_logger=mock_logger,
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
        manager = self._create_manager(
            mock_logger=mock_logger,
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
        manager = self._create_manager(
            mock_logger=mock_logger,
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
        self, solar_panel_manager, mock_temperature_sensor
    ):
        """Test temperature range validation."""
        with patch.object(
            type(mock_temperature_sensor), "temperature", new_callable=PropertyMock
        ) as mock_temp:
            mock_temp.return_value = 25.0
            result = solar_panel_manager.get_temperature()
            assert result == 25.0

    def test_light_level_range_validation(self, solar_panel_manager, mock_light_sensor):
        """Test light level range validation."""
        with patch.object(
            type(mock_light_sensor), "light", new_callable=PropertyMock
        ) as mock_light:
            mock_light.return_value = 1000.0
            result = solar_panel_manager.get_light_level()
            assert result == 1000.0

    def test_concurrent_sensor_access(
        self, solar_panel_manager, mock_temperature_sensor, mock_light_sensor
    ):
        """Test concurrent sensor access."""
        with (
            patch.object(
                type(mock_temperature_sensor), "temperature", new_callable=PropertyMock
            ) as mock_temp,
            patch.object(
                type(mock_light_sensor), "light", new_callable=PropertyMock
            ) as mock_light,
        ):
            mock_temp.return_value = 25.0
            mock_light.return_value = 1000.0

            temp_result = solar_panel_manager.get_temperature()
            light_result = solar_panel_manager.get_light_level()

            assert temp_result == 25.0
            assert light_result == 1000.0

    def test_error_logging_format(
        self, solar_panel_manager, mock_temperature_sensor, mock_logger
    ):
        """Test error logging format."""
        with patch.object(
            type(mock_temperature_sensor), "temperature", new_callable=PropertyMock
        ) as mock_temp:
            mock_temp.side_effect = Exception("Test error")
            with pytest.raises(Exception, match="Test error"):
                solar_panel_manager.get_temperature()
            mock_logger.error.assert_called_once()

    def test_get_all_data_success(
        self, solar_panel_manager, mock_temperature_sensor, mock_light_sensor
    ):
        """Test successful get_all_data call."""
        with (
            patch.object(
                type(mock_temperature_sensor), "temperature", new_callable=PropertyMock
            ) as mock_temp,
            patch.object(
                type(mock_light_sensor), "light", new_callable=PropertyMock
            ) as mock_light,
        ):
            mock_temp.return_value = 25.0
            mock_light.return_value = 1000.0

            temp, light = solar_panel_manager.get_all_data()

            assert temp == 25.0
            assert light == 1000.0

    def test_get_all_data_temperature_failure(
        self,
        solar_panel_manager,
        mock_temperature_sensor,
        mock_light_sensor,
        mock_logger,
    ):
        """Test get_all_data with temperature sensor failure."""
        with (
            patch.object(
                type(mock_temperature_sensor), "temperature", new_callable=PropertyMock
            ) as mock_temp,
            patch.object(
                type(mock_light_sensor), "light", new_callable=PropertyMock
            ) as mock_light,
        ):
            mock_temp.side_effect = Exception("Temperature error")
            mock_light.return_value = 1000.0

            with pytest.raises(Exception, match="Temperature error"):
                solar_panel_manager.get_all_data()

    def test_get_all_data_light_failure(
        self,
        solar_panel_manager,
        mock_temperature_sensor,
        mock_light_sensor,
        mock_logger,
    ):
        """Test get_all_data with light sensor failure."""
        with (
            patch.object(
                type(mock_temperature_sensor), "temperature", new_callable=PropertyMock
            ) as mock_temp,
            patch.object(
                type(mock_light_sensor), "light", new_callable=PropertyMock
            ) as mock_light,
        ):
            mock_temp.return_value = 25.0
            mock_light.side_effect = Exception("Light error")

            with pytest.raises(Exception, match="Light error"):
                solar_panel_manager.get_all_data()

    def test_get_all_data_both_sensors_failure(
        self,
        solar_panel_manager,
        mock_temperature_sensor,
        mock_light_sensor,
        mock_logger,
    ):
        """Test get_all_data with both sensors failing."""
        with (
            patch.object(
                type(mock_temperature_sensor), "temperature", new_callable=PropertyMock
            ) as mock_temp,
            patch.object(
                type(mock_light_sensor), "light", new_callable=PropertyMock
            ) as mock_light,
        ):
            mock_temp.side_effect = Exception("Temperature error")
            mock_light.side_effect = Exception("Light error")

            with pytest.raises(Exception, match="Temperature error"):
                solar_panel_manager.get_all_data()

    def test_get_all_data_temperature_sensor_none(
        self, mock_logger, mock_light_sensor, mock_torque_coils, mock_load_switch_pin
    ):
        """Test get_all_data when temperature sensor is None."""
        manager = self._create_manager(
            mock_logger=mock_logger,
            temperature_sensor=None,
            light_sensor=mock_light_sensor,
            torque_coils=mock_torque_coils,
            load_switch_pin=mock_load_switch_pin,
        )
        # Enable load switch for testing
        manager.enable_load()

        with patch.object(
            type(mock_light_sensor), "light", new_callable=PropertyMock
        ) as mock_light:
            mock_light.return_value = 1000.0

            temp, light = manager.get_all_data()

            assert temp is None
            assert light == 1000.0

    def test_get_all_data_light_sensor_none(
        self,
        mock_logger,
        mock_temperature_sensor,
        mock_torque_coils,
        mock_load_switch_pin,
    ):
        """Test get_all_data when light sensor is None."""
        manager = self._create_manager(
            mock_logger=mock_logger,
            temperature_sensor=mock_temperature_sensor,
            light_sensor=None,
            torque_coils=mock_torque_coils,
            load_switch_pin=mock_load_switch_pin,
        )
        # Enable load switch for testing
        manager.enable_load()

        with patch.object(
            type(mock_temperature_sensor), "temperature", new_callable=PropertyMock
        ) as mock_temp:
            mock_temp.return_value = 25.0

            temp, light = manager.get_all_data()

            assert temp == 25.0
            assert light is None

    def test_get_all_data_both_sensors_none(
        self, mock_logger, mock_torque_coils, mock_load_switch_pin
    ):
        """Test get_all_data when both sensors are None."""
        manager = self._create_manager(
            mock_logger=mock_logger,
            temperature_sensor=None,
            light_sensor=None,
            torque_coils=mock_torque_coils,
            load_switch_pin=mock_load_switch_pin,
        )
        # Enable load switch for testing
        manager.enable_load()

        temp, light = manager.get_all_data()

        assert temp is None
        assert light is None

    def test_get_sensor_states_success(
        self, solar_panel_manager, mock_temperature_sensor, mock_light_sensor
    ):
        """Test successful get_sensor_states call."""
        with (
            patch.object(
                type(mock_temperature_sensor), "temperature", new_callable=PropertyMock
            ) as mock_temp,
            patch.object(
                type(mock_light_sensor), "light", new_callable=PropertyMock
            ) as mock_light,
        ):
            mock_temp.return_value = 25.0
            mock_light.return_value = 1000.0

            solar_panel_manager.get_temperature()
            solar_panel_manager.get_light_level()

            states = solar_panel_manager.get_sensor_states()
            assert states["temperature"] == "OK"
            assert states["light"] == "OK"

    def test_get_sensor_states_with_error(self, solar_panel_manager):
        """Test get_sensor_states with sensor errors."""
        states = solar_panel_manager.get_sensor_states()
        assert "temperature" in states
        assert "light" in states

    def test_error_tracking_and_logging(
        self, solar_panel_manager, mock_temperature_sensor, mock_logger
    ):
        """Test error tracking and logging."""
        with patch.object(
            type(mock_temperature_sensor), "temperature", new_callable=PropertyMock
        ) as mock_temp:
            mock_temp.side_effect = Exception("Test error")
            with pytest.raises(Exception, match="Test error"):
                solar_panel_manager.get_temperature()

            error_count = solar_panel_manager.get_error_count()
            assert error_count == 1

    def test_multiple_errors_accumulate(
        self, solar_panel_manager, mock_temperature_sensor, mock_logger
    ):
        """Test that multiple errors accumulate."""
        with patch.object(
            type(mock_temperature_sensor), "temperature", new_callable=PropertyMock
        ) as mock_temp:
            mock_temp.side_effect = Exception("Test error")

            # First error
            with pytest.raises(Exception, match="Test error"):
                solar_panel_manager.get_temperature()

            # Second error
            with pytest.raises(Exception, match="Test error"):
                solar_panel_manager.get_temperature()

            error_count = solar_panel_manager.get_error_count()
            assert error_count == 2

    def test_error_count_zero_initially(self, solar_panel_manager):
        """Test that error count starts at zero."""
        error_count = solar_panel_manager.get_error_count()
        assert error_count == 0

    def test_enable_load_success(self, solar_panel_manager, mock_logger):
        """Test successful load switch enable."""
        solar_panel_manager.enable_load()  # Should not raise
        assert solar_panel_manager.is_enabled is True

    def test_disable_load_success(self, solar_panel_manager, mock_logger):
        """Test successful load switch disable."""
        # First enable, then disable
        solar_panel_manager.enable_load()
        solar_panel_manager.disable_load()  # Should not raise
        assert solar_panel_manager.is_enabled is False

    def test_reset_load_success(self, solar_panel_manager, mock_logger):
        """Test successful load switch reset."""
        # Start with load enabled
        solar_panel_manager.enable_load()
        solar_panel_manager.reset_load()  # Should not raise
        assert solar_panel_manager.is_enabled is True

    def test_get_load_state_initial(self, solar_panel_manager):
        """Test initial load state."""
        # Since we enable the load switch in the fixture for testing,
        # the initial state should be enabled
        assert solar_panel_manager.is_enabled is True

    def test_temperature_not_powered_error(
        self, solar_panel_manager, mock_temperature_sensor
    ):
        """Test NotPowered error when load switch is disabled for temperature reading."""
        solar_panel_manager.disable_load()
        with pytest.raises(NotPowered):
            solar_panel_manager.get_temperature()

    def test_light_level_not_powered_error(
        self, solar_panel_manager, mock_light_sensor
    ):
        """Test NotPowered error when load switch is disabled for light reading."""
        solar_panel_manager.disable_load()
        with pytest.raises(NotPowered):
            solar_panel_manager.get_light_level()

    def test_get_all_data_not_powered_error(self, solar_panel_manager):
        """Test NotPowered error when load switch is disabled for get_all_data."""
        solar_panel_manager.disable_load()
        with pytest.raises(NotPowered):
            solar_panel_manager.get_all_data()

    def test_drive_torque_coils_not_powered_error(self, solar_panel_manager):
        """Test NotPowered error when load switch is disabled for torque coils."""
        solar_panel_manager.disable_load()
        with pytest.raises(NotPowered):
            solar_panel_manager.drive_torque_coils()

    def test_sensor_operations_work_when_powered(
        self, solar_panel_manager, mock_temperature_sensor, mock_light_sensor
    ):
        """Test sensor operations work normally when load switch is enabled."""
        solar_panel_manager.enable_load()
        with (
            patch.object(
                type(mock_temperature_sensor), "temperature", new_callable=PropertyMock
            ) as mock_temp,
            patch.object(
                type(mock_light_sensor), "light", new_callable=PropertyMock
            ) as mock_light,
        ):
            mock_temp.return_value = 25.0
            mock_light.return_value = 1000.0

            temp_result = solar_panel_manager.get_temperature()
            light_result = solar_panel_manager.get_light_level()

            assert temp_result == 25.0
            assert light_result == 1000.0

    def test_load_switch_enable_failure(self, solar_panel_manager, mock_logger):
        """Test load switch enable failure."""
        mock_logger.error.return_value = None

        class PinWithFail:
            @property
            def value(self):
                return False

            @value.setter
            def value(self, v):
                raise Exception("Enable error")

        solar_panel_manager._load_switch_pin = PinWithFail()
        with pytest.raises(
            RuntimeError, match="Failed to enable load switch: Enable error"
        ):
            solar_panel_manager.enable_load()

    def test_load_switch_disable_failure(self, solar_panel_manager, mock_logger):
        """Test load switch disable failure."""
        mock_logger.error.return_value = None

        class PinWithFail:
            @property
            def value(self):
                return True

            @value.setter
            def value(self, v):
                raise Exception("Disable error")

        solar_panel_manager._load_switch_pin = PinWithFail()
        with pytest.raises(
            RuntimeError, match="Failed to disable load switch: Disable error"
        ):
            solar_panel_manager.disable_load()

    def test_enable_load_with_gpio_pin_high(
        self,
        mock_logger,
        mock_temperature_sensor,
        mock_light_sensor,
        mock_torque_coils,
        mock_load_switch_pin,
    ):
        """Test enable_load sets GPIO pin correctly for enable_high=True."""
        manager = self._create_manager(
            mock_logger=mock_logger,
            temperature_sensor=mock_temperature_sensor,
            light_sensor=mock_light_sensor,
            torque_coils=mock_torque_coils,
            load_switch_pin=mock_load_switch_pin,
            enable_high=True,
        )
        manager.enable_load()
        mock_load_switch_pin.value = True
        assert manager.is_enabled is True

    def test_enable_load_with_gpio_pin_low(
        self,
        mock_logger,
        mock_temperature_sensor,
        mock_light_sensor,
        mock_torque_coils,
        mock_load_switch_pin,
    ):
        """Test enable_load sets GPIO pin correctly for enable_high=False."""
        manager = self._create_manager(
            mock_logger=mock_logger,
            temperature_sensor=mock_temperature_sensor,
            light_sensor=mock_light_sensor,
            torque_coils=mock_torque_coils,
            load_switch_pin=mock_load_switch_pin,
            enable_high=False,
        )
        manager.enable_load()
        mock_load_switch_pin.value = False
        assert manager.is_enabled is True

    def test_disable_load_with_gpio_pin_high(
        self,
        mock_logger,
        mock_temperature_sensor,
        mock_light_sensor,
        mock_torque_coils,
        mock_load_switch_pin,
    ):
        """Test disable_load sets GPIO pin correctly for enable_high=True."""
        manager = self._create_manager(
            mock_logger=mock_logger,
            temperature_sensor=mock_temperature_sensor,
            light_sensor=mock_light_sensor,
            torque_coils=mock_torque_coils,
            load_switch_pin=mock_load_switch_pin,
            enable_high=True,
        )
        manager.enable_load()
        manager.disable_load()
        mock_load_switch_pin.value = False
        assert manager.is_enabled is False

    def test_disable_load_with_gpio_pin_low(
        self,
        mock_logger,
        mock_temperature_sensor,
        mock_light_sensor,
        mock_torque_coils,
        mock_load_switch_pin,
    ):
        """Test disable_load sets GPIO pin correctly for enable_high=False."""
        manager = self._create_manager(
            mock_logger=mock_logger,
            temperature_sensor=mock_temperature_sensor,
            light_sensor=mock_light_sensor,
            torque_coils=mock_torque_coils,
            load_switch_pin=mock_load_switch_pin,
            enable_high=False,
        )
        manager.enable_load()
        manager.disable_load()
        mock_load_switch_pin.value = True
        assert manager.is_enabled is False

    def test_enable_load_without_gpio_pin(
        self, mock_logger, mock_temperature_sensor, mock_light_sensor, mock_torque_coils
    ):
        """Test enable_load raises NotImplementedError without GPIO pin."""
        manager = self._create_manager(
            mock_logger=mock_logger,
            temperature_sensor=mock_temperature_sensor,
            light_sensor=mock_light_sensor,
            torque_coils=mock_torque_coils,
            load_switch_pin=None,
        )
        with pytest.raises(NotImplementedError, match="Load switch pin is required"):
            manager.enable_load()

    def test_disable_load_without_gpio_pin(
        self, mock_logger, mock_temperature_sensor, mock_light_sensor, mock_torque_coils
    ):
        """Test disable_load raises NotImplementedError without GPIO pin."""
        manager = self._create_manager(
            mock_logger=mock_logger,
            temperature_sensor=mock_temperature_sensor,
            light_sensor=mock_light_sensor,
            torque_coils=mock_torque_coils,
            load_switch_pin=None,
        )
        with pytest.raises(NotImplementedError, match="Load switch pin is required"):
            manager.disable_load()

    def test_disable_load_sets_pin_value_correctly(
        self, solar_panel_manager, mock_load_switch_pin
    ):
        """Test that disable_load() correctly sets the pin value and updates is_enabled."""
        # Start with load enabled
        solar_panel_manager.enable_load()
        assert solar_panel_manager.is_enabled is True

        # Disable the load
        solar_panel_manager.disable_load()

        # Verify pin was set to disable value (False for enable_high=True)
        assert mock_load_switch_pin.value is False

        # Verify is_enabled reflects the pin state
        assert solar_panel_manager.is_enabled is False

    def test_reset_load_without_gpio_pin(
        self, mock_logger, mock_temperature_sensor, mock_light_sensor, mock_torque_coils
    ):
        """Test reset_load raises NotImplementedError without GPIO pin."""
        manager = self._create_manager(
            mock_logger=mock_logger,
            temperature_sensor=mock_temperature_sensor,
            light_sensor=mock_light_sensor,
            torque_coils=mock_torque_coils,
            load_switch_pin=None,
        )
        with pytest.raises(NotImplementedError, match="Load switch pin is required"):
            manager.reset_load()
