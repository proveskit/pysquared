import time
from typing import Optional, Type
from unittest.mock import MagicMock, patch

import pytest
from freezegun import freeze_time

from mocks.circuitpython.byte_array import ByteArray
from mocks.circuitpython.microcontroller import Processor
from pysquared.beacon import Beacon
from pysquared.hardware.radio.modulation import LoRa, RadioModulation
from pysquared.logger import Logger
from pysquared.nvm.counter import Counter
from pysquared.nvm.flag import Flag
from pysquared.protos.power_monitor import PowerMonitorProto
from pysquared.protos.radio import RadioProto
from pysquared.protos.temperature_sensor import TemperatureSensorProto


@pytest.fixture
def mock_logger() -> MagicMock:
    return MagicMock(spec=Logger)


@pytest.fixture
def mock_radio() -> MagicMock:
    radio = MagicMock(spec=RadioProto)
    # Set up get_modulation to return LoRa
    radio.get_modulation.return_value = LoRa
    radio.send.return_value = True
    return radio


class MockRadio(RadioProto):
    def send(self, data: object) -> bool:
        return True

    def set_modulation(self, modulation: Type[RadioModulation]) -> None:
        pass

    def get_modulation(self) -> Type[RadioModulation]:
        return LoRa

    def receive(self, timeout: Optional[int] = None) -> Optional[bytes]:
        return b"test_data"


# class MockProcessor(Processor):
#     temperature: float = 25.0


class MockFlag(Flag):
    def get(self) -> bool:
        return True

    def get_name(self) -> str:
        return "test_flag"


class MockCounter(Counter):
    def get(self) -> int:
        return 42

    def get_name(self) -> str:
        return "test_counter"


class MockPowerMonitor(PowerMonitorProto):
    def get_current(self) -> float:
        return 0.5

    def get_bus_voltage(self) -> float:
        return 3.3

    def get_shunt_voltage(self) -> float:
        return 0.1


class MockTemperatureSensor(TemperatureSensorProto):
    def get_temperature(self) -> float:
        return 22.5


def test_beacon_init(mock_logger, mock_radio):
    """Test Beacon initialization."""
    boot_time = time.time()
    beacon = Beacon(mock_logger, "test_beacon", mock_radio, boot_time)

    assert beacon._log is mock_logger
    assert beacon._name == "test_beacon"
    assert beacon._radio is mock_radio
    assert beacon._boot_time == boot_time
    assert beacon._sensors == ()


@freeze_time(time_to_freeze="2025-05-16 12:34:56", tz_offset=0)
@patch("time.time")
def test_beacon_send_basic(mock_time, mock_logger, mock_radio):
    """Test sending a basic beacon with no sensors."""
    boot_time = 1000.0
    mock_time.return_value = 1060.0  # 60 seconds after boot

    beacon = Beacon(mock_logger, "test_beacon", mock_radio, boot_time)
    result = beacon.send()

    assert result is True
    mock_radio.send.assert_called_once()
    state_dict = mock_radio.send.call_args[0][0]
    assert state_dict["name"] == "test_beacon"
    assert state_dict["time"] == time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    assert state_dict["uptime"] == 60.0


@pytest.fixture
def setup_datastore():
    return ByteArray(size=17)


@patch("pysquared.nvm.flag.microcontroller")
@patch("pysquared.nvm.counter.microcontroller")
def test_beacon_send_with_sensors(
    mock_flag_microcontroller, mock_counter_microcontroller, mock_logger, mock_radio
):
    """Test sending a beacon with sensors."""
    mock_flag_microcontroller.nvm = (
        setup_datastore  # Mock the nvm module to use the ByteArray
    )
    mock_counter_microcontroller.nvm = (
        setup_datastore  # Mock the nvm module to use the ByteArray
    )

    beacon = Beacon(
        mock_logger,
        "test_beacon",
        mock_radio,
        0,
        Processor(),
        MockFlag(0, 0),
        MockCounter(0),
        MockRadio(),
        MockPowerMonitor(),
        MockTemperatureSensor(),
    )

    result = beacon.send()
    assert result is True

    state_dict = mock_radio.send.call_args[0][0]

    # processor sensor
    assert pytest.approx(state_dict["Processor_temperature"], 0.01) == 35.0

    # flag
    assert state_dict["test_flag"] is True

    # counter
    assert state_dict["test_counter"] == 42

    # radio
    assert state_dict["MockRadio_modulation"] == "LoRa"

    # power monitor sensor
    assert pytest.approx(state_dict["MockPowerMonitor_current_avg"], 0.01) == 0.5
    assert pytest.approx(state_dict["MockPowerMonitor_bus_voltage_avg"], 0.01) == 3.3
    assert pytest.approx(state_dict["MockPowerMonitor_shunt_voltage_avg"], 0.01) == 0.1

    # temperature sensor
    assert pytest.approx(state_dict["MockTemperatureSensor_temperature"], 0.01) == 22.5


def test_beacon_avg_readings(mock_logger, mock_radio):
    """Test the avg_readings method in the context of the Beacon class."""
    beacon = Beacon(mock_logger, "test_beacon", mock_radio, 0.0)

    # Test with a function that returns consistent values
    def constant_func():
        return 5.0

    result = beacon.avg_readings(constant_func, num_readings=5)
    assert pytest.approx(result, 0.01) == 5.0

    # Test with a function that returns None
    def none_func():
        return None

    result = beacon.avg_readings(none_func)
    assert result is None
    mock_logger.warning.assert_called_once()


def test_avg_readings_varying_values(mock_logger, mock_radio):
    """Test avg_readings with values that vary."""
    beacon = Beacon(mock_logger, "test_beacon", mock_radio, 0.0)

    # Create a simple counter function that returns incrementing values
    # Starting from 1 and incrementing by 1 each time
    values = list(range(1, 6))  # [1, 2, 3, 4, 5]
    expected_avg = sum(values) / len(values)  # (1+2+3+4+5)/5 = 15/5 = 3

    read_count = 0

    def incrementing_func():
        nonlocal read_count
        value = values[read_count % len(values)]
        read_count += 1
        return value

    # Test with a specific number of readings that's a multiple of our pattern length
    result = beacon.avg_readings(incrementing_func, num_readings=5)
    assert result == expected_avg
