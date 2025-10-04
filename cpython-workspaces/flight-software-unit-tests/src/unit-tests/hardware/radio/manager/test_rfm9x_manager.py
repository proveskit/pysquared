"""Unit tests for the RFM9xManager class.

This module contains unit tests for the `RFM9xManager` class, which manages
RFM9x radios. The tests cover initialization, sending and receiving data,
modifying radio configuration, and retrieving radio parameters like temperature
and RSSI.
"""

import math
import sys
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from busio import SPI
from digitalio import DigitalInOut
from mocks.adafruit_rfm.rfm9x import RFM9x as MockRFM9x
from mocks.adafruit_rfm.rfm9xfsk import RFM9xFSK as MockRFM9xFSK
from pysquared.config.radio import RadioConfig
from pysquared.hardware.exception import HardwareInitializationError
from pysquared.hardware.radio.modulation import FSK, LoRa
from pysquared.logger import Logger
from pysquared.sensor_reading.error import SensorReadingUnknownError
from pysquared.sensor_reading.temperature import Temperature

rfm9x = MagicMock()
rfm9x.RFM9x = MockRFM9x
rfm9xfsk = MagicMock()
rfm9xfsk.RFM9xFSK = MockRFM9xFSK
sys.modules["adafruit_rfm.rfm9x"] = rfm9x
sys.modules["adafruit_rfm.rfm9xfsk"] = rfm9xfsk

from pysquared.hardware.radio.manager.rfm9x import RFM9xManager  # noqa: E402


@pytest.fixture
def mock_spi() -> MagicMock:
    """Mocks the SPI bus."""
    return MagicMock(spec=SPI)


@pytest.fixture
def mock_chip_select() -> MagicMock:
    """Mocks the chip select DigitalInOut pin."""
    return MagicMock(spec=DigitalInOut)


@pytest.fixture
def mock_reset() -> MagicMock:
    """Mocks the reset DigitalInOut pin."""
    return MagicMock(spec=DigitalInOut)


@pytest.fixture
def mock_logger() -> MagicMock:
    """Mocks the Logger class."""
    return MagicMock(spec=Logger)


@pytest.fixture
def mock_radio_config() -> RadioConfig:
    """Provides a mock RadioConfig instance with default values."""
    return RadioConfig(
        {
            "license": "testlicense",
            "modulation": "FSK",
            "transmit_frequency": 915,
            "start_time": 0,
            "fsk": {"broadcast_address": 255, "node_address": 1, "modulation_type": 0},
            "lora": {
                "ack_delay": 0.2,
                "coding_rate": 5,
                "cyclic_redundancy_check": True,
                "spreading_factor": 7,
                "transmit_power": 23,
            },
        }
    )


@pytest.fixture
def mock_rfm9x(
    mock_spi: MagicMock, mock_chip_select: MagicMock, mock_reset: MagicMock
) -> Generator[MagicMock, None, None]:
    """Mocks the RFM9x class.

    Args:
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.

    Yields:
        A MagicMock instance of RFM9x.
    """
    with patch("pysquared.hardware.radio.manager.rfm9x.RFM9x") as mock_class:
        mock_class.return_value = MockRFM9x(mock_spi, mock_chip_select, mock_reset, 0)
        yield mock_class


@pytest.fixture
def mock_rfm9xfsk(
    mock_spi: MagicMock, mock_chip_select: MagicMock, mock_reset: MagicMock
) -> Generator[MagicMock, None, None]:
    """Mocks the RFM9xFSK class.

    Args:
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.

    Yields:
        A MagicMock instance of RFM9xFSK.
    """
    with patch("pysquared.hardware.radio.manager.rfm9x.RFM9xFSK") as mock_class:
        mock_class.return_value = MockRFM9xFSK(
            mock_spi, mock_chip_select, mock_reset, 0
        )
        yield mock_class


