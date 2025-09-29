"""Unit tests for the Beacon class.

This module contains unit tests for the `Beacon` class, which is responsible for
collecting and sending telemetry data. The tests cover initialization, basic
sending functionality, and sending with various sensor types.
"""

import sys
import time
from typing import Optional, Type
from unittest.mock import MagicMock, patch

import pytest
from freezegun import freeze_time

from mocks.circuitpython.byte_array import ByteArray
from mocks.circuitpython.microcontroller import Processor
from pysquared.hardware.radio.modulation import LoRa, RadioModulation
from pysquared.hardware.radio.packetizer.packet_manager import PacketManager
from pysquared.logger import Logger
from pysquared.nvm.counter import Counter
from pysquared.nvm.flag import Flag
from pysquared.protos.imu import IMUProto
from pysquared.protos.magnetometer import MagnetometerProto
from pysquared.protos.power_monitor import PowerMonitorProto
from pysquared.protos.radio import RadioProto
from pysquared.protos.temperature_sensor import TemperatureSensorProto
from pysquared.sensor_reading.acceleration import Acceleration
from pysquared.sensor_reading.angular_velocity import AngularVelocity
from pysquared.sensor_reading.avg import avg_readings
from pysquared.sensor_reading.current import Current
from pysquared.sensor_reading.magnetic import Magnetic
from pysquared.sensor_reading.temperature import Temperature
from pysquared.sensor_reading.voltage import Voltage

microcontroller = MagicMock()
microcontroller.Processor = Processor
sys.modules["microcontroller"] = microcontroller
from pysquared.beacon import Beacon  # noqa: E402


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


class MockMagnetometer(MagnetometerProto):
    """Mocks the MagnetometerProto for testing."""

    def get_magnetic_field(self) -> Magnetic:
        """Mocks the get_magnetic_field method."""
        return Magnetic(25.5, -12.3, 8.7)


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
        microcontroller.Processor(),
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
    key_map = beacon.generate_key_mapping()

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
        "MockTemperatureSensor_5_temperature_timestamp",
        "MockTemperatureSensor_5_temperature_value",
    ]

    # Add IMU keys (acceleration and angular_velocity with timestamp and values)
    expected_keys.extend(
        [
            "MockIMU_6_acceleration_timestamp",
            "MockIMU_6_angular_velocity_timestamp",
        ]
    )
    for i in range(3):
        expected_keys.append(f"MockIMU_6_acceleration_value_{i}")
        expected_keys.append(f"MockIMU_6_angular_velocity_value_{i}")

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


def test_beacon_build_state(mock_logger, mock_packet_manager):
    """Tests the _build_state method.

    Args:
        mock_logger: Mocked Logger instance.
        mock_packet_manager: Mocked PacketManager instance.
    """
    import time
    from unittest.mock import patch

    beacon = Beacon(mock_logger, "test_beacon", mock_packet_manager, 1000.0)

    # Mock time.time() and time.localtime()
    with (
        patch("time.time", return_value=1060.0),
        patch(
            "time.localtime",
            return_value=time.struct_time((2024, 1, 15, 10, 30, 45, 0, 0, 0)),
        ),
    ):
        state = beacon._build_state()

        # Verify basic state structure
        assert isinstance(state, dict)  # OrderedDict is a dict subclass
        assert state["name"] == "test_beacon"
        assert state["time"] == "2024-01-15 10:30:45"
        assert state["uptime"] == 60.0  # 1060 - 1000

        # Should have only basic fields for beacon with no sensors
        assert len(state) == 3


def test_beacon_encode_value(mock_logger, mock_packet_manager):
    """Tests the _encode_known_value method.

    Args:
        mock_logger: Mocked Logger instance.
        mock_packet_manager: Mocked PacketManager instance.
    """
    from pysquared.binary_encoder import BinaryEncoder

    beacon = Beacon(mock_logger, "test_beacon", mock_packet_manager, 0.0)
    encoder = BinaryEncoder()

    # Test integer encoding
    beacon._encode_known_value(encoder, "small_int", 100)
    beacon._encode_known_value(encoder, "medium_int", 30000)
    beacon._encode_known_value(encoder, "large_int", 2000000000)

    # Test float encoding
    beacon._encode_known_value(encoder, "test_float", 3.14)

    # Test string encoding
    beacon._encode_known_value(encoder, "test_string", "hello")

    # Test list encoding (3-element numeric)
    beacon._encode_known_value(encoder, "acceleration", [1.0, 2.0, 3.0])

    # Test list encoding (non-numeric)
    beacon._encode_known_value(encoder, "text_list", ["a", "b"])

    # Get encoded data and verify it can be decoded
    data = encoder.to_bytes()
    assert isinstance(data, bytes)
    assert len(data) > 0

    # Decode and verify expected values are present
    decoded = beacon.decode_binary_beacon(data, encoder.get_key_map())

    # Check that expected values are in the decoded data
    values = list(decoded.values())
    assert 100 in values
    assert 30000 in values
    assert 2000000000 in values
    assert any(abs(v - 3.14) < 0.01 for v in values if isinstance(v, float))
    assert "hello" in values
    # The list [1.0, 2.0, 3.0] should be split into individual float values
    assert any(abs(v - 1.0) < 0.01 for v in values if isinstance(v, float))
    assert any(abs(v - 2.0) < 0.01 for v in values if isinstance(v, float))
    assert any(abs(v - 3.0) < 0.01 for v in values if isinstance(v, float))
    # The text list should be converted to string
    assert "['a', 'b']" in values or '["a", "b"]' in values


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
        side_effect=Exception("Angular Velocity scope sensor failure")
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


