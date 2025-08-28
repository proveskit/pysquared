"""Unit tests for the Beacon class.

This module contains unit tests for the `Beacon` class, which is responsible for
collecting and sending telemetry data. The tests cover initialization, basic
sending functionality, and sending with various sensor types.
"""

import json
import time
from typing import Optional, Type
from unittest.mock import MagicMock, patch

import pytest
from freezegun import freeze_time

from mocks.circuitpython.byte_array import ByteArray
from mocks.circuitpython.microcontroller import Processor
from pysquared.beacon import Beacon
from pysquared.hardware.radio.modulation import LoRa, RadioModulation
from pysquared.hardware.radio.packetizer.packet_manager import PacketManager
from pysquared.logger import Logger
from pysquared.nvm.counter import Counter
from pysquared.nvm.flag import Flag
from pysquared.protos.imu import IMUProto
from pysquared.protos.power_monitor import PowerMonitorProto
from pysquared.protos.radio import RadioProto
from pysquared.protos.temperature_sensor import TemperatureSensorProto
from pysquared.sensor_reading.acceleration import Acceleration
from pysquared.sensor_reading.angular_velocity import AngularVelocity
from pysquared.sensor_reading.avg import avg_readings
from pysquared.sensor_reading.current import Current
from pysquared.sensor_reading.temperature import Temperature
from pysquared.sensor_reading.voltage import Voltage


@pytest.fixture
def mock_logger() -> MagicMock:
    """Mocks the Logger class."""
    return MagicMock(spec=Logger)


@pytest.fixture
def mock_packet_manager() -> MagicMock:
    """Mocks the PacketManager class."""
    return MagicMock(spec=PacketManager)


class MockRadio(RadioProto):
    """Mocks the RadioProto for testing."""

    def send(self, data: object) -> bool:
        """Mocks the send method."""
        return True

    def set_modulation(self, modulation: Type[RadioModulation]) -> None:
        """Mocks the set_modulation method."""
        pass

    def get_modulation(self) -> Type[RadioModulation]:
        """Mocks the get_modulation method."""
        return LoRa

    def receive(self, timeout: Optional[int] = None) -> Optional[bytes]:
        """Mocks the receive method."""
        return b"test_data"


class MockFlag(Flag):
    """Mocks the Flag class for testing."""

    def get(self) -> bool:
        """Mocks the get method."""
        return True

    def get_name(self) -> str:
        """Mocks the get_name method."""
        return "test_flag"


class MockCounter(Counter):
    """Mocks the Counter class for testing."""

    def get(self) -> int:
        """Mocks the get method."""
        return 42

    def get_name(self) -> str:
        """Mocks the get_name method."""
        return "test_counter"


class MockPowerMonitor(PowerMonitorProto):
    """Mocks the PowerMonitorProto for testing."""

    def get_current(self) -> Current:
        """Mocks the get_current method."""
        return Current(0.5)

    def get_bus_voltage(self) -> Voltage:
        """Mocks the get_bus_voltage method."""
        return Voltage(3.3)

    def get_shunt_voltage(self) -> Voltage:
        """Mocks the get_shunt_voltage method."""
        return Voltage(0.1)


class MockTemperatureSensor(TemperatureSensorProto):
    """Mocks the TemperatureSensorProto for testing."""

    def get_temperature(self) -> Temperature:
        """Mocks the get_temperature method."""
        return Temperature(22.5)


class MockIMU(IMUProto):
    """Mocks the IMUProto for testing."""

    def get_angular_velocity(self) -> AngularVelocity:
        """Mocks the get_angular_velocity method."""
        return AngularVelocity(0.1, 2.3, 4.5)

    def get_acceleration(self) -> Acceleration:
        """Mocks the get_acceleration method."""
        return Acceleration(5.4, 3.2, 1.0)


def test_beacon_init(mock_logger, mock_packet_manager):
    """Tests Beacon initialization.

    Args:
        mock_logger: Mocked Logger instance.
        mock_packet_manager: Mocked PacketManager instance.
    """
    boot_time = time.time()
    beacon = Beacon(mock_logger, "test_beacon", mock_packet_manager, boot_time)

    assert beacon._log is mock_logger
    assert beacon._name == "test_beacon"
    assert beacon._packet_manager is mock_packet_manager
    assert beacon._boot_time == boot_time
    assert beacon._sensors == ()


