from unittest.mock import MagicMock

import microcontroller
import pytest

from pysquared.config.config import Config
from pysquared.logger import Logger
from pysquared.protos.power_monitor import PowerMonitorProto
from pysquared.protos.temperature_sensor import TemperatureSensorProto
from pysquared.state_of_health import DEGRADED, NOMINAL, StateOfHealth


@pytest.fixture
def state_of_health():
    # Mock dependencies
    logger = MagicMock(spec=Logger)
    config = MagicMock(spec=Config)
    config.normal_charge_current = 1.5
    config.normal_battery_voltage = 3.7
    config.normal_temp = 25
    config.normal_micro_temp = 45

    # Add CONFIG_SCHEMA to the mock config
    config.CONFIG_SCHEMA = {
        "normal_charge_current": {"type": float, "min": 0.0, "max": 2000.0},
        "normal_battery_voltage": {"type": float, "min": 6.0, "max": 8.4},
        "normal_temp": {"type": int, "min": 5, "max": 40},
        "normal_micro_temp": {"type": int, "min": 1, "max": 50},
    }

    battery_power_monitor = MagicMock(spec=PowerMonitorProto, autospec=True)
    solar_power_monitor = MagicMock(spec=PowerMonitorProto, autospec=True)
    temperature_sensor = MagicMock(spec=TemperatureSensorProto, autospec=True)
    radio_manager = MagicMock()
    imu_manager = MagicMock()

    # Set up mock return values
    battery_power_monitor.get_bus_voltage.side_effect = [7.0] * 50
    battery_power_monitor.get_shunt_voltage.side_effect = [7.0] * 50
    battery_power_monitor.get_current.side_effect = [1.5] * 50
    solar_power_monitor.get_bus_voltage.side_effect = [7.0] * 50
    solar_power_monitor.get_shunt_voltage.side_effect = [7.0] * 50
    solar_power_monitor.get_current.side_effect = [2.0] * 50
    temperature_sensor.get_temperature.side_effect = [25.0] * 50
    radio_manager.get_temperature.return_value = 25.0
    imu_manager.get_temperature.return_value = 30.0
    microcontroller.cpu = MagicMock()
    microcontroller.cpu.temperature = 45.0

    # Remove .temperature from all mocks except microcontroller.cpu
    if hasattr(battery_power_monitor, "temperature"):
        del battery_power_monitor.temperature
    if hasattr(solar_power_monitor, "temperature"):
        del solar_power_monitor.temperature
    if hasattr(radio_manager, "temperature"):
        del radio_manager.temperature
    if hasattr(imu_manager, "temperature"):
        del imu_manager.temperature

    # Create StateOfHealth instance with sensors as *args
    return StateOfHealth(
        logger,
        config,
        battery_power_monitor,
        solar_power_monitor,
        temperature_sensor,
        radio_manager,
        imu_manager,
        microcontroller.cpu,
    )


def test_nominal_health(state_of_health):
    """Test that StateOfHealth returns NOMINAL when all sensors are within normal ranges"""
    result = state_of_health.get()
    if isinstance(result, DEGRADED):
        print("Logger.warning call args:", state_of_health.logger.warning.call_args)
    assert isinstance(result, NOMINAL)
    state_of_health.logger.info.assert_called_with("State of health is NOMINAL")


def test_degraded_health_high_current(state_of_health):
    """Test that StateOfHealth returns DEGRADED when current is outside normal range"""
    # Set current to be outside normal range for all 50 readings
    state_of_health._sensors[0].get_current.side_effect = [1.5 + 11.0] * 50
    state_of_health._sensors[0].get_bus_voltage.side_effect = [3.7] * 50
    state_of_health._sensors[0].get_shunt_voltage.side_effect = [0.1] * 50
    state_of_health._sensors[1].get_bus_voltage.side_effect = [5.0] * 50
    state_of_health._sensors[1].get_shunt_voltage.side_effect = [0.1] * 50
    state_of_health._sensors[1].get_current.side_effect = [2.0] * 50
    result = state_of_health.get()
    assert isinstance(result, DEGRADED)
    state_of_health.logger.warning.assert_called()


def test_degraded_health_high_voltage(state_of_health):
    """Test that StateOfHealth returns DEGRADED when voltage is outside normal range"""
    # Set bus voltage to be outside normal range for all 50 readings
    state_of_health._sensors[0].get_bus_voltage.side_effect = [3.7 + 11.0] * 50
    state_of_health._sensors[0].get_shunt_voltage.side_effect = [0.1] * 50
    state_of_health._sensors[0].get_current.side_effect = [1.5] * 50
    state_of_health._sensors[1].get_bus_voltage.side_effect = [5.0] * 50
    state_of_health._sensors[1].get_shunt_voltage.side_effect = [0.1] * 50
    state_of_health._sensors[1].get_current.side_effect = [2.0] * 50
    result = state_of_health.get()
    assert isinstance(result, DEGRADED)
    state_of_health.logger.warning.assert_called()


def test_degraded_health_high_temperature(state_of_health):
    """Test that StateOfHealth returns DEGRADED when temperature is outside normal range"""
    # Set temperature to be outside normal range for all 50 readings
    state_of_health._sensors[2].get_temperature.side_effect = [
        41.0
    ] * 50  # Above max of 40
    result = state_of_health.get()
    assert isinstance(result, DEGRADED)
    state_of_health.logger.warning.assert_called()