def test_beacon_send_json_legacy_method(mock_logger, mock_packet_manager):
    """Tests the legacy send_json method.

    Args:
        mock_logger: Mocked Logger instance.
        mock_packet_manager: Mocked PacketManager instance.
    """
    beacon = Beacon(mock_logger, "test_beacon", mock_packet_manager, 0)

    result = beacon.send_json()

    # Verify the packet manager was called with JSON encoded data
    mock_packet_manager.send.assert_called_once()
    sent_data = mock_packet_manager.send.call_args[0][0]
    assert isinstance(sent_data, bytes)

    # Verify the result matches the packet manager's return value
    assert result == mock_packet_manager.send.return_value


def test_beacon_safe_float_convert_error_handling():
    """Tests the _safe_float_convert method error handling."""
    beacon = Beacon(MagicMock(spec=Logger), "test", MagicMock(spec=PacketManager), 0)

    # Test successful conversions
    assert beacon._safe_float_convert(42) == 42.0
    assert beacon._safe_float_convert(3.14) == 3.14
    assert beacon._safe_float_convert("2.5") == 2.5

    # Test error case - object that can't be converted to float
    with pytest.raises(ValueError, match="Cannot convert list to float"):
        beacon._safe_float_convert([1, 2, 3])


def test_beacon_generate_key_mapping(mock_logger, mock_packet_manager):
    """Tests the generate_key_mapping method.

    Args:
        mock_logger: Mocked Logger instance.
        mock_packet_manager: Mocked PacketManager instance.
    """
    beacon = Beacon(mock_logger, "test_beacon", mock_packet_manager, 0)

    key_map = beacon.generate_key_mapping()

    # Verify that a mapping dictionary is returned
    assert isinstance(key_map, dict)
    # The mapping should have entries for at least the basic system info
    assert len(key_map) > 0


@patch("pysquared.nvm.flag.microcontroller")
@patch("pysquared.nvm.counter.microcontroller")
def test_beacon_generate_key_mapping_with_sensors(
    mock_flag_microcontroller,
    mock_counter_microcontroller,
    mock_logger,
    mock_packet_manager,
):
    """Tests the generate_key_mapping method with various sensors.

    Args:
        mock_flag_microcontroller: Mocked microcontroller for Flag.
        mock_counter_microcontroller: Mocked microcontroller for Counter.
        mock_logger: Mocked Logger instance.
        mock_packet_manager: Mocked PacketManager instance.
    """
    mock_flag_microcontroller.nvm = setup_datastore
    mock_counter_microcontroller.nvm = setup_datastore

    # Create sensors to test template generation
    processor = Processor()
    flag = MockFlag(0, 0)
    counter = MockCounter(0)
    radio = MockRadio()
    imu = MockIMU()
    power_monitor = MockPowerMonitor()
    temp_sensor = MockTemperatureSensor()

    beacon = Beacon(
        mock_logger,
        "test_beacon",
        mock_packet_manager,
        0,
        processor,
        flag,
        counter,
        radio,
        imu,
        power_monitor,
        temp_sensor,
    )

    key_map = beacon.generate_key_mapping()

    # Verify comprehensive key mapping is generated
    assert isinstance(key_map, dict)
    assert len(key_map) > 10  # Should have many keys for all the sensors


