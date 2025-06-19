from unittest.mock import MagicMock

import microcontroller
import pytest

from mocks.circuitpython.byte_array import ByteArray
from pysquared.logger import Logger
from pysquared.nvm.counter import Counter
from pysquared.nvm.flag import Flag
from pysquared.protos.imu import IMUProto
from pysquared.protos.power_monitor import PowerMonitorProto
from pysquared.protos.radio import RadioProto
from pysquared.state_of_health import StateOfHealth, NOMINAL, DEGRADED
from pysquared.config.config import Config
from pysquared.protos.temperature_sensor import TemperatureSensorProto


@pytest.fixture
def state_of_health():
    # Mock dependencies
    logger = MagicMock(spec=Logger)
    config = MagicMock(spec=Config)
    config.normal_charge_current = 1.5
    config.normal_battery_voltage = 3.7
    config.normal_temp = 25
    config.normal_micro_temp = 45
    battery_power_monitor = MagicMock(spec=PowerMonitorProto, autospec=True)
    solar_power_monitor = MagicMock(spec=PowerMonitorProto, autospec=True)
    temperature_sensor = MagicMock(spec=TemperatureSensorProto, autospec=True)
    radio_manager = MagicMock()
    imu_manager = MagicMock()
    
    # Set up mock return values
    battery_power_monitor.get_bus_voltage.side_effect = [3.7] * 50
    battery_power_monitor.get_shunt_voltage.side_effect = [0.1] * 50
    battery_power_monitor.get_current.side_effect = [1.5] * 50
    solar_power_monitor.get_bus_voltage.side_effect = [5.0] * 50
    solar_power_monitor.get_shunt_voltage.side_effect = [0.1] * 50
    solar_power_monitor.get_current.side_effect = [2.0] * 50
    temperature_sensor.get_temperature.side_effect = [25.0] * 50
    radio_manager.get_temperature.return_value = 25.0
    imu_manager.get_temperature.return_value = 30.0
    microcontroller.cpu = MagicMock()
    microcontroller.cpu.temperature = 45.0

    # Remove .temperature from all mocks except microcontroller.cpu
    if hasattr(battery_power_monitor, 'temperature'):
        del battery_power_monitor.temperature
    if hasattr(solar_power_monitor, 'temperature'):
        del solar_power_monitor.temperature
    if hasattr(radio_manager, 'temperature'):
        del radio_manager.temperature
    if hasattr(imu_manager, 'temperature'):
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
        print('Logger.warning call args:', state_of_health.logger.warning.call_args)
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
    state_of_health._sensors[2].get_temperature.side_effect = [25 + 11.0] * 50
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