def test_init_fsk_success(
    mock_rfm9x: MagicMock,
    mock_rfm9xfsk: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Tests successful initialization when radio_config.modulation is FSK.

    Args:
        mock_rfm9x: Mocked RFM9x class.
        mock_rfm9xfsk: Mocked RFM9xFSK class.
        mock_logger: Mocked Logger instance.
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.
        mock_radio_config: Mocked RadioConfig instance.
    """
    mock_fsk_instance = MagicMock()
    mock_rfm9xfsk.return_value = mock_fsk_instance

    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )

    mock_rfm9xfsk.assert_called_once_with(
        mock_spi,
        mock_chip_select,
        mock_reset,
        mock_radio_config.transmit_frequency,
    )
    mock_rfm9x.assert_not_called()
    assert manager._radio == mock_fsk_instance
    assert (
        mock_fsk_instance.fsk_broadcast_address
        == mock_radio_config.fsk.broadcast_address
    )
    assert mock_fsk_instance.fsk_node_address == mock_radio_config.fsk.node_address
    assert mock_fsk_instance.modulation_type == mock_radio_config.fsk.modulation_type
    mock_logger.debug.assert_called_with(
        "Initializing radio", radio_type="RFM9xManager", modulation=FSK.__name__
    )


def test_init_lora_success(
    mock_rfm9x: MagicMock,
    mock_rfm9xfsk: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Tests successful initialization when radio_config.modulation is LoRa.

    Args:
        mock_rfm9x: Mocked RFM9x class.
        mock_rfm9xfsk: Mocked RFM9xFSK class.
        mock_logger: Mocked Logger instance.
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.
        mock_radio_config: Mocked RadioConfig instance.
    """
    mock_radio_config.modulation = "LoRa"
    mock_lora_instance = MagicMock()
    mock_rfm9x.return_value = mock_lora_instance

    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )

    mock_rfm9x.assert_called_once_with(
        mock_spi,
        mock_chip_select,
        mock_reset,
        mock_radio_config.transmit_frequency,
    )
    mock_rfm9xfsk.assert_not_called()
    assert manager._radio == mock_lora_instance
    assert mock_lora_instance.ack_delay == mock_radio_config.lora.ack_delay
    assert (
        mock_lora_instance.enable_crc == mock_radio_config.lora.cyclic_redundancy_check
    )
    assert (
        mock_lora_instance.spreading_factor == mock_radio_config.lora.spreading_factor
    )
    assert mock_lora_instance.tx_power == mock_radio_config.lora.transmit_power
    # Check high SF optimization (default config SF is 7, so preamble_length shouldn't be set to SF)
    # For SF <= 9, preamble_length should be 8 (default), not equal to SF
    assert (
        not hasattr(mock_lora_instance, "preamble_length")
        or mock_lora_instance.preamble_length != mock_radio_config.lora.spreading_factor
    )
    mock_logger.debug.assert_called_with(
        "Initializing radio", radio_type="RFM9xManager", modulation=LoRa.__name__
    )


def test_init_lora_high_sf_success(
    mock_rfm9x: MagicMock,
    mock_rfm9xfsk: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,  # Use base config
):
    """Tests LoRa initialization with high spreading factor.

    Args:
        mock_rfm9x: Mocked RFM9x class.
        mock_rfm9xfsk: Mocked RFM9xFSK class.
        mock_logger: Mocked Logger instance.
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.
        mock_radio_config: Mocked RadioConfig instance.
    """
    mock_radio_config.modulation = "LoRa"
    # Modify config for high SF
    mock_radio_config.lora.spreading_factor = 10
    mock_lora_instance = MagicMock()
    # Set SF on the mock instance *before* it's returned by the patch
    mock_lora_instance.spreading_factor = 10
    mock_rfm9x.return_value = mock_lora_instance

    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )

    mock_rfm9x.assert_called_once()
    assert manager._radio == mock_lora_instance
    # Check high SF optimization IS set
    assert mock_lora_instance.preamble_length == 10


