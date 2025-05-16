import time
from unittest.mock import MagicMock, patch

import pytest
from freezegun import freeze_time

from pysquared.beacon import Beacon
from pysquared.hardware.radio.modulation import LoRa
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


@pytest.fixture
def mock_power_monitor() -> MagicMock:
    power_monitor = MagicMock(spec=PowerMonitorProto)
    power_monitor.get_current.return_value = 0.5
    power_monitor.get_bus_voltage.return_value = 3.3
    power_monitor.get_shunt_voltage.return_value = 0.1
    power_monitor.__class__.__name__ = "MockPowerMonitor"
    return power_monitor


@pytest.fixture
def mock_temperature_sensor() -> MagicMock:
    temp_sensor = MagicMock(spec=TemperatureSensorProto)
    temp_sensor.get_temperature.return_value = 25.5
    temp_sensor.__class__.__name__ = "MockTemperatureSensor"
    return temp_sensor


@pytest.fixture
def mock_flag() -> MagicMock:
    flag = MagicMock(spec=Flag)
    flag.get_name.return_value = "test_flag"
    flag.get.return_value = True
    return flag


@pytest.fixture
def mock_counter() -> MagicMock:
    counter = MagicMock(spec=Counter)
    counter.get_name.return_value = "test_counter"
    counter.get.return_value = 42
    return counter


# @pytest.fixture
# def mock_time_localtime() -> Generator[MagicMock, None, None]:
#     with patch("time.localtime") as mock_time:
#         mock_time = MagicMock()
#         mock_time.tm_year = 2025
#         mock_time.tm_mon = 5
#         mock_time.tm_mday = 16
#         mock_time.tm_hour = 12
#         mock_time.tm_min = 34
#         mock_time.tm_sec = 56
#         yield mock_time


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
    """Test sending a basic beacon with minimal sensors."""
    boot_time = 1000.0
    mock_time.return_value = 1060.0  # 60 seconds after boot

    beacon = Beacon(mock_logger, "test_beacon", mock_radio, boot_time)
    result = beacon.send()

    assert result is True
    mock_radio.send.assert_called_once()
    state_dict = mock_radio.send.call_args[0][0]
    assert state_dict["name"] == "test_beacon"
    assert state_dict["time"] == "2025-05-16 12:34:56"
    assert state_dict["uptime"] == 60.0