@freeze_time(time_to_freeze="2025-05-16 12:34:56", tz_offset=0)
@patch("time.time")
def test_beacon_send_basic(mock_time, mock_logger, mock_packet_manager):
    """Tests sending a basic beacon with no sensors.

    Args:
        mock_time: Mocked time.time function.
        mock_logger: Mocked Logger instance.
        mock_packet_manager: Mocked PacketManager instance.
    """
    boot_time = 1000.0
    mock_time.return_value = 1060.0  # 60 seconds after boot

    beacon = Beacon(mock_logger, "test_beacon", mock_packet_manager, boot_time)
    _ = beacon.send()

    mock_packet_manager.send.assert_called_once()
    send_args = mock_packet_manager.send.call_args[0][0]
    d = json.loads(send_args)
    assert d["name"] == "test_beacon"
    assert d["time"] == time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    assert d["uptime"] == 60.0


@pytest.fixture
def setup_datastore():
    """Sets up a mock datastore for NVM components."""
    return ByteArray(size=17)


@patch("pysquared.nvm.flag.microcontroller")
@patch("pysquared.nvm.counter.microcontroller")
def test_beacon_send_with_sensors(
    mock_flag_microcontroller,
    mock_counter_microcontroller,
    mock_logger,
    mock_packet_manager,
):
    """Tests sending a beacon with various sensor types.

    Args:
        mock_flag_microcontroller: Mocked microcontroller for Flag.
        mock_counter_microcontroller: Mocked microcontroller for Counter.
        mock_logger: Mocked Logger instance.
        mock_packet_manager: Mocked PacketManager instance.
    """
    mock_flag_microcontroller.nvm = (
        setup_datastore  # Mock the nvm module to use the ByteArray
    )
    mock_counter_microcontroller.nvm = (
        setup_datastore  # Mock the nvm module to use the ByteArray
    )

    beacon = Beacon(
        mock_logger,
        "test_beacon",
        mock_packet_manager,
        0,
        Processor(),
        MockFlag(0, 0),
        MockCounter(0),
        MockRadio(),
        MockPowerMonitor(),
        MockTemperatureSensor(),
        MockIMU(),
    )

    _ = beacon.send()

    mock_packet_manager.send.assert_called_once()
    send_args = mock_packet_manager.send.call_args[0][0]
    d = json.loads(send_args)

    # processor sensor
    assert pytest.approx(d["Processor_0_temperature"], 0.01) == 35.0

    # flag
    assert d["test_flag_1"] is True

    # counter
    assert d["test_counter_2"] == 42

    # radio
    assert d["MockRadio_3_modulation"] == "LoRa"

    # power monitor sensor
    assert pytest.approx(d["MockPowerMonitor_4_current_avg"], 0.01) == 0.5
    assert pytest.approx(d["MockPowerMonitor_4_bus_voltage_avg"], 0.01) == 3.3
    assert pytest.approx(d["MockPowerMonitor_4_shunt_voltage_avg"], 0.01) == 0.1

    # temperature sensor
    assert (
        pytest.approx(d["MockTemperatureSensor_5_temperature"]["value"], 0.01) == 22.5
    )
    assert d["MockTemperatureSensor_5_temperature"]["timestamp"] is not None

    # IMU sensor
    assert pytest.approx(d["MockIMU_6_angular_velocity"]["value"][0], 0.1) == 0.1
    assert pytest.approx(d["MockIMU_6_angular_velocity"]["value"][1], 0.1) == 2.3
    assert pytest.approx(d["MockIMU_6_angular_velocity"]["value"][2], 0.1) == 4.5
    assert d["MockIMU_6_angular_velocity"]["timestamp"] is not None
    assert pytest.approx(d["MockIMU_6_acceleration"]["value"][0], 0.1) == 5.4
    assert pytest.approx(d["MockIMU_6_acceleration"]["value"][1], 0.1) == 3.2
    assert pytest.approx(d["MockIMU_6_acceleration"]["value"][2], 0.1) == 1.0
    assert d["MockIMU_6_acceleration"]["timestamp"] is not None


