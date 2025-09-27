"""Unit tests for the PowerHealth class.

This module contains unit tests for the `PowerHealth` class, which assesses the
health of the power system based on voltage and current readings. The tests cover
various scenarios, including nominal, degraded, and critical states, as well as
error handling during sensor readings.
"""

from unittest.mock import MagicMock

import pytest

from pysquared.config.config import Config
from pysquared.logger import Logger
from pysquared.power_health import CRITICAL, DEGRADED, NOMINAL, UNKNOWN, PowerHealth
from pysquared.protos.power_monitor import PowerMonitorProto
from pysquared.sensor_reading.current import Current
from pysquared.sensor_reading.voltage import Voltage


@pytest.fixture
def mock_logger():
    """Mocks the Logger class."""
    return MagicMock(spec=Logger)


@pytest.fixture
def mock_config():
    """Mocks the Config class with predefined power thresholds."""
    config = MagicMock(spec=Config)
    config.normal_charge_current = 100.0
    config.normal_battery_voltage = 7.2
    config.degraded_battery_voltage = 7.0
    config.critical_battery_voltage = 6.0
    return config


@pytest.fixture
def mock_power_monitor():
    """Mocks the PowerMonitorProto class."""
    monitor = MagicMock(spec=PowerMonitorProto)
    # Default mock return values as sensor reading objects
    monitor.get_bus_voltage.return_value = Voltage(7.2)
    monitor.get_current.return_value = Current(100.0)
    return monitor


@pytest.fixture
def power_health(mock_logger, mock_config, mock_power_monitor):
    """Provides a PowerHealth instance for testing."""
    return PowerHealth(
        logger=mock_logger,
        config=mock_config,
        power_monitor=mock_power_monitor,
    )


def test_power_health_initialization(
    power_health, mock_logger, mock_config, mock_power_monitor
):
    """Tests that PowerHealth initializes correctly.

    Args:
        power_health: PowerHealth instance for testing.
        mock_logger: Mocked Logger instance.
        mock_config: Mocked Config instance.
        mock_power_monitor: Mocked PowerMonitorProto instance.
    """
    assert power_health.logger == mock_logger
    assert power_health.config == mock_config
    assert power_health._power_monitor == mock_power_monitor


def test_get_nominal_state(power_health):
    """Tests that get() returns NOMINAL when all readings are within normal range.

    Args:
        power_health: PowerHealth instance for testing.
    """
    # Mock normal readings
    power_health._power_monitor.get_bus_voltage.return_value = Voltage(
        7.2
    )  # Normal voltage
    power_health._power_monitor.get_current.return_value = Current(
        100.0
    )  # Normal current

    result = power_health.get()

    assert isinstance(result, NOMINAL)
    power_health.logger.debug.assert_called_with("Power health is NOMINAL")


def test_get_critical_state_low_voltage(power_health):
    """Tests that get() returns CRITICAL when battery voltage is at/below critical threshold.

    Args:
        power_health: PowerHealth instance for testing.
    """
    # Mock critical voltage reading
    power_health._power_monitor.get_bus_voltage.return_value = Voltage(
        5.8
    )  # Below critical (6.0)
    power_health._power_monitor.get_current.return_value = Current(100.0)

    result = power_health.get()

    assert isinstance(result, CRITICAL)
    # Use any_order=True to handle call details, and check the values with pytest.approx for floating point precision
    call_args = power_health.logger.warning.call_args
    assert call_args[0] == ("Power is CRITICAL",)
    assert call_args[1]["voltage"] == pytest.approx(5.8, rel=1e-6)
    assert call_args[1]["threshold"] == 6.0


def test_get_critical_state_exactly_critical_voltage(power_health):
    """Tests that get() returns CRITICAL when battery voltage is exactly at critical threshold.

    Args:
        power_health: PowerHealth instance for testing.
    """
    # Mock exactly critical voltage reading
    power_health._power_monitor.get_bus_voltage.return_value = Voltage(
        6.0
    )  # Exactly critical
    power_health._power_monitor.get_current.return_value = Current(100.0)

    result = power_health.get()

    assert isinstance(result, CRITICAL)
    power_health.logger.warning.assert_called_with(
        "Power is CRITICAL",
        voltage=6.0,
        threshold=6.0,
    )


def test_get_degraded_state_current_deviation(power_health):
    """Tests that get() returns DEGRADED when current is outside normal range.

    Args:
        power_health: PowerHealth instance for testing.
    """
    # Mock readings with current deviation
    power_health._power_monitor.get_bus_voltage.return_value = Voltage(
        7.2
    )  # Normal voltage
    power_health._power_monitor.get_current.return_value = Current(
        250.0
    )  # Way above normal (100.0)

    result = power_health.get()

    assert isinstance(result, DEGRADED)
    power_health.logger.warning.assert_called_with(
        "Power is DEGRADED: Current above threshold",
        current=250.0,
        threshold=100.0,
    )


def test_get_degraded_state_voltage_deviation(power_health):
    """Tests that get() returns DEGRADED when voltage is at or below degraded threshold but not critical.

    Args:
        power_health: PowerHealth instance for testing.
    """
    power_health._power_monitor.get_bus_voltage.return_value = Voltage(
        6.8
    )  # Below degraded threshold (7.0) but above critical (6.0)
    power_health._power_monitor.get_current.return_value = Current(
        100.0
    )  # Normal current

    result = power_health.get()

    assert isinstance(result, DEGRADED)
    # Use pytest.approx for floating point precision
    call_args = power_health.logger.warning.call_args
    assert call_args[0] == ("Power is DEGRADED: Bus voltage below threshold",)
    assert call_args[1]["voltage"] == pytest.approx(6.8, rel=1e-6)
    assert call_args[1]["threshold"] == 7.0