def test_init_failed_fsk(
    mock_rfm9xfsk: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Tests __init__ retries on FSK initialization failure.

    Args:
        mock_rfm9xfsk: Mocked RFM9xFSK class.
        mock_logger: Mocked Logger instance.
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.
        mock_radio_config: Mocked RadioConfig instance.
    """
    mock_rfm9xfsk.side_effect = Exception("Simulated FSK failure")

    with pytest.raises(HardwareInitializationError):
        RFM9xManager(
            mock_logger,
            mock_radio_config,
            mock_spi,
            mock_chip_select,
            mock_reset,
        )

    mock_logger.debug.assert_called_with(
        "Initializing radio", radio_type="RFM9xManager", modulation=FSK.__name__
    )
    mock_rfm9xfsk.assert_called_once()


def test_init_failed_lora(
    mock_rfm9x: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Tests __init__ retries on LoRa initialization failure.

    Args:
        mock_rfm9x: Mocked RFM9x class.
        mock_logger: Mocked Logger instance.
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.
        mock_radio_config: Mocked RadioConfig instance.
    """
    mock_radio_config.modulation = "LoRa"
    mock_rfm9x.side_effect = Exception("Simulated LoRa failure")

    with pytest.raises(HardwareInitializationError):
        RFM9xManager(
            mock_logger,
            mock_radio_config,
            mock_spi,
            mock_chip_select,
            mock_reset,
        )

    mock_logger.debug.assert_called_with(
        "Initializing radio", radio_type="RFM9xManager", modulation=LoRa.__name__
    )
    mock_rfm9x.assert_called_once()


def test_send_success_bytes(
    mock_rfm9x: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Tests successful sending of bytes.

    Args:
        mock_rfm9x: Mocked RFM9x class.
        mock_logger: Mocked Logger instance.
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.
        mock_radio_config: Mocked RadioConfig instance.
    """
    mock_radio_config.modulation = "LoRa"
    mock_radio_instance = MagicMock()
    mock_radio_instance.send = MagicMock()
    mock_rfm9x.return_value = mock_radio_instance

    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )

    msg = b"Hello Radio"
    _ = manager.send(msg)

    mock_radio_instance.send.assert_called_once_with(msg)


def test_send_unlicensed(
    mock_rfm9x: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Tests send attempt when not licensed.

    Args:
        mock_rfm9x: Mocked RFM9x class.
        mock_logger: Mocked Logger instance.
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.
        mock_radio_config: Mocked RadioConfig instance.
    """
    mock_radio_config.modulation = "LoRa"
    mock_radio_instance = MagicMock()
    mock_radio_instance.send = MagicMock()
    mock_rfm9x.return_value = mock_radio_instance

    mock_radio_config.license = ""  # Simulate unlicensed state

    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )

    result = manager.send(b"test")

    assert result is False
    mock_radio_instance.send.assert_not_called()
    mock_logger.warning.assert_called_once_with(
        "Radio send attempt failed: Not licensed."
    )


def test_send_exception(
    mock_rfm9x: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Tests handling of exception during radio.send().

    Args:
        mock_rfm9x: Mocked RFM9x class.
        mock_logger: Mocked Logger instance.
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.
        mock_radio_config: Mocked RadioConfig instance.
    """
    mock_radio_config.modulation = "LoRa"
    mock_radio_instance = MagicMock()
    mock_radio_instance.send = MagicMock()
    send_error = RuntimeError("SPI Error")
    mock_radio_instance.send.side_effect = send_error
    mock_rfm9x.return_value = mock_radio_instance

    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )

    result = manager.send(b"test")

    assert result is False
    mock_logger.error.assert_called_once_with("Error sending radio message", send_error)


def test_get_modulation_initialized(
    mock_rfm9x: MagicMock,
    mock_rfm9xfsk: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Tests get_modulation when radio is initialized.

    Args:
        mock_rfm9x: Mocked RFM9x class.
        mock_rfm9xfsk: Mocked RFM9xFSK class.
        mock_logger: Mocked Logger instance.
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.
        mock_radio_config: Mocked RadioConfig instance.
    """
    # Test FSK instance
    manager_fsk = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )
    assert manager_fsk.get_modulation() == FSK

    # Test LoRa instance
    mock_radio_config.modulation = "LoRa"
    manager_lora = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )
    assert manager_lora.get_modulation() == LoRa


