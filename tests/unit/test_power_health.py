from unittest.mock import MagicMock

import pytest

from pysquared.config.config import Config
from pysquared.logger import Logger
from pysquared.power_health import CRITICAL, DEGRADED, NOMINAL, UNKNOWN, PowerHealth
from pysquared.protos.power_monitor import PowerMonitorProto


@pytest.fixture
def mock_logger():
    return MagicMock(spec=Logger)


@pytest.fixture
def mock_config():
    config = MagicMock(spec=Config)
    config.normal_charge_current = 100.0
    config.normal_battery_voltage = 7.2
    config.degraded_battery_voltage = 7.0
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
    assert power_health._power_monitor == mock_power_monitor


def test_get_nominal_state(power_health):
    """Test that get() returns NOMINAL when all readings are within normal range"""
    # Mock normal readings
    power_health._power_monitor.get_bus_voltage.return_value = 7.2  # Normal voltage
    power_health._power_monitor.get_current.return_value = 100.0  # Normal current

    result = power_health.get()

    assert isinstance(result, NOMINAL)
    power_health.logger.info.assert_called_with("Power health is NOMINAL")


def test_get_critical_state_low_voltage(power_health):
    """Test that get() returns CRITICAL when battery voltage is at/below critical threshold"""
    # Mock critical voltage reading
    power_health._power_monitor.get_bus_voltage.return_value = (
        5.8  # Below critical (6.0)
    )
    power_health._power_monitor.get_current.return_value = 100.0

    result = power_health.get()

    assert isinstance(result, CRITICAL)
    power_health.logger.warning.assert_called_with(
        "CRITICAL: Battery voltage 5.8V is at or below critical threshold 6.0V"
    )


def test_get_critical_state_exactly_critical_voltage(power_health):
    """Test that get() returns CRITICAL when battery voltage is exactly at critical threshold"""
    # Mock exactly critical voltage reading
    power_health._power_monitor.get_bus_voltage.return_value = 6.0  # Exactly critical
    power_health._power_monitor.get_current.return_value = 100.0

    result = power_health.get()

    assert isinstance(result, CRITICAL)
    power_health.logger.warning.assert_called_with(
        "CRITICAL: Battery voltage 6.0V is at or below critical threshold 6.0V"
    )


def test_get_degraded_state_current_deviation(power_health):
    """Test that get() returns DEGRADED when current is outside normal range"""
    # Mock readings with current deviation
    power_health._power_monitor.get_bus_voltage.return_value = 7.2  # Normal voltage
    power_health._power_monitor.get_current.return_value = (
        250.0  # Way above normal (100.0)
    )

    result = power_health.get()

    assert isinstance(result, DEGRADED)
    power_health.logger.info.assert_called_with(
        "Power health is NOMINAL with minor deviations",
        errors=["Current reading 250.0 is outside of normal range 100.0"],
    )


def test_get_degraded_state_voltage_deviation(power_health):
    """Test that get() returns DEGRADED when voltage is at or below degraded threshold but not critical"""
    power_health._power_monitor.get_bus_voltage.return_value = (
        6.8  # Below degraded threshold (7.0) but above critical (6.0)
    )
    power_health._power_monitor.get_current.return_value = 100.0  # Normal current

    result = power_health.get()

    assert isinstance(result, DEGRADED)
    power_health.logger.info.assert_called_with(
        "Power health is NOMINAL with minor deviations",
        errors=["Bus voltage reading 6.8V is at or below degraded threshold 7.0V"],
    )


def test_get_nominal_with_minor_voltage_deviation(power_health):
    """Test that get() returns NOMINAL when voltage is above degraded threshold"""
    power_health._power_monitor.get_bus_voltage.return_value = (
        7.1  # Above degraded threshold (7.0)
    )
    power_health._power_monitor.get_current.return_value = 100.0  # Normal current

    result = power_health.get()

    assert isinstance(result, NOMINAL)
    power_health.logger.info.assert_called_with("Power health is NOMINAL")


def test_avg_reading_normal_operation(power_health):
    """Test _avg_reading() with normal sensor readings"""
    mock_func = MagicMock(return_value=7.5)

    result = power_health._avg_reading(mock_func, num_readings=10)

    assert result == 7.5
    assert mock_func.call_count == 10


def test_avg_reading_with_none_values(power_health):
    """Test _avg_reading() when sensor returns None"""
    mock_func = MagicMock(return_value=None)
    mock_func.__name__ = "test_sensor_function"

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
    power_health._power_monitor.get_bus_voltage.return_value = None
    power_health._power_monitor.get_current.return_value = 100.0

    # Mock _avg_reading to return None for voltage
    power_health._avg_reading = MagicMock(side_effect=[None, 100.0])

    result = power_health.get()

    assert isinstance(result, UNKNOWN)
    power_health.logger.warning.assert_called_with(
        "Power monitor failed to provide bus voltage reading"
    )


