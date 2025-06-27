from unittest.mock import MagicMock

import pytest

from pysquared.config.config import Config
from pysquared.logger import Logger
from pysquared.protos.power_monitor import PowerMonitorProto
from pysquared.state_of_health import CRITICAL, DEGRADED, NOMINAL, PowerHealth


@pytest.fixture
def mock_logger():
    return MagicMock(spec=Logger)


@pytest.fixture
def mock_config():
    config = MagicMock(spec=Config)
    config.normal_charge_current = 100.0
    config.normal_battery_voltage = 7.2
    config.critical_battery_voltage = 6.0
    return config


@pytest.fixture
def mock_power_monitor():
    return MagicMock(spec=PowerMonitorProto)


@pytest.fixture
def power_health(mock_logger, mock_config, mock_power_monitor):
    return PowerHealth(
        logger=mock_logger,
        config=mock_config,
        power_monitor=mock_power_monitor,
    )


def test_power_health_initialization(
    power_health, mock_logger, mock_config, mock_power_monitor
):
    """Test that PowerHealth initializes correctly"""
    assert power_health.logger == mock_logger
    assert power_health.config == mock_config
    assert power_health._sensor == mock_power_monitor


def test_get_nominal_state(power_health):
    """Test that get() returns NOMINAL when all readings are within normal range"""
    # Mock normal readings
    power_health._sensor.get_bus_voltage.return_value = 7.2  # Normal voltage
    power_health._sensor.get_current.return_value = 100.0  # Normal current

    result = power_health.get()

    assert isinstance(result, NOMINAL)
    power_health.logger.info.assert_called_with("Power health is NOMINAL")


def test_get_critical_state_low_voltage(power_health):
    """Test that get() returns CRITICAL when battery voltage is at/below critical threshold"""
    # Mock critical voltage reading
    power_health._sensor.get_bus_voltage.return_value = 5.8  # Below critical (6.0)
    power_health._sensor.get_current.return_value = 100.0

    result = power_health.get()

    assert isinstance(result, CRITICAL)
    power_health.logger.warning.assert_called_with(
        "CRITICAL: Battery voltage 5.8V is at or below critical threshold 6.0V"
    )


def test_get_critical_state_exactly_critical_voltage(power_health):
    """Test that get() returns CRITICAL when battery voltage is exactly at critical threshold"""
    # Mock exactly critical voltage reading
    power_health._sensor.get_bus_voltage.return_value = 6.0  # Exactly critical
    power_health._sensor.get_current.return_value = 100.0

    result = power_health.get()

    assert isinstance(result, CRITICAL)


def test_get_degraded_state_current_deviation(power_health):
    """Test that get() returns DEGRADED when current is outside normal range"""
    # Mock readings with current deviation
    power_health._sensor.get_bus_voltage.return_value = 7.2  # Normal voltage
    power_health._sensor.get_current.return_value = 250.0  # Way above normal (100.0)

    result = power_health.get()

    assert isinstance(result, DEGRADED)
    power_health.logger.info.assert_called()


def test_get_degraded_state_voltage_deviation(power_health):
    """Test that get() returns DEGRADED when voltage is outside normal range but not critical"""
    # Voltage tolerance = abs(7.2 - 6.0) / 2 = 0.6
    power_health._sensor.get_bus_voltage.return_value = (
        6.5  # Outside tolerance but not critical
    )
    power_health._sensor.get_current.return_value = 100.0  # Normal current

    result = power_health.get()

    assert isinstance(result, DEGRADED)


def test_get_nominal_with_minor_voltage_deviation(power_health):
    """Test that get() returns NOMINAL when voltage deviation is within tolerance"""
    # Voltage tolerance = abs(7.2 - 6.0) / 2 = 0.6
    power_health._sensor.get_bus_voltage.return_value = (
        6.8  # Within tolerance (7.2 ± 0.6)
    )
    power_health._sensor.get_current.return_value = 100.0  # Normal current

    result = power_health.get()

    assert isinstance(result, NOMINAL)


def test_avg_reading_normal_operation(power_health):
    """Test _avg_reading() with normal sensor readings"""
    mock_func = MagicMock(return_value=7.5)

    result = power_health._avg_reading(mock_func, num_readings=10)

    assert result == 7.5
    assert mock_func.call_count == 10


def test_avg_reading_with_none_values(power_health):
    """Test _avg_reading() when sensor returns None"""
    mock_func = MagicMock(return_value=None)

    result = power_health._avg_reading(mock_func, num_readings=5)

    assert result is None
    assert mock_func.call_count == 1
    power_health.logger.warning.assert_called()


def test_avg_reading_with_varying_values(power_health):
    """Test _avg_reading() with varying sensor readings"""
    mock_func = MagicMock(side_effect=[7.0, 7.2, 7.4, 7.6, 7.8])

    result = power_health._avg_reading(mock_func, num_readings=5)

    expected_avg = (7.0 + 7.2 + 7.4 + 7.6 + 7.8) / 5
    assert result == pytest.approx(expected_avg, rel=1e-6)
    assert mock_func.call_count == 5


def test_avg_reading_default_num_readings(power_health):
    """Test _avg_reading() uses default of 50 readings"""
    mock_func = MagicMock(return_value=7.0)

    result = power_health._avg_reading(mock_func)

    assert result == 7.0
    assert mock_func.call_count == 50


def test_get_with_none_voltage_reading(power_health):
    """Test get() when voltage reading returns None"""
    power_health._sensor.get_bus_voltage.return_value = None
    power_health._sensor.get_current.return_value = 100.0

    # Mock _avg_reading to return None for voltage
    power_health._avg_reading = MagicMock(side_effect=[None, 100.0])

    result = power_health.get()

    assert isinstance(result, NOMINAL)


def test_get_with_none_current_reading(power_health):
    """Test get() when current reading returns None"""
    power_health._sensor.get_bus_voltage.return_value = 7.2
    power_health._sensor.get_current.return_value = None

    # Mock _avg_reading to return None for current
    power_health._avg_reading = MagicMock(side_effect=[7.2, None])

    result = power_health.get()

    assert isinstance(result, NOMINAL)


def test_get_logs_sensor_debug_info(power_health):
    """Test that get() logs debug information about the sensor"""
    power_health._sensor.get_bus_voltage.return_value = 7.2
    power_health._sensor.get_current.return_value = 100.0

    power_health.get()

    power_health.logger.debug.assert_called_with(
        "Power monitor: ", sensor=power_health._sensor
    )


def test_voltage_tolerance_calculation(power_health):
    """Test that voltage tolerance is calculated correctly based on config"""
    # normal_battery_voltage = 7.2, critical_battery_voltage = 6.0
    # Expected tolerance = abs(7.2 - 6.0) / 2 = 0.6

    power_health._sensor.get_bus_voltage.return_value = (
        6.55  # Just outside tolerance (7.2 - 0.6 = 6.6)
    )
    power_health._sensor.get_current.return_value = 100.0

    result = power_health.get()

    assert isinstance(result, DEGRADED)


def test_current_deviation_threshold(power_health):
    """Test current deviation uses normal_charge_current as threshold"""
    # normal_charge_current = 100.0, so deviation > 100.0 should trigger error
    power_health._sensor.get_bus_voltage.return_value = 7.2
    power_health._sensor.get_current.return_value = 250.0  # deviation = 150 > 100

    result = power_health.get()

    assert isinstance(result, DEGRADED)