def test_avg_readings_function():
    """Tests the avg_readings standalone function."""

    # Test with a function that returns consistent values
    def constant_func():
        """Returns a constant value."""
        return Voltage(5.0)

    result = avg_readings(constant_func, num_readings=5)
    assert pytest.approx(result, 0.01) == 5.0

    # Test with a function that raises an exception
    def error_func():
        """Raises an exception to simulate a sensor failure."""
        raise Exception("Sensor error")

    with pytest.raises(RuntimeError, match="Error retrieving reading from error_func"):
        avg_readings(error_func)


def test_avg_readings_varying_values():
    """Tests avg_readings with values that vary."""
    # Create a simple counter function that returns incrementing values
    # Starting from 1 and incrementing by 1 each time
    values = list(range(1, 6))  # [1, 2, 3, 4, 5]
    expected_avg = sum(values) / len(values)  # (1+2+3+4+5)/5 = 15/5 = 3

    read_count = 0

    def incrementing_func():
        """Returns incrementing values from the list."""
        nonlocal read_count
        value = values[read_count % len(values)]
        read_count += 1
        return Voltage(value)

    # Test with a specific number of readings that's a multiple of our pattern length
    result = avg_readings(incrementing_func, num_readings=5)
    assert result == expected_avg


@patch("pysquared.nvm.flag.microcontroller")
@patch("pysquared.nvm.counter.microcontroller")
def test_beacon_send_with_imu_acceleration_error(
    mock_flag_microcontroller,
    mock_counter_microcontroller,
    mock_logger,
    mock_packet_manager,
):
    """Tests sending a beacon when IMU acceleration sensor fails.

    Args:
        mock_flag_microcontroller: Mocked microcontroller for Flag.
        mock_counter_microcontroller: Mocked microcontroller for Counter.
        mock_logger: Mocked Logger instance.
        mock_packet_manager: Mocked PacketManager instance.
    """
    mock_flag_microcontroller.nvm = setup_datastore
    mock_counter_microcontroller.nvm = setup_datastore

    imu = MockIMU()
    # Mock the get_acceleration method to raise an exception
    imu.get_acceleration = MagicMock(
        side_effect=Exception("Acceleration sensor failure")
    )

    beacon = Beacon(
        mock_logger,
        "test_beacon",
        mock_packet_manager,
        0,
        imu,
    )

    _ = beacon.send()

    # Verify the error was logged
    mock_logger.error.assert_called_with(
        "Error retrieving acceleration",
        imu.get_acceleration.side_effect,
        sensor="MockIMU",
        index=0,
    )

    # Verify beacon was still sent (despite the error)
    mock_packet_manager.send.assert_called_once()


@patch("pysquared.nvm.flag.microcontroller")
@patch("pysquared.nvm.counter.microcontroller")
def test_beacon_send_with_imu_angular_velocity_error(
    mock_flag_microcontroller,
    mock_counter_microcontroller,
    mock_logger,
    mock_packet_manager,
):
    """Tests sending a beacon when IMU angular_velocity sensor fails.

    Args:
        mock_flag_microcontroller: Mocked microcontroller for Flag.
        mock_counter_microcontroller: Mocked microcontroller for Counter.
        mock_logger: Mocked Logger instance.
        mock_packet_manager: Mocked PacketManager instance.
    """
    mock_flag_microcontroller.nvm = setup_datastore
    mock_counter_microcontroller.nvm = setup_datastore

    imu = MockIMU()
    # Mock the get_angular_velocity method to raise an exception
    imu.get_angular_velocity = MagicMock(
        side_effect=Exception("AngularVelocityscope sensor failure")
    )

    beacon = Beacon(
        mock_logger,
        "test_beacon",
        mock_packet_manager,
        0,
        imu,
    )

    _ = beacon.send()

    # Verify the error was logged
    mock_logger.error.assert_called_with(
        "Error retrieving angular velocity",
        imu.get_angular_velocity.side_effect,
        sensor="MockIMU",
        index=0,
    )

    # Verify beacon was still sent (despite the error)
    mock_packet_manager.send.assert_called_once()