@pytest.mark.parametrize(
    "raw_value, expected_temperature",
    [
        (0b00011001, 168.0),  # Positive temp: 25 -> 25 + 143 = 168
        (0b11100111, 118.0),  # Negative temp: 231 -> -25 -> -25 + 143 = 118
        (0x00, 143.0),  # Zero
        (0x7F, 270.0),  # Max positive (127)
        (0x80, 15.0),  # Max negative (-128) -> -128 + 143 = 15
    ],
)
def test_get_temperature_success(
    mock_rfm9x: MagicMock,
    mock_rfm9xfsk: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
    raw_value: int,
    expected_temperature: float,
):
    """Tests successful temperature reading and calculation.

    Args:
        mock_rfm9x: Mocked RFM9x class.
        mock_rfm9xfsk: Mocked RFM9xFSK class.
        mock_logger: Mocked Logger instance.
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.
        mock_radio_config: Mocked RadioConfig instance.
        raw_value: Raw temperature value from the radio.
        expected_temperature: Expected calculated temperature.
    """
    mock_radio_instance = MagicMock()
    mock_radio_instance.read_u8 = MagicMock()
    mock_radio_instance.read_u8.return_value = raw_value

    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )
    manager._radio = mock_radio_instance

    temp = manager.get_temperature()

    assert isinstance(temp, Temperature)
    assert math.isclose(temp.value, expected_temperature, rel_tol=1e-9)
    mock_radio_instance.read_u8.assert_called_once_with(0x5B)
    mock_logger.debug.assert_called_with("Radio temperature read", temp=temp.value)


def test_get_temperature_read_exception(
    mock_rfm9x: MagicMock,
    mock_rfm9xfsk: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Tests handling exception during radio.read_u8().

    Args:
        mock_rfm9x: Mocked RFM9x class.
        mock_rfm9xfsk: Mocked RFM9xFSK class.
        mock_logger: Mocked Logger instance.
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.
        mock_radio_config: Mocked RadioConfig instance.
    """
    mock_radio_config.modulation = "LoRa"
    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )
    mock_radio_instance = MagicMock()
    manager._radio = mock_radio_instance

    read_error = RuntimeError("Read failed")
    mock_radio_instance.read_u8 = MagicMock()
    mock_radio_instance.read_u8.side_effect = read_error

    with pytest.raises(SensorReadingUnknownError):
        manager.get_temperature()


def test_receive_success(
    mock_rfm9x: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Tests successful reception of a message.

    Args:
        mock_rfm9x: Mocked RFM9x class.
        mock_logger: Mocked Logger instance.
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.
        mock_radio_config: Mocked RadioConfig instance.
    """
    mock_radio_config.modulation = "LoRa"
    mock_radio_instance = MagicMock()
    expected_data = b"Received Data"
    mock_radio_instance.receive = MagicMock()
    mock_radio_instance.receive.return_value = expected_data
    mock_rfm9x.return_value = mock_radio_instance

    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )

    received_data = manager.receive(timeout=10)

    assert received_data == expected_data
    mock_radio_instance.receive.assert_called_once_with(keep_listening=True, timeout=10)
    mock_logger.error.assert_not_called()


def test_receive_no_message(
    mock_rfm9x: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Tests receiving when no message is available (timeout).

    Args:
        mock_rfm9x: Mocked RFM9x class.
        mock_logger: Mocked Logger instance.
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.
        mock_radio_config: Mocked RadioConfig instance.
    """
    mock_radio_config.modulation = "LoRa"
    mock_radio_instance = MagicMock()
    mock_radio_instance.receive = MagicMock()
    mock_radio_instance.receive.return_value = None  # Simulate timeout
    mock_rfm9x.return_value = mock_radio_instance

    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )

    received_data = manager.receive(timeout=10)

    assert received_data is None
    mock_radio_instance.receive.assert_called_once_with(keep_listening=True, timeout=10)
    mock_logger.debug.assert_called_with("No message received")
    mock_logger.error.assert_not_called()


def test_receive_exception(
    mock_rfm9x: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Tests handling of exception during radio.receive().

    Args:
        mock_rfm9x: Mocked RFM9x class.
        mock_logger: Mocked Logger instance.
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.
        mock_radio_config: Mocked RadioConfig instance.
    """
    mock_radio_config.modulation = "LoRa"
    mock_radio_instance = MagicMock()
    mock_radio_instance.receive = MagicMock()
    receive_error = RuntimeError("Receive Error")
    mock_radio_instance.receive.side_effect = receive_error
    mock_rfm9x.return_value = mock_radio_instance

    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )

    received_data = manager.receive(timeout=10)

    assert received_data is None
    mock_radio_instance.receive.assert_called_once_with(keep_listening=True, timeout=10)
    mock_logger.error.assert_called_once_with("Error receiving data", receive_error)


