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

    def get_current(self) -> float:
        """Mocks the get_current method."""
        return 0.5

    def get_bus_voltage(self) -> float:
        """Mocks the get_bus_voltage method."""
        return 3.3

    def get_shunt_voltage(self) -> float:
        """Mocks the get_shunt_voltage method."""
        return 0.1


class MockTemperatureSensor(TemperatureSensorProto):
    """Mocks the TemperatureSensorProto for testing."""

    def get_temperature(self) -> float:
        """Mocks the get_temperature method."""
        return 22.5


class MockIMU(IMUProto):
    """Mocks the IMUProto for testing."""

    def get_gyro_data(self) -> tuple[float, float, float]:
        """Mocks the get_gyro_data method."""
        return (0.1, 2.3, 4.5)

    def get_acceleration(self) -> tuple[float, float, float]:
        """Mocks the get_acceleration method."""
        return (5.4, 3.2, 1.0)


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
    assert pytest.approx(d["MockTemperatureSensor_5_temperature"], 0.01) == 22.5

    # IMU sensor
    assert pytest.approx(d["MockIMU_6_gyroscope"][0], 0.1) == 0.1
    assert pytest.approx(d["MockIMU_6_gyroscope"][1], 0.1) == 2.3
    assert pytest.approx(d["MockIMU_6_gyroscope"][2], 0.1) == 4.5
    assert pytest.approx(d["MockIMU_6_acceleration"][0], 0.1) == 5.4
    assert pytest.approx(d["MockIMU_6_acceleration"][1], 0.1) == 3.2
    assert pytest.approx(d["MockIMU_6_acceleration"][2], 0.1) == 1.0


def test_beacon_avg_readings(mock_logger, mock_packet_manager):
    """Tests the avg_readings method in the context of the Beacon class.

    Args:
        mock_logger: Mocked Logger instance.
        mock_packet_manager: Mocked PacketManager instance.
    """
    beacon = Beacon(mock_logger, "test_beacon", mock_packet_manager, 0.0)

    # Test with a function that returns consistent values
    def constant_func():
        """Returns a constant value."""
        return 5.0

    result = beacon.avg_readings(constant_func, num_readings=5)
    assert pytest.approx(result, 0.01) == 5.0

    # Test with a function that returns None
    def none_func():
        """Returns None to simulate a sensor failure."""
        return None

    result = beacon.avg_readings(none_func)
    assert result is None
    mock_logger.warning.assert_called_once()


def test_avg_readings_varying_values(mock_logger, mock_packet_manager):
    """Tests avg_readings with values that vary.

    Args:
        mock_logger: Mocked Logger instance.
        mock_packet_manager: Mocked PacketManager instance.
    """
    beacon = Beacon(mock_logger, "test_beacon", mock_packet_manager, 0.0)

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
        return value

    # Test with a specific number of readings that's a multiple of our pattern length
    result = beacon.avg_readings(incrementing_func, num_readings=5)
    assert result == expected_avg