@patch("pysquared.nvm.flag.microcontroller")
@patch("pysquared.nvm.counter.microcontroller")
def test_beacon_send_with_power_monitor_current_error(
    mock_flag_microcontroller,
    mock_counter_microcontroller,
    mock_logger,
    mock_packet_manager,
):
    """Tests sending a beacon when power monitor current sensor fails.

    Args:
        mock_flag_microcontroller: Mocked microcontroller for Flag.
        mock_counter_microcontroller: Mocked microcontroller for Counter.
        mock_logger: Mocked Logger instance.
        mock_packet_manager: Mocked PacketManager instance.
    """
    mock_flag_microcontroller.nvm = setup_datastore
    mock_counter_microcontroller.nvm = setup_datastore

    power_monitor = MockPowerMonitor()
    # Mock the get_current method to raise an exception
    power_monitor.get_current = MagicMock(
        side_effect=Exception("Current sensor failure")
    )
    power_monitor.get_current.__name__ = "get_current"

    beacon = Beacon(
        mock_logger,
        "test_beacon",
        mock_packet_manager,
        0,
        power_monitor,
    )

    _ = beacon.send()

    # Verify the error was logged
    mock_logger.error.assert_called_with(
        "Error retrieving current",
        mock_logger.error.call_args[0][1],  # The actual RuntimeError that was raised
        sensor="MockPowerMonitor",
        index=0,
    )
    # Verify the exception is a RuntimeError from avg_readings
    assert isinstance(mock_logger.error.call_args[0][1], RuntimeError)
    assert "Error retrieving reading from get_current" in str(
        mock_logger.error.call_args[0][1]
    )

    # Verify beacon was still sent (despite the error)
    mock_packet_manager.send.assert_called_once()


@patch("pysquared.nvm.flag.microcontroller")
@patch("pysquared.nvm.counter.microcontroller")
def test_beacon_send_with_power_monitor_bus_voltage_error(
    mock_flag_microcontroller,
    mock_counter_microcontroller,
    mock_logger,
    mock_packet_manager,
):
    """Tests sending a beacon when power monitor bus voltage sensor fails.

    Args:
        mock_flag_microcontroller: Mocked microcontroller for Flag.
        mock_counter_microcontroller: Mocked microcontroller for Counter.
        mock_logger: Mocked Logger instance.
        mock_packet_manager: Mocked PacketManager instance.
    """
    mock_flag_microcontroller.nvm = setup_datastore
    mock_counter_microcontroller.nvm = setup_datastore

    power_monitor = MockPowerMonitor()
    # Mock the get_bus_voltage method to raise an exception
    power_monitor.get_bus_voltage = MagicMock(
        side_effect=Exception("Bus voltage sensor failure")
    )
    power_monitor.get_bus_voltage.__name__ = "get_bus_voltage"

    beacon = Beacon(
        mock_logger,
        "test_beacon",
        mock_packet_manager,
        0,
        power_monitor,
    )

    _ = beacon.send()

    # Verify the error was logged
    mock_logger.error.assert_called_with(
        "Error retrieving bus voltage",
        mock_logger.error.call_args[0][1],  # The actual RuntimeError that was raised
        sensor="MockPowerMonitor",
        index=0,
    )
    # Verify the exception is a RuntimeError from avg_readings
    assert isinstance(mock_logger.error.call_args[0][1], RuntimeError)
    assert "Error retrieving reading from get_bus_voltage" in str(
        mock_logger.error.call_args[0][1]
    )

    # Verify beacon was still sent (despite the error)
    mock_packet_manager.send.assert_called_once()


@patch("pysquared.nvm.flag.microcontroller")
@patch("pysquared.nvm.counter.microcontroller")
def test_beacon_send_with_power_monitor_shunt_voltage_error(
    mock_flag_microcontroller,
    mock_counter_microcontroller,
    mock_logger,
    mock_packet_manager,
):
    """Tests sending a beacon when power monitor shunt voltage sensor fails.

    Args:
        mock_flag_microcontroller: Mocked microcontroller for Flag.
        mock_counter_microcontroller: Mocked microcontroller for Counter.
        mock_logger: Mocked Logger instance.
        mock_packet_manager: Mocked PacketManager instance.
    """
    mock_flag_microcontroller.nvm = setup_datastore
    mock_counter_microcontroller.nvm = setup_datastore

    power_monitor = MockPowerMonitor()
    # Mock the get_shunt_voltage method to raise an exception
    power_monitor.get_shunt_voltage = MagicMock(
        side_effect=Exception("Shunt voltage sensor failure")
    )
    power_monitor.get_shunt_voltage.__name__ = "get_shunt_voltage"

    beacon = Beacon(
        mock_logger,
        "test_beacon",
        mock_packet_manager,
        0,
        power_monitor,
    )

    _ = beacon.send()

    # Verify the error was logged
    mock_logger.error.assert_called_with(
        "Error retrieving shunt voltage",
        mock_logger.error.call_args[0][1],  # The actual RuntimeError that was raised
        sensor="MockPowerMonitor",
        index=0,
    )
    # Verify the exception is a RuntimeError from avg_readings
    assert isinstance(mock_logger.error.call_args[0][1], RuntimeError)
    assert "Error retrieving reading from get_shunt_voltage" in str(
        mock_logger.error.call_args[0][1]
    )

    # Verify beacon was still sent (despite the error)
    mock_packet_manager.send.assert_called_once()


