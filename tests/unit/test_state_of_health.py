import pytest
import sys
from unittest.mock import MagicMock
from mocks.circuitpython.microcontroller import Pin  # Import the mock Pin class

# Mock microcontroller and its attributes
sys.modules['microcontroller'] = MagicMock()
sys.modules['microcontroller'].nvm = MagicMock()
sys.modules['microcontroller'].Pin = Pin  # Use the mock Pin class
import microcontroller
import pysquared.nvm.counter as counter
from pysquared.state_of_health import StateOfHealth
from pysquared.logger import Logger
from pysquared.protos.imu import IMUProto
from pysquared.protos.power_monitor import PowerMonitorProto
from pysquared.protos.radio import RadioProto
from pysquared.satellite import Satellite


@pytest.fixture
def state_of_health():
    # Mock dependencies
    satellite = MagicMock(spec=Satellite)
    logger = MagicMock(spec=Logger)
    battery_power_monitor = MagicMock(spec=PowerMonitorProto)
    solar_power_monitor = MagicMock(spec=PowerMonitorProto)
    radio_manager = MagicMock(spec=RadioProto)
    imu_manager = MagicMock(spec=IMUProto)
    radio_manager.get_temperature = MagicMock(return_value=25.0)
    imu_manager.get_temperature = MagicMock(return_value=30.0)

    # Create StateOfHealth instance
    return StateOfHealth(
        c=satellite,
        logger=logger,
        battery_power_monitor=battery_power_monitor,
        solar_power_monitor=solar_power_monitor,
        radio_manager=radio_manager,
        imu_manager=imu_manager,
    )


def test_system_voltage(state_of_health):
    state_of_health.battery_power_monitor.get_bus_voltage.return_value = 3.7
    state_of_health.battery_power_monitor.get_shunt_voltage.return_value = 0.1

    result = state_of_health.system_voltage()

    assert result == pytest.approx(3.8, rel=1e-2)
    assert state_of_health.battery_power_monitor.get_bus_voltage.call_count == 50
    assert state_of_health.battery_power_monitor.get_shunt_voltage.call_count == 50


def test_battery_voltage(state_of_health):
    state_of_health.battery_power_monitor.get_bus_voltage.return_value = 3.7

    result = state_of_health.battery_voltage()

    assert result == pytest.approx(3.9, rel=1e-2)
    assert state_of_health.battery_power_monitor.get_bus_voltage.call_count == 50


def test_current_draw(state_of_health):
    state_of_health.battery_power_monitor.get_current.return_value = 1.5

    result = state_of_health.current_draw()

    assert result == pytest.approx(1.5, rel=1e-2)
    assert state_of_health.battery_power_monitor.get_current.call_count == 50


def test_charge_current(state_of_health):
    state_of_health.solar_power_monitor.get_current.return_value = 2.0

    result = state_of_health.charge_current()

    assert result == pytest.approx(2.0, rel=1e-2)
    assert state_of_health.solar_power_monitor.get_current.call_count == 50


def test_solar_voltage(state_of_health):
    state_of_health.solar_power_monitor.get_bus_voltage.return_value = 5.0

    result = state_of_health.solar_voltage()

    assert result == pytest.approx(5.0, rel=1e-2)
    assert state_of_health.solar_power_monitor.get_bus_voltage.call_count == 50


def test_update(state_of_health):
    # Mock return values for all dependencies
    state_of_health.system_voltage = MagicMock(return_value=3.8)
    state_of_health.current_draw = MagicMock(return_value=1.5)
    state_of_health.solar_voltage = MagicMock(return_value=5.0)
    state_of_health.charge_current = MagicMock(return_value=2.0)
    state_of_health.battery_voltage = MagicMock(return_value=3.9)
    state_of_health.radio_manager.get_temperature.return_value = 25.0
    state_of_health.radio_manager.get_modulation.return_value = "FSK"
    state_of_health.imu_manager.get_temperature.return_value = 30.0
    state_of_health.logger.get_error_count.return_value = 0
    state_of_health.c.power_mode = "Normal"
    state_of_health.c.get_system_uptime = 1000
    state_of_health.c.boot_count.get.return_value = 5
    state_of_health.c.f_burned.get.return_value = False
    state_of_health.c.f_brownout.get.return_value = False
    microcontroller.cpu.temperature = 45.0

    state_of_health.update()

    assert state_of_health.state["system_voltage"] == 3.8
    assert state_of_health.state["system_current"] == 1.5
    assert state_of_health.state["solar_voltage"] == 5.0
    assert state_of_health.state["solar_current"] == 2.0
    assert state_of_health.state["battery_voltage"] == 3.9
    assert state_of_health.state["radio_temperature"] == 25.0
    assert state_of_health.state["radio_modulation"] == "FSK"
    assert state_of_health.state["microcontroller_temperature"] == microcontroller.cpu.temperature
    assert state_of_health.state["internal_temperature"] == 30.0
    assert state_of_health.state["error_count"] == 0
    assert state_of_health.state["power_mode"] == "Normal"
    assert state_of_health.state["uptime"] == 1000
    assert state_of_health.state["boot_count"] == 5
    assert state_of_health.state["burned_flag"] is False
    assert state_of_health.state["brownout_flag"] is False