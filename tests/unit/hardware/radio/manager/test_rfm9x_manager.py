import math
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from busio import SPI
from digitalio import DigitalInOut

from mocks.adafruit_rfm.rfm9x import RFM9x
from mocks.adafruit_rfm.rfm9xfsk import RFM9xFSK
from pysquared.config.radio import RadioConfig
from pysquared.hardware.exception import HardwareInitializationError
from pysquared.hardware.radio.manager.rfm9x import RFM9xManager
from pysquared.hardware.radio.modulation import FSK, LoRa
from pysquared.logger import Logger


@pytest.fixture
def mock_spi() -> MagicMock:
    return MagicMock(spec=SPI)


@pytest.fixture
def mock_chip_select() -> MagicMock:
    return MagicMock(spec=DigitalInOut)


@pytest.fixture
def mock_reset() -> MagicMock:
    return MagicMock(spec=DigitalInOut)


@pytest.fixture
def mock_logger() -> MagicMock:
    return MagicMock(spec=Logger)


@pytest.fixture
def mock_radio_config() -> RadioConfig:
    return RadioConfig(
        {
            "license": "testlicense",
            "modulation": "FSK",
            "sender_id": 1,
            "receiver_id": 2,
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
    with patch("pysquared.hardware.radio.manager.rfm9x.RFM9x") as mock_class:
        mock_class.return_value = RFM9x(mock_spi, mock_chip_select, mock_reset, 0)
        yield mock_class


@pytest.fixture
def mock_rfm9xfsk(
    mock_spi: MagicMock, mock_chip_select: MagicMock, mock_reset: MagicMock
) -> Generator[MagicMock, None, None]:
    with patch("pysquared.hardware.radio.manager.rfm9x.RFM9xFSK") as mock_class:
        mock_class.return_value = RFM9xFSK(mock_spi, mock_chip_select, mock_reset, 0)
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
    """Test successful initialization when radio_config.modulation == "FSK"."""
    mock_fsk_instance = MagicMock(spec=RFM9xFSK)
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
    assert mock_fsk_instance.node == mock_radio_config.sender_id
    assert mock_fsk_instance.destination == mock_radio_config.receiver_id
    assert (
        mock_fsk_instance.fsk_broadcast_address
        == mock_radio_config.fsk.broadcast_address
    )
    assert mock_fsk_instance.fsk_node_address == mock_radio_config.fsk.node_address
    assert mock_fsk_instance.modulation_type == mock_radio_config.fsk.modulation_type
    mock_logger.debug.assert_called_with(
        "Initializing radio", radio_type="RFM9xManager", modulation=FSK
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
    """Test successful initialization when radio_config.modulation == "LoRa"."""
    mock_radio_config.modulation = "LoRa"
    mock_lora_instance = MagicMock(spec=RFM9x)
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
    assert mock_lora_instance.node == mock_radio_config.sender_id
    assert mock_lora_instance.destination == mock_radio_config.receiver_id
    assert mock_lora_instance.ack_delay == mock_radio_config.lora.ack_delay
    assert (
        mock_lora_instance.enable_crc == mock_radio_config.lora.cyclic_redundancy_check
    )
    assert (
        mock_lora_instance.spreading_factor == mock_radio_config.lora.spreading_factor
    )
    assert mock_lora_instance.tx_power == mock_radio_config.lora.transmit_power
    # Check high SF optimization (default config SF is 7, so these shouldn't be set)
    assert (
        not hasattr(mock_lora_instance, "preamble_length")
        or mock_lora_instance.preamble_length is None
    )
    assert (
        not hasattr(mock_lora_instance, "low_datarate_optimize")
        or mock_lora_instance.low_datarate_optimize is None
    )
    mock_logger.debug.assert_called_with(
        "Initializing radio", radio_type="RFM9xManager", modulation=LoRa
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
    """Test LoRa initialization with high spreading factor."""
    mock_radio_config.modulation = "LoRa"
    # Modify config for high SF
    mock_radio_config.lora.spreading_factor = 10
    mock_lora_instance = MagicMock(spec=RFM9x)
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
    assert mock_lora_instance.low_datarate_optimize == 1


@pytest.mark.slow
def test_init_with_retries_fsk(
    mock_rfm9xfsk: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Test __init__ retries on FSK initialization failure."""
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
        "Initializing radio", radio_type="RFM9xManager", modulation=FSK
    )
    assert mock_rfm9xfsk.call_count == 3


@pytest.mark.slow
def test_init_with_retries_lora(
    mock_rfm9x: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Test __init__ retries on LoRa initialization failure."""
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
        "Initializing radio", radio_type="RFM9xManager", modulation=LoRa
    )
    assert mock_rfm9x.call_count == 3


# Test send Method
def test_send_success_bytes(
    mock_rfm9x: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Test successful sending of bytes."""
    mock_radio_config.modulation = "LoRa"
    mock_radio_instance = MagicMock(spec=RFM9x)
    mock_radio_instance.send = MagicMock()
    mock_radio_instance.send.return_value = True  # Simulate successful send
    mock_rfm9x.return_value = mock_radio_instance

    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )

    msg = b"Hello Radio"
    result = manager.send(msg)

    license_bytes: bytes = bytes(mock_radio_config.license, "UTF-8")
    expected_msg: bytes = b" ".join([license_bytes, msg, license_bytes])

    assert result is True
    mock_radio_instance.send.assert_called_once_with(expected_msg)
    mock_logger.info.assert_called_once_with("Radio message sent")


def test_send_success_string(
    mock_rfm9x: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Test successful sending of a string (should be converted to bytes)."""
    mock_radio_config.modulation = "LoRa"
    mock_radio_instance = MagicMock(spec=RFM9x)
    mock_radio_instance.send = MagicMock()
    mock_radio_instance.send.return_value = True
    mock_rfm9x.return_value = mock_radio_instance

    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )

    data_str = "Hello String"
    expected_bytes: bytes = b" ".join(
        [
            bytes(mock_radio_config.license, "UTF-8"),
            bytes(data_str, "UTF-8"),
            bytes(mock_radio_config.license, "UTF-8"),
        ]
    )

    result = manager.send(data_str)

    assert result is True
    mock_radio_instance.send.assert_called_once_with(expected_bytes)
    mock_logger.info.assert_called_once_with("Radio message sent")


def test_send_unexpected_type(
    mock_rfm9x: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Test successful sending of a string (should be converted to bytes)."""
    mock_radio_config.modulation = "LoRa"
    mock_radio_instance = MagicMock(spec=RFM9x)
    mock_radio_instance.send = MagicMock()
    mock_radio_instance.send.return_value = True
    mock_rfm9x.return_value = mock_radio_instance

    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )

    result = manager.send(manager)
    assert result is True

    mock_radio_instance.send.assert_called_once_with(
        bytes(f"testlicense {manager} testlicense", "UTF-8")
    )
    mock_logger.warning.assert_called_once_with(
        "Attempting to send non-bytes/str data type: <class 'pysquared.hardware.radio.manager.rfm9x.RFM9xManager'>",
    )


def test_send_unlicensed(
    mock_rfm9x: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Test send attempt when not licensed."""
    mock_radio_config.modulation = "LoRa"
    mock_radio_instance = MagicMock(spec=RFM9x)
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
    """Test handling of exception during radio.send()."""
    mock_radio_config.modulation = "LoRa"
    mock_radio_instance = MagicMock(spec=RFM9x)
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
    """Test get_modulation when radio is initialized."""
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


# Test get_temperature Method
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
    """Test successful temperature reading and calculation."""
    mock_radio_instance = MagicMock(spec=RFM9x)
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

    assert isinstance(temp, float)
    assert math.isclose(temp, expected_temperature, rel_tol=1e-9)
    mock_radio_instance.read_u8.assert_called_once_with(0x5B)
    mock_logger.debug.assert_called_with("Radio temperature read", temp=temp)


def test_get_temperature_read_exception(
    mock_rfm9x: MagicMock,
    mock_rfm9xfsk: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Test handling exception during radio.read_u8()."""
    mock_radio_config.modulation = "LoRa"
    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )
    mock_radio_instance = MagicMock(spec=RFM9x)
    manager._radio = mock_radio_instance

    read_error = RuntimeError("Read failed")
    mock_radio_instance.read_u8 = MagicMock()
    mock_radio_instance.read_u8.side_effect = read_error

    temp = manager.get_temperature()

    assert math.isnan(temp)
    mock_logger.error.assert_called_once_with(
        "Error reading radio temperature", read_error
    )


def test_receive_success(
    mock_rfm9x: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Test successful reception of a message."""
    mock_radio_config.modulation = "LoRa"
    mock_radio_instance = MagicMock(spec=RFM9x)
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
    """Test receiving when no message is available (timeout)."""
    mock_radio_config.modulation = "LoRa"
    mock_radio_instance = MagicMock(spec=RFM9x)
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
    """Test handling of exception during radio.receive()."""
    mock_radio_config.modulation = "LoRa"
    mock_radio_instance = MagicMock(spec=RFM9x)
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
    mock_rfm9x: MagicMock,
    mock_rfm9xfsk: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Test modifying the radio configuration."""
    mock_radio_config.modulation = "LoRa"

    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )
    # Verify the radio was initialized with the correct node address
    assert manager._radio.node == mock_radio_config.sender_id
    assert manager._radio.ack_delay == mock_radio_config.lora.ack_delay

    # Create a new config with modified node address
    new_config = mock_radio_config
    new_config.sender_id = 255

    # Modify the config
    manager.modify_config("sender_id", new_config.sender_id)

    # Verify the radio was modified with the new config
    assert manager._radio.node == new_config.sender_id
    assert manager._radio.ack_delay == new_config.lora.ack_delay

    mock_logger.debug.assert_any_call(
        "Initializing radio", radio_type="RFM9xManager", modulation=LoRa
    )


def test_modify_fsk_config(
    mock_rfm9x: MagicMock,
    mock_rfm9xfsk: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Test modifying the radio configuration."""

    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )
    # Verify the radio was initialized with the correct node address
    assert manager._radio.node == mock_radio_config.sender_id
    assert (
        manager._radio.fsk_broadcast_address == mock_radio_config.fsk.broadcast_address  # type: ignore
    )

    # Modify the config
    manager.modify_config("fsk_broadcast_address", 123)

    # Verify the radio was modified with the new config
    assert manager._radio.node == mock_radio_config.sender_id
    assert manager._radio.fsk_broadcast_address == 123  # type: ignore

    mock_logger.debug.assert_any_call(
        "Initializing radio", radio_type="RFM9xManager", modulation=FSK
    )