def test_get_with_none_current_reading(power_health):
    """Test get() when current reading returns None"""
    power_health._power_monitor.get_bus_voltage.return_value = 7.2
    power_health._power_monitor.get_current.return_value = None

    # Mock _avg_reading to return None for current
    power_health._avg_reading = MagicMock(side_effect=[7.2, None])

    result = power_health.get()

    assert isinstance(result, UNKNOWN)
    power_health.logger.warning.assert_called_with(
        "Power monitor failed to provide current reading"
    )


def test_get_with_exception_during_voltage_reading(power_health):
    """Test get() when exception occurs during voltage reading"""
    # Mock _avg_reading to raise an exception on first call (voltage)
    test_exception = RuntimeError("Sensor communication error")
    power_health._avg_reading = MagicMock(side_effect=test_exception)

    result = power_health.get()

    assert isinstance(result, UNKNOWN)
    # Check that error was called with the correct message and exception as positional parameter
    power_health.logger.error.assert_called_once_with(
        "Exception occurred while reading from power monitor", test_exception
    )


def test_get_with_exception_during_current_reading(power_health):
    """Test get() when exception occurs during current reading"""
    # Mock _avg_reading to return normal voltage, then raise exception for current
    test_exception = RuntimeError("Current sensor failed")
    power_health._avg_reading = MagicMock(side_effect=[7.2, test_exception])

    result = power_health.get()

    assert isinstance(result, UNKNOWN)
    # Check that error was called with the correct message and exception as positional parameter
    power_health.logger.error.assert_called_once_with(
        "Exception occurred while reading from power monitor", test_exception
    )


def test_get_with_sensor_method_exception(power_health):
    """Test get() when the sensor method itself raises an exception"""
    # Make the sensor method raise an exception directly
    test_exception = OSError("I2C communication failed")
    power_health._power_monitor.get_bus_voltage.side_effect = test_exception

    result = power_health.get()

    assert isinstance(result, UNKNOWN)
    # Check that error was called with the correct message and exception as positional parameter
    power_health.logger.error.assert_called_once_with(
        "Exception occurred while reading from power monitor", test_exception
    )


def test_get_logs_sensor_debug_info(power_health):
    """Test that get() logs debug information about the sensor"""
    power_health._power_monitor.get_bus_voltage.return_value = 7.2
    power_health._power_monitor.get_current.return_value = 100.0

    power_health.get()

    power_health.logger.debug.assert_called_with(
        "Power monitor: ", sensor=power_health._power_monitor
    )


def test_degraded_vs_critical_voltage_boundaries(power_health):
    """Test boundary conditions between degraded and critical voltage thresholds"""
    # Test voltage just above critical but below degraded
    power_health._power_monitor.get_bus_voltage.return_value = (
        6.5  # Above critical (6.0) but below degraded (7.0)
    )
    power_health._power_monitor.get_current.return_value = 100.0

    result = power_health.get()

    assert isinstance(result, DEGRADED)
    power_health.logger.info.assert_called_with(
        "Power health is NOMINAL with minor deviations",
        errors=["Bus voltage reading 6.5V is at or below degraded threshold 7.0V"],
    )


def test_current_deviation_threshold(power_health):
    """Test current deviation uses normal_charge_current as threshold"""
    # normal_charge_current = 100.0, so deviation > 100.0 should trigger error
    power_health._power_monitor.get_bus_voltage.return_value = 7.2
    power_health._power_monitor.get_current.return_value = (
        250.0  # deviation = 150 > 100
    )

    result = power_health.get()

    assert isinstance(result, DEGRADED)
    power_health.logger.info.assert_called_with(
        "Power health is NOMINAL with minor deviations",
        errors=["Current reading 250.0 is outside of normal range 100.0"],
    )


def test_degraded_battery_voltage_threshold(power_health):
    """Test that get() returns DEGRADED when voltage is exactly at degraded threshold"""
    power_health._power_monitor.get_bus_voltage.return_value = (
        7.0  # Exactly at degraded threshold
    )
    power_health._power_monitor.get_current.return_value = 100.0  # Normal current

    result = power_health.get()

    assert isinstance(result, DEGRADED)
    power_health.logger.info.assert_called_with(
        "Power health is NOMINAL with minor deviations",
        errors=["Bus voltage reading 7.0V is at or below degraded threshold 7.0V"],
    )


def test_voltage_just_above_degraded_threshold(power_health):
    """Test that get() returns NOMINAL when voltage is just above degraded threshold"""
    power_health._power_monitor.get_bus_voltage.return_value = (
        7.01  # Just above degraded threshold (7.0)
    )
    power_health._power_monitor.get_current.return_value = 100.0  # Normal current

    result = power_health.get()

    assert isinstance(result, NOMINAL)
    power_health.logger.info.assert_called_with("Power health is NOMINAL")