def test_get_nominal_with_minor_voltage_deviation(power_health):
    """Tests that get() returns NOMINAL when voltage is above degraded threshold.

    Args:
        power_health: PowerHealth instance for testing.
    """
    power_health._power_monitor.get_bus_voltage.return_value = Voltage(
        7.1
    )  # Above degraded threshold (7.0)
    power_health._power_monitor.get_current.return_value = Current(
        100.0
    )  # Normal current

    result = power_health.get()

    assert isinstance(result, NOMINAL)
    power_health.logger.debug.assert_called_with("Power health is NOMINAL")


def test_get_with_exception_during_voltage_reading(power_health):
    """Tests get() when exception occurs during voltage reading.

    Args:
        power_health: PowerHealth instance for testing.
    """
    # Mock the sensor method to raise an exception
    test_exception = RuntimeError("Sensor communication error")
    power_health._power_monitor.get_bus_voltage.side_effect = test_exception

    result = power_health.get()

    assert isinstance(result, UNKNOWN)
    # The error is now a RuntimeError from avg_readings about func.__name__
    # Check that error was called with error message and some exception
    power_health.logger.error.assert_called_once()
    call_args = power_health.logger.error.call_args
    assert call_args[0][0] == "Error retrieving bus voltage"
    assert isinstance(call_args[0][1], Exception)  # Some exception was passed


def test_get_with_exception_during_current_reading(power_health):
    """Tests get() when exception occurs during current reading.

    Args:
        power_health: PowerHealth instance for testing.
    """
    # Mock voltage to work normally but current to raise exception
    power_health._power_monitor.get_bus_voltage.return_value = Voltage(7.2)
    test_exception = RuntimeError("Current sensor failed")
    power_health._power_monitor.get_current.side_effect = test_exception

    result = power_health.get()

    assert isinstance(result, UNKNOWN)
    # Check that error was called with error message and some exception
    power_health.logger.error.assert_called_once()
    call_args = power_health.logger.error.call_args
    assert call_args[0][0] == "Error retrieving current"
    assert isinstance(call_args[0][1], Exception)  # Some exception was passed


def test_get_with_sensor_method_exception(power_health):
    """Tests get() when the sensor method itself raises an exception.

    Args:
        power_health: PowerHealth instance for testing.
    """
    # Make the sensor method raise an exception directly
    test_exception = OSError("I2C communication failed")
    power_health._power_monitor.get_bus_voltage.side_effect = test_exception

    result = power_health.get()

    assert isinstance(result, UNKNOWN)
    # Check that error was called with error message and some exception
    power_health.logger.error.assert_called_once()
    call_args = power_health.logger.error.call_args
    assert call_args[0][0] == "Error retrieving bus voltage"
    assert isinstance(call_args[0][1], Exception)  # Some exception was passed


def test_degraded_vs_critical_voltage_boundaries(power_health):
    """Tests boundary conditions between degraded and critical voltage thresholds.

    Args:
        power_health: PowerHealth instance for testing.
    """
    # Test voltage just above critical but below degraded
    power_health._power_monitor.get_bus_voltage.return_value = Voltage(
        6.5
    )  # Above critical (6.0) but below degraded (7.0)
    power_health._power_monitor.get_current.return_value = Current(100.0)

    result = power_health.get()

    assert isinstance(result, DEGRADED)
    power_health.logger.warning.assert_called_with(
        "Power is DEGRADED: Bus voltage below threshold",
        voltage=6.5,
        threshold=7.0,
    )


def test_current_deviation_threshold(power_health):
    """Tests current deviation uses normal_charge_current as threshold.

    Args:
        power_health: PowerHealth instance for testing.
    """
    # normal_charge_current = 100.0, so deviation = 150 > 100 should trigger error
    power_health._power_monitor.get_bus_voltage.return_value = Voltage(7.2)
    power_health._power_monitor.get_current.return_value = Current(
        250.0
    )  # deviation = 150 > 100

    result = power_health.get()

    assert isinstance(result, DEGRADED)
    power_health.logger.warning.assert_called_with(
        "Power is DEGRADED: Current above threshold",
        current=250.0,
        threshold=100.0,
    )


def test_degraded_battery_voltage_threshold(power_health):
    """Tests that get() returns DEGRADED when voltage is exactly at degraded threshold.

    Args:
        power_health: PowerHealth instance for testing.
    """
    power_health._power_monitor.get_bus_voltage.return_value = Voltage(
        7.0
    )  # Exactly at degraded threshold
    power_health._power_monitor.get_current.return_value = Current(
        100.0
    )  # Normal current

    result = power_health.get()

    assert isinstance(result, DEGRADED)
    power_health.logger.warning.assert_called_with(
        "Power is DEGRADED: Bus voltage below threshold",
        voltage=7.0,
        threshold=7.0,
    )


def test_voltage_just_above_degraded_threshold(power_health):
    """Tests that get() returns NOMINAL when voltage is just above degraded threshold.

    Args:
        power_health: PowerHealth instance for testing.
    """
    power_health._power_monitor.get_bus_voltage.return_value = Voltage(
        7.01
    )  # Just above degraded threshold (7.0)
    power_health._power_monitor.get_current.return_value = Current(
        100.0
    )  # Normal current

    result = power_health.get()

    assert isinstance(result, NOMINAL)
    power_health.logger.debug.assert_called_with("Power health is NOMINAL")