def test_beacon_encode_sensor_dict_with_non_numeric_values():
    """Tests encoding sensor dictionaries with non-numeric values to cover line 186."""
    beacon = Beacon(MagicMock(spec=Logger), "test", MagicMock(spec=PacketManager), 0)

    # Create a mock encoder to test the encoding logic
    from unittest.mock import Mock

    encoder = Mock()
    encoder.add_string = Mock()
    encoder.add_float = Mock()
    encoder.to_bytes = Mock(return_value=b"test")

    # Test sensor data with non-numeric, non-3D list values
    sensor_data = {
        "status": "active",
        "mode": "normal",
        "calibration": {"x": 1, "y": 2},  # This will trigger line 186
    }

    beacon._encode_sensor_dict(encoder, "test_sensor", sensor_data)

    # Verify encoding completed without error
    encoded_data = encoder.to_bytes()
    assert isinstance(encoded_data, bytes)


@patch("pysquared.nvm.flag.microcontroller")
@patch("pysquared.nvm.counter.microcontroller")
def test_beacon_send_with_magnetometer(
    mock_flag_microcontroller,
    mock_counter_microcontroller,
    mock_logger,
    mock_packet_manager,
):
    """Tests sending a beacon with magnetometer sensor.

    Args:
        mock_flag_microcontroller: Mocked microcontroller for Flag.
        mock_counter_microcontroller: Mocked microcontroller for Counter.
        mock_logger: Mocked Logger instance.
        mock_packet_manager: Mocked PacketManager instance.
    """
    mock_flag_microcontroller.nvm = setup_datastore
    mock_counter_microcontroller.nvm = setup_datastore

    magnetometer = MockMagnetometer()

    beacon = Beacon(
        mock_logger,
        "test_beacon",
        mock_packet_manager,
        0,
        magnetometer,
    )

    result = beacon.send()

    # Verify the beacon was sent successfully
    assert result == mock_packet_manager.send.return_value
    mock_packet_manager.send.assert_called_once()

    # Decode the sent data to verify magnetometer data is included
    sent_data = mock_packet_manager.send.call_args[0][0]
    decoded_data = Beacon.decode_binary_beacon(sent_data)

    # Verify magnetometer data is present in the decoded data
    values = list(decoded_data.values())

    # Should contain the magnetic field components (25.5, -12.3, 8.7)
    # Use approximate comparison for floating point values
    assert any(abs(v - 25.5) < 0.01 for v in values if isinstance(v, (int, float)))
    assert any(abs(v - (-12.3)) < 0.01 for v in values if isinstance(v, (int, float)))
    assert any(abs(v - 8.7) < 0.01 for v in values if isinstance(v, (int, float)))


def test_beacon_send_with_magnetometer_error(mock_logger, mock_packet_manager):
    """Tests sending a beacon when magnetometer sensor fails.

    Args:
        mock_logger: Mocked Logger instance.
        mock_packet_manager: Mocked PacketManager instance.
    """
    magnetometer = MockMagnetometer()
    # Mock the get_magnetic_field method to raise an exception
    magnetometer.get_magnetic_field = MagicMock(
        side_effect=Exception("Magnetometer sensor failure")
    )

    beacon = Beacon(
        mock_logger,
        "test_beacon",
        mock_packet_manager,
        0,
        magnetometer,
    )

    _ = beacon.send()

    # Verify the error was logged
    mock_logger.error.assert_called_with(
        "Error retrieving magnetic field",
        magnetometer.get_magnetic_field.side_effect,
        sensor="MockMagnetometer",
        index=0,
    )

    # Verify beacon was still sent (despite the error)
    mock_packet_manager.send.assert_called_once()


@patch("pysquared.nvm.flag.microcontroller")
@patch("pysquared.nvm.counter.microcontroller")
def test_beacon_generate_key_mapping_with_magnetometer(
    mock_flag_microcontroller,
    mock_counter_microcontroller,
    mock_logger,
    mock_packet_manager,
):
    """Tests the generate_key_mapping method includes magnetometer template data.

    Args:
        mock_flag_microcontroller: Mocked microcontroller for Flag.
        mock_counter_microcontroller: Mocked microcontroller for Counter.
        mock_logger: Mocked Logger instance.
        mock_packet_manager: Mocked PacketManager instance.
    """
    mock_flag_microcontroller.nvm = setup_datastore
    mock_counter_microcontroller.nvm = setup_datastore

    magnetometer = MockMagnetometer()

    beacon = Beacon(
        mock_logger,
        "test_beacon",
        mock_packet_manager,
        0,
        magnetometer,
    )

    key_map = beacon.generate_key_mapping()

    # Verify comprehensive key mapping is generated
    assert isinstance(key_map, dict)

    # Check that magnetometer template keys are present in the mapping
    # The keys should include magnetometer timestamp and 3D magnetic field components
    key_names = list(key_map.values())
    magnetometer_keys = [key for key in key_names if "magnetic_field" in str(key)]

    # Should have at least 4 keys: timestamp + 3 components (x, y, z)
    assert len(magnetometer_keys) >= 4