@patch("pysquared.nvm.flag.microcontroller")
@patch("pysquared.nvm.counter.microcontroller")
def test_beacon_send_with_temperature_sensor_error(
    mock_flag_microcontroller,
    mock_counter_microcontroller,
    mock_logger,
    mock_packet_manager,
):
    """Tests sending a beacon when temperature sensor fails.

    Args:
        mock_flag_microcontroller: Mocked microcontroller for Flag.
        mock_counter_microcontroller: Mocked microcontroller for Counter.
        mock_logger: Mocked Logger instance.
        mock_packet_manager: Mocked PacketManager instance.
    """
    mock_flag_microcontroller.nvm = setup_datastore
    mock_counter_microcontroller.nvm = setup_datastore

    temp_sensor = MockTemperatureSensor()
    # Mock the get_temperature method to raise an exception
    temp_sensor.get_temperature = MagicMock(
        side_effect=Exception("Temperature sensor failure")
    )

    beacon = Beacon(
        mock_logger,
        "test_beacon",
        mock_packet_manager,
        0,
        temp_sensor,
    )

    _ = beacon.send()

    # Verify the error was logged
    mock_logger.error.assert_called_with(
        "Error retrieving temperature",
        temp_sensor.get_temperature.side_effect,
        sensor="MockTemperatureSensor",
        index=0,
    )

    # Verify beacon was still sent (despite the error)
    mock_packet_manager.send.assert_called_once()


@patch("pysquared.nvm.flag.microcontroller")
@patch("pysquared.nvm.counter.microcontroller")
def test_beacon_send_with_multiple_sensor_errors(
    mock_flag_microcontroller,
    mock_counter_microcontroller,
    mock_logger,
    mock_packet_manager,
):
    """Tests sending a beacon when multiple sensors fail.

    Args:
        mock_flag_microcontroller: Mocked microcontroller for Flag.
        mock_counter_microcontroller: Mocked microcontroller for Counter.
        mock_logger: Mocked Logger instance.
        mock_packet_manager: Mocked PacketManager instance.
    """
    mock_flag_microcontroller.nvm = setup_datastore
    mock_counter_microcontroller.nvm = setup_datastore

    imu = MockIMU()
    power_monitor = MockPowerMonitor()
    temp_sensor = MockTemperatureSensor()

    # Mock multiple methods to raise exceptions
    imu.get_acceleration = MagicMock(
        side_effect=Exception("Acceleration sensor failure")
    )
    power_monitor.get_current = MagicMock(
        side_effect=Exception("Current sensor failure")
    )
    power_monitor.get_current.__name__ = "get_current"
    temp_sensor.get_temperature = MagicMock(
        side_effect=Exception("Temperature sensor failure")
    )

    beacon = Beacon(
        mock_logger,
        "test_beacon",
        mock_packet_manager,
        0,
        imu,
        power_monitor,
        temp_sensor,
    )

    _ = beacon.send()

    # Verify all errors were logged
    assert mock_logger.error.call_count == 3

    # Check that the correct error messages were logged
    calls = mock_logger.error.call_args_list
    error_messages = [call[0][0] for call in calls]

    assert "Error retrieving acceleration" in error_messages
    assert "Error retrieving current" in error_messages
    assert "Error retrieving temperature" in error_messages

    # Verify beacon was still sent (despite the errors)
    mock_packet_manager.send.assert_called_once()
