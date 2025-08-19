"""Unit tests for the Beacon class.

This module contains unit tests for the `Beacon` class, which is responsible for
collecting and sending telemetry data. The tests cover initialization, basic
sending functionality, and sending with various sensor types.
"""

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
from pysquared.sensor_reading.temperature import Temperature


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

    def get_temperature(self) -> Temperature:
        """Mocks the get_temperature method."""
        return Temperature(22.5)


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

    # Data is now binary encoded, so we need to decode it
    d = Beacon.decode_binary_beacon(send_args)

    # Check that we have the expected values (decoded values are present)
    values = list(d.values())
    assert "test_beacon" in values  # name value
    assert 60.0 in values  # uptime should be 60.0


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

    # Data is now binary encoded, decode without key map (will use generic field names)
    d = Beacon.decode_binary_beacon(send_args)

    # With binary encoding and no key map, we can't easily check specific field names
    # but we can verify that the expected values are present
    values = list(d.values())
    assert 35.0 in values  # processor temperature
    assert 1 in values  # flag value (True becomes 1)
    assert 42 in values  # counter value
    assert "LoRa" in values  # radio modulation
    assert any(
        abs(v - 0.5) < 0.01 for v in values if isinstance(v, float)
    )  # power monitor current
    assert any(
        abs(v - 3.3) < 0.01 for v in values if isinstance(v, float)
    )  # bus voltage
    assert any(
        abs(v - 22.5) < 0.01 for v in values if isinstance(v, float)
    )  # temperature
    # IMU values should be present as individual float values
    assert any(abs(v - 0.1) < 0.1 for v in values if isinstance(v, float))  # gyro x
    assert any(abs(v - 2.3) < 0.1 for v in values if isinstance(v, float))  # gyro y
    assert any(abs(v - 5.4) < 0.1 for v in values if isinstance(v, float))  # accel x


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


@patch("pysquared.nvm.flag.microcontroller")
@patch("pysquared.nvm.counter.microcontroller")
def test_beacon_create_key_map(
    mock_flag_microcontroller,
    mock_counter_microcontroller,
    mock_logger,
    mock_packet_manager,
):
    """Tests the create_key_map method.

    Args:
        mock_flag_microcontroller: Mocked microcontroller for Flag.
        mock_counter_microcontroller: Mocked microcontroller for Counter.
        mock_logger: Mocked Logger instance.
        mock_packet_manager: Mocked PacketManager instance.
    """
    mock_flag_microcontroller.nvm = setup_datastore
    mock_counter_microcontroller.nvm = setup_datastore

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

    # Test create_key_map
    key_map = beacon.create_key_map()

    # Verify key_map is a dictionary
    assert isinstance(key_map, dict)

    # Verify it contains expected keys
    expected_keys = [
        "name",
        "time",
        "uptime",
        "Processor_0_temperature",
        "test_flag_1",
        "test_counter_2",
        "MockRadio_3_modulation",
        "MockPowerMonitor_4_current_avg",
        "MockPowerMonitor_4_bus_voltage_avg",
        "MockPowerMonitor_4_shunt_voltage_avg",
        "MockTemperatureSensor_5_temperature",
        "MockTemperatureSensor_5_temperature_timestamp",
    ]

    # Add IMU keys (acceleration and gyroscope, 3 components each)
    for i in range(3):
        expected_keys.append(f"MockIMU_6_acceleration_{i}")
        expected_keys.append(f"MockIMU_6_gyroscope_{i}")

    # Check that all expected keys are present in the values of key_map
    key_map_values = set(key_map.values())
    for expected_key in expected_keys:
        assert expected_key in key_map_values, (
            f"Expected key '{expected_key}' not found in key_map"
        )

    # Verify key_map maps hashes to key names
    for hash_val, key_name in key_map.items():
        assert isinstance(hash_val, int)
        assert isinstance(key_name, str)