def test_modify_lora_config(
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Tests modifying the radio configuration for LoRa mode.

    Args:
        mock_logger: Mocked Logger instance.
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.
        mock_radio_config: Mocked RadioConfig instance.
    """
    # Create manager without initializing the radio
    manager = RFM9xManager.__new__(RFM9xManager)
    manager._log = mock_logger
    manager._radio_config = mock_radio_config

    # Initialize the radio manually with LoRa mock
    lora_mock = MockRFM9x(mock_spi, mock_chip_select, mock_reset, 915)
    lora_mock.ack_delay = mock_radio_config.lora.ack_delay
    manager._radio = lora_mock  # type: ignore

    # Modify the config
    manager.modify_config("spreading_factor", 7)
    manager.modify_config("ack_delay", 0.5)
    manager.modify_config("cyclic_redundancy_check", False)
    manager.modify_config("transmit_power", 20)

    # Verify the radio was modified with the new config
    assert manager._radio.spreading_factor == 7  # type: ignore
    assert manager._radio.ack_delay == pytest.approx(0.5, rel=1e-9)  # type: ignore
    # Check that preamble_length is set to 8 (default for LoRa)
    assert manager._radio.preamble_length == 8  # type: ignore
    assert manager._radio.enable_crc is False  # type: ignore
    assert manager._radio.tx_power == 20  # type: ignore

    # modify an unknown config key
    with pytest.raises(KeyError):
        manager.modify_config("unknown_key", "value")


def test_modify_lora_config_high_sf_success(
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,  # Use base config
):
    """Tests LoRa initialization with high spreading factor.

    Args:
        mock_logger: Mocked Logger instance.
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.
        mock_radio_config: Mocked RadioConfig instance.
    """
    # Create manager without initializing the radio
    manager = RFM9xManager.__new__(RFM9xManager)
    manager._log = mock_logger
    manager._radio_config = mock_radio_config

    # Initialize the radio manually with LoRa mock
    lora_mock = MockRFM9x(mock_spi, mock_chip_select, mock_reset, 915)
    lora_mock.ack_delay = mock_radio_config.lora.ack_delay
    lora_mock.spreading_factor = mock_radio_config.lora.spreading_factor
    manager._radio = lora_mock  # type: ignore

    # Modify the config
    manager.modify_config("spreading_factor", 10)

    # Verify the radio was modified with the new config
    assert manager._radio.ack_delay == pytest.approx(  # type: ignore
        mock_radio_config.lora.ack_delay, rel=1e-9
    )
    assert manager._radio.spreading_factor == 10  # type: ignore
    assert manager._radio.preamble_length == 10  # type: ignore


def test_modify_fsk_config(
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Tests modifying the radio configuration for FSK mode.

    Args:
        mock_logger: Mocked Logger instance.
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.
        mock_radio_config: Mocked RadioConfig instance.
    """
    # Create manager without initializing the radio
    manager = RFM9xManager.__new__(RFM9xManager)
    manager._log = mock_logger
    manager._radio_config = mock_radio_config

    # Initialize the radio manually with FSK mock
    fsk_mock = MockRFM9xFSK(mock_spi, mock_chip_select, mock_reset, 915)
    fsk_mock.fsk_broadcast_address = mock_radio_config.fsk.broadcast_address
    manager._radio = fsk_mock  # type: ignore

    # Modify the config
    manager.modify_config("broadcast_address", 123)
    manager.modify_config("node_address", 222)
    manager.modify_config("modulation_type", 1)

    # Verify the radio was modified with the new config
    assert manager._radio.fsk_broadcast_address == 123  # type: ignore
    assert manager._radio.fsk_node_address == 222  # type: ignore
    assert manager._radio.modulation_type == 1  # type: ignore

    # modify an unknown config key
    with pytest.raises(KeyError):
        manager.modify_config("unknown_key", "value")


def test_get_max_packet_size_lora(
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Tests get_max_packet_size method with LoRa radio.

    Args:
        mock_logger: Mocked Logger instance.
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.
        mock_radio_config: Mocked RadioConfig instance.
    """
    # Create manager without initializing the radio
    manager = RFM9xManager.__new__(RFM9xManager)
    manager._log = mock_logger
    manager._radio_config = mock_radio_config

    # Initialize the radio manually with LoRa mock
    lora_mock = MockRFM9x(mock_spi, mock_chip_select, mock_reset, 915)
    lora_mock.max_packet_length = 252
    manager._radio = lora_mock  # type: ignore

    # Check that get_max_packet_size returns the radio's max_packet_length
    assert manager.get_max_packet_size() == 252


def test_get_max_packet_size_fsk(
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Tests get_max_packet_size method with FSK radio.

    Args:
        mock_logger: Mocked Logger instance.
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.
        mock_radio_config: Mocked RadioConfig instance.
    """
    # Create manager without initializing the radio
    manager = RFM9xManager.__new__(RFM9xManager)
    manager._log = mock_logger
    manager._radio_config = mock_radio_config

    # Initialize the radio manually with FSK mock
    fsk_mock = MockRFM9xFSK(mock_spi, mock_chip_select, mock_reset, 915)
    fsk_mock.max_packet_length = 252
    manager._radio = fsk_mock  # type: ignore

    # Check that get_max_packet_size returns the radio's max_packet_length
    assert manager.get_max_packet_size() == 252


def test_get_rssi(
    mock_rfm9x: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Tests getting the RSSI value from the radio.

    Args:
        mock_rfm9x: Mocked RFM9x class.
        mock_logger: Mocked Logger instance.
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.
        mock_radio_config: Mocked RadioConfig instance.
    """
    mock_radio_config.modulation = "LoRa"
    mock_radio_instance = MagicMock()
    expected_rssi = 70.0
    mock_radio_instance.last_rssi = expected_rssi
    mock_rfm9x.return_value = mock_radio_instance

    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )

    rssi_value = manager.get_rssi()

    assert rssi_value == expected_rssi


def test_send_oversized_packet_truncates(
    mock_rfm9x: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Tests that oversized packets are truncated and a warning is logged.

    Args:
        mock_rfm9x: Mocked RFM9x class.
        mock_logger: Mocked Logger instance.
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.
        mock_radio_config: Mocked RadioConfig instance.
    """
    mock_radio_config.modulation = "LoRa"
    mock_radio_instance = MagicMock()
    mock_radio_instance.max_packet_length = 252  # RFM9x max packet length
    mock_radio_instance.send = MagicMock(return_value=True)
    mock_rfm9x.return_value = mock_radio_instance

    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )

    # Create oversized data (253 bytes, which is 1 byte over the limit)
    oversized_data = b"x" * 253

    # Send the oversized data
    result = manager.send(oversized_data)

    # Verify that send was successful
    assert result is True

    # Verify that a warning was logged about truncation
    mock_logger.warning.assert_called()
    warning_calls = [call for call in mock_logger.warning.call_args_list]
    truncation_warning = None
    for call in warning_calls:
        if call[0][0] == "Data exceeds max packet size, truncating":
            truncation_warning = call
            break

    assert truncation_warning is not None
    assert truncation_warning[1]["data_length"] == 253
    assert truncation_warning[1]["max_packet_size"] == 252

    # Verify that the data sent to the radio was truncated to 252 bytes
    mock_radio_instance.send.assert_called_once()
    sent_data = mock_radio_instance.send.call_args[0][0]
    assert len(sent_data) == 252