def test_avg_reading_with_valid_readings(state_of_health):
    """Test that _avg_reading returns correct average for valid readings"""
    # Mock a sensor function that returns consistent values
    mock_func = MagicMock()
    mock_func.return_value = 10.0
    mock_func.__name__ = "test_sensor"

    result = state_of_health._avg_reading(mock_func, num_readings=5)

    assert result == 10.0
    assert mock_func.call_count == 5


def test_avg_reading_with_none_readings(state_of_health):
    """Test that _avg_reading returns None when sensor returns None"""
    # Mock a sensor function that returns None
    mock_func = MagicMock()
    mock_func.return_value = None
    mock_func.__name__ = "test_sensor"

    result = state_of_health._avg_reading(mock_func, num_readings=5)

    assert result is None
    state_of_health.logger.warning.assert_called()


def test_check_power_monitor_within_range(state_of_health):
    """Test that _check_power_monitor returns empty list when all readings are within schema bounds"""
    # Create a mock power monitor with readings within schema bounds
    power_monitor = MagicMock(spec=PowerMonitorProto, autospec=True)
    power_monitor.get_bus_voltage.side_effect = [7.0] * 50  # Within 6.0-8.4 bounds
    power_monitor.get_shunt_voltage.side_effect = [7.0] * 50  # Within 6.0-8.4 bounds
    power_monitor.get_current.side_effect = [1.0] * 50  # Within 0.0-2000.0 bounds

    result = state_of_health._check_power_monitor(power_monitor)

    assert result == []
    assert len(result) == 0


def test_check_power_monitor_out_of_range(state_of_health):
    """Test that _check_power_monitor returns error list when readings are outside schema bounds"""
    # Create a mock power monitor with readings outside schema bounds
    power_monitor = MagicMock(spec=PowerMonitorProto, autospec=True)
    power_monitor.get_bus_voltage.side_effect = [9.0] * 50  # Above 8.4 max
    power_monitor.get_shunt_voltage.side_effect = [5.0] * 50  # Below 6.0 min
    power_monitor.get_current.side_effect = [2500.0] * 50  # Above 2000.0 max

    result = state_of_health._check_power_monitor(power_monitor)

    assert len(result) == 3  # Three errors: bus voltage, shunt voltage, and current
    assert any(
        "Bus voltage reading" in error and "above maximum bound 8.4" in error
        for error in result
    )
    assert any(
        "Shunt voltage reading" in error and "below minimum bound 6.0" in error
        for error in result
    )
    assert any(
        "Current reading" in error and "above maximum bound 2000.0" in error
        for error in result
    )


def test_check_cpu_sensor_within_range(state_of_health):
    """Test that _check_cpu_sensor returns empty list when temperature is within schema bounds"""
    # Create a mock CPU sensor with temperature within schema bounds
    cpu_sensor = MagicMock()
    cpu_sensor.temperature = 25.0  # Within 1-50 bounds

    result = state_of_health._check_cpu_sensor(cpu_sensor)

    assert result == []
    assert len(result) == 0


def test_check_cpu_sensor_out_of_range(state_of_health):
    """Test that _check_cpu_sensor returns error list when temperature is outside schema bounds"""
    # Create a mock CPU sensor with temperature outside schema bounds
    cpu_sensor = MagicMock()
    cpu_sensor.temperature = 55.0  # Above 50 max

    result = state_of_health._check_cpu_sensor(cpu_sensor)

    assert len(result) == 1
    assert "Processor temperature reading" in result[0]
    assert "above maximum bound 50" in result[0]


def test_check_cpu_sensor_below_min(state_of_health):
    """Test that _check_cpu_sensor returns error when temperature is below minimum bound"""
    # Create a mock CPU sensor with temperature below minimum bound
    cpu_sensor = MagicMock()
    cpu_sensor.temperature = 0.0  # Below 1 min

    result = state_of_health._check_cpu_sensor(cpu_sensor)

    assert len(result) == 1
    assert "Processor temperature reading" in result[0]
    assert "below minimum bound 1" in result[0]


def test_check_against_schema_bounds_within_range(state_of_health):
    """Test that _check_against_schema_bounds returns empty list when reading is within bounds"""
    result = state_of_health._check_against_schema_bounds(
        reading=25.0, config_key="normal_temp", reading_name="Test reading"
    )
    assert result == []


def test_check_against_schema_bounds_above_max(state_of_health):
    """Test that _check_against_schema_bounds returns error when reading is above max"""
    result = state_of_health._check_against_schema_bounds(
        reading=45.0, config_key="normal_temp", reading_name="Test reading"
    )
    assert len(result) == 1
    assert "above maximum bound 40" in result[0]


def test_check_against_schema_bounds_below_min(state_of_health):
    """Test that _check_against_schema_bounds returns error when reading is below min"""
    result = state_of_health._check_against_schema_bounds(
        reading=3.0, config_key="normal_temp", reading_name="Test reading"
    )
    assert len(result) == 1
    assert "below minimum bound 5" in result[0]


def test_check_against_schema_bounds_invalid_config_key(state_of_health):
    """Test that _check_against_schema_bounds handles invalid config keys gracefully"""
    result = state_of_health._check_against_schema_bounds(
        reading=25.0, config_key="invalid_key", reading_name="Test reading"
    )
    assert result == []
    state_of_health.logger.warning.assert_called()


def test_check_against_schema_bounds_none_reading(state_of_health):
    """Test that _check_against_schema_bounds handles None readings gracefully"""
    result = state_of_health._check_against_schema_bounds(
        reading=None, config_key="normal_temp", reading_name="Test reading"
    )
    assert result == []