def test_beacon_encode_binary_state(mock_logger, mock_packet_manager):
    """Tests the _encode_binary_state method.

    Args:
        mock_logger: Mocked Logger instance.
        mock_packet_manager: Mocked PacketManager instance.
    """
    from collections import OrderedDict

    beacon = Beacon(mock_logger, "test_beacon", mock_packet_manager, 0.0)

    # Create test state data
    state = OrderedDict()
    state["name"] = "TestSat"
    state["uptime"] = 123.45
    state["battery_level"] = 85
    state["temperature"] = 22.5
    state["acceleration"] = [0.1, 0.2, 9.8]  # Test tuple/list handling
    state["status"] = True  # Test non-numeric, non-string data

    # Test the method
    binary_data = beacon._encode_binary_state(state)

    # Verify it returns bytes
    assert isinstance(binary_data, bytes)
    assert len(binary_data) > 0

    # Verify we can decode the data
    decoded = Beacon.decode_binary_beacon(binary_data)

    # Check that decoded data contains expected values
    decoded_values = list(decoded.values())
    assert "TestSat" in decoded_values
    assert any(abs(v - 123.45) < 0.01 for v in decoded_values if isinstance(v, float))
    assert 85 in decoded_values
    assert any(abs(v - 22.5) < 0.01 for v in decoded_values if isinstance(v, float))
    # Array should be split into individual float values
    assert any(abs(v - 0.1) < 0.01 for v in decoded_values if isinstance(v, float))
    assert any(abs(v - 0.2) < 0.01 for v in decoded_values if isinstance(v, float))
    assert any(abs(v - 9.8) < 0.01 for v in decoded_values if isinstance(v, float))
    # Boolean True should be treated as integer 1 (since bool is subclass of int)
    assert 1 in decoded_values


def test_beacon_encode_binary_state_integer_sizing(mock_logger, mock_packet_manager):
    """Tests _encode_binary_state integer size optimization.

    Args:
        mock_logger: Mocked Logger instance.
        mock_packet_manager: Mocked PacketManager instance.
    """
    from collections import OrderedDict

    beacon = Beacon(mock_logger, "test_beacon", mock_packet_manager, 0.0)

    # Test different integer sizes
    state = OrderedDict()
    state["small_int"] = 100  # Should use 1 byte
    state["medium_int"] = 30000  # Should use 2 bytes
    state["large_int"] = 2000000000  # Should use 4 bytes

    binary_data = beacon._encode_binary_state(state)

    # Verify encoding and decoding works
    assert isinstance(binary_data, bytes)
    decoded = Beacon.decode_binary_beacon(binary_data)

    decoded_values = list(decoded.values())
    assert 100 in decoded_values
    assert 30000 in decoded_values
    assert 2000000000 in decoded_values


def test_beacon_encode_binary_state_edge_cases(mock_logger, mock_packet_manager):
    """Tests _encode_binary_state with edge cases.

    Args:
        mock_logger: Mocked Logger instance.
        mock_packet_manager: Mocked PacketManager instance.
    """
    from collections import OrderedDict

    beacon = Beacon(mock_logger, "test_beacon", mock_packet_manager, 0.0)

    # Test edge cases
    state = OrderedDict()
    state["empty_list"] = []  # Empty array
    state["non_numeric_list"] = ["a", "b"]  # Non-numeric array
    state["mixed_list"] = [1, "text", 2.5]  # Mixed array
    state["none_value"] = None  # None value

    binary_data = beacon._encode_binary_state(state)

    # Should handle gracefully and return valid binary data
    assert isinstance(binary_data, bytes)
    decoded = Beacon.decode_binary_beacon(binary_data)

    # All values should be converted to strings for complex/unsupported types
    decoded_values = list(decoded.values())
    assert "[]" in decoded_values
    assert "['a', 'b']" in decoded_values or '["a", "b"]' in decoded_values
    assert any("text" in str(v) for v in decoded_values)  # Mixed list as string
    assert "None" in decoded_values
