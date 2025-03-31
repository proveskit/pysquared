import math
from unittest.mock import MagicMock, patch

import pytest

from mocks.adafruit_rfm.rfm9x import RFM9x
from mocks.adafruit_rfm.rfm9xfsk import RFM9xFSK
from mocks.circuitpython.byte_array import ByteArray
from pysquared.config.radio import RadioConfig
from pysquared.hardware.exception import HardwareInitializationError
from pysquared.hardware.radio.manager.rfm9x import RFM9xManager
from pysquared.hardware.radio.modulation import RadioModulation
from pysquared.logger import Logger
from pysquared.nvm.flag import Flag

# Type hinting only
try:
    from busio import SPI
    from digitalio import DigitalInOut
except ImportError:
    pass


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
def mock_use_fsk() -> Flag:
    return Flag(index=0, bit_index=0, datastore=ByteArray(size=8))


@pytest.fixture
def mock_radio_config() -> RadioConfig:
    return RadioConfig(
        {
            "license": "testlicense",
            "sender_id": 1,
            "receiver_id": 2,
            "transmit_frequency": 915,
            "start_time": 0,
            "fsk": {"broadcast_address": 255, "node_address": 1, "modulation_type": 0},
            "lora": {
                "ack_delay": 0.2,
                "coding_rate": 5,
                "cyclic_redundancy_check": True,
                "max_output": True,
                "spreading_factor": 7,
                "transmit_power": 23,
            },
        }
    )


@patch("pysquared.hardware.radio.manager.rfm9x.RFM9xFSK")
@patch("pysquared.hardware.radio.manager.rfm9x.RFM9x")
def test_init_fsk_success(
    mock_rfm9x: MagicMock,
    mock_rfm9xfsk: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: Flag,
):
    """Test successful initialization when use_fsk flag is True."""
    mock_use_fsk.toggle(True)
    mock_fsk_instance = MagicMock(spec=RFM9xFSK)
    mock_rfm9xfsk.return_value = mock_fsk_instance

    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
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
        "Initializing radio", radio_type="RFM9xManager", modulation=RadioModulation.FSK
    )


@patch("pysquared.hardware.radio.manager.rfm9x.RFM9xFSK")
@patch("pysquared.hardware.radio.manager.rfm9x.RFM9x")
def test_init_lora_success(
    mock_rfm9x: MagicMock,
    mock_rfm9xfsk: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: Flag,
):
    """Test successful initialization when use_fsk flag is False."""
    mock_use_fsk.toggle(False)
    mock_lora_instance = MagicMock(spec=RFM9x)
    mock_rfm9x.return_value = mock_lora_instance

    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
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
    assert mock_lora_instance.max_output == mock_radio_config.lora.max_output
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
        "Initializing radio", radio_type="RFM9xManager", modulation=RadioModulation.LORA
    )


@patch("pysquared.hardware.radio.manager.rfm9x.RFM9xFSK")
@patch("pysquared.hardware.radio.manager.rfm9x.RFM9x")
def test_init_lora_high_sf_success(
    mock_rfm9x: MagicMock,
    mock_rfm9xfsk: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,  # Use base config
    mock_use_fsk: Flag,
):
    """Test LoRa initialization with high spreading factor."""
    mock_use_fsk.toggle(False)
    # Modify config for high SF
    mock_radio_config.lora.spreading_factor = 10
    mock_lora_instance = MagicMock(spec=RFM9x)
    # Set SF on the mock instance *before* it's returned by the patch
    mock_lora_instance.spreading_factor = 10
    mock_rfm9x.return_value = mock_lora_instance

    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
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
@patch("pysquared.hardware.radio.manager.rfm9x.RFM9xFSK")
def test_init_with_retries_fsk(
    mock_rfm9xfsk: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: Flag,
):
    """Test __init__ retries on FSK initialization failure."""
    mock_use_fsk.toggle(True)
    mock_rfm9xfsk.side_effect = Exception("Simulated FSK failure")

    with pytest.raises(HardwareInitializationError):
        RFM9xManager(
            mock_logger,
            mock_radio_config,
            mock_use_fsk,
            mock_spi,
            mock_chip_select,
            mock_reset,
        )

    mock_logger.debug.assert_called_with(
        "Initializing radio", radio_type="RFM9xManager", modulation=RadioModulation.FSK
    )
    assert mock_rfm9xfsk.call_count == 3


@pytest.mark.slow
@patch("pysquared.hardware.radio.manager.rfm9x.RFM9x")
def test_init_with_retries_lora(
    mock_rfm9x: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: Flag,
):
    """Test __init__ retries on LoRa initialization failure."""
    mock_use_fsk.toggle(False)
    mock_rfm9x.side_effect = Exception("Simulated LoRa failure")

    with pytest.raises(HardwareInitializationError):
        RFM9xManager(
            mock_logger,
            mock_radio_config,
            mock_use_fsk,
            mock_spi,
            mock_chip_select,
            mock_reset,
        )

    mock_logger.debug.assert_called_with(
        "Initializing radio", radio_type="RFM9xManager", modulation=RadioModulation.LORA
    )
    assert mock_rfm9x.call_count == 3


# Test send Method
@patch("pysquared.hardware.radio.manager.rfm9x.RFM9x")  # Patch LoRa for simplicity
def test_send_success_bytes(
    mock_rfm9x: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: Flag,
):
    """Test successful sending of bytes."""
    mock_use_fsk.toggle(False)  # Use LoRa
    mock_radio_instance = MagicMock(spec=RFM9x)
    mock_radio_instance.send = MagicMock()
    mock_radio_instance.send.return_value = True  # Simulate successful send
    mock_rfm9x.return_value = mock_radio_instance

    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )

    data_bytes = b"Hello Radio"
    result = manager.send(data_bytes)

    assert result is True
    mock_radio_instance.send.assert_called_once_with(data_bytes)
    mock_logger.info.assert_called_once_with(
        "Radio message sent", success=True, len=len(data_bytes)
    )


@patch("pysquared.hardware.radio.manager.rfm9x.RFM9x")
def test_send_success_string(
    mock_rfm9x: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: Flag,
):
    """Test successful sending of a string (should be converted to bytes)."""
    mock_use_fsk.toggle(False)
    mock_radio_instance = MagicMock(spec=RFM9x)
    mock_radio_instance.send = MagicMock()
    mock_radio_instance.send.return_value = True
    mock_rfm9x.return_value = mock_radio_instance

    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )

    data_str = "Hello String"
    expected_bytes = bytes(data_str, "UTF-8")
    result = manager.send(data_str)

    assert result is True
    mock_radio_instance.send.assert_called_once_with(expected_bytes)
    mock_logger.info.assert_called_once_with(
        "Radio message sent", success=True, len=len(expected_bytes)
    )


@patch("pysquared.hardware.radio.manager.rfm9x.RFM9x")
def test_send_unlicensed(
    mock_rfm9x: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: Flag,
):
    """Test send attempt when not licensed."""
    mock_use_fsk.toggle(False)
    mock_radio_instance = MagicMock(spec=RFM9x)
    mock_radio_instance.send = MagicMock()
    mock_rfm9x.return_value = mock_radio_instance

    mock_radio_config.license = ""  # Simulate unlicensed state

    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
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


@patch("pysquared.hardware.radio.manager.rfm9x.RFM9x")
def test_send_exception(
    mock_rfm9x: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: Flag,
):
    """Test handling of exception during radio.send()."""
    mock_use_fsk.toggle(False)
    mock_radio_instance = MagicMock(spec=RFM9x)
    mock_radio_instance.send = MagicMock()
    send_error = RuntimeError("SPI Error")
    mock_radio_instance.send.side_effect = send_error
    mock_rfm9x.return_value = mock_radio_instance

    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )

    result = manager.send(b"test")

    assert result is False
    mock_logger.error.assert_called_once_with("Error sending radio message", send_error)


def test_set_modulation_lora_to_fsk(
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: Flag,
):
    """Test toggling the modulation flag."""
    # Start as LoRa
    mock_use_fsk.toggle(False)
    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )
    assert manager.get_modulation() == RadioModulation.LORA
    assert mock_use_fsk.get() is False

    # Request FSK
    manager.set_modulation(RadioModulation.FSK)
    assert mock_use_fsk.get() is True
    mock_logger.info.assert_called_with(
        "Radio modulation change requested for next init",
        requested=RadioModulation.FSK,
        current=RadioModulation.LORA,
    )


def test_set_modulation_fsk_to_lora(
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: Flag,
):
    """Test toggling the modulation flag."""
    # Start as FSK
    mock_use_fsk.toggle(True)
    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )
    assert manager.get_modulation() == RadioModulation.FSK
    assert mock_use_fsk.get() is True

    manager.set_modulation(RadioModulation.LORA)
    mock_logger.info.assert_called_with(
        "Radio modulation change requested for next init",
        requested=RadioModulation.LORA,
        current=RadioModulation.FSK,
    )


def test_get_modulation_initialized(
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: Flag,
):
    """Test get_modulation when radio is initialized."""
    # Test FSK instance
    mock_use_fsk.toggle(True)
    manager_fsk = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )
    assert manager_fsk.get_modulation() == RadioModulation.FSK

    # Test LoRa instance
    mock_use_fsk.toggle(False)
    manager_lora = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )
    assert manager_lora.get_modulation() == RadioModulation.LORA


def test_get_modulation_not_initialized(
    mock_use_fsk: Flag,
):
    """Test get_modulation when radio is not initialized (relies on flag)."""
    manager = RFM9xManager.__new__(
        RFM9xManager
    )  # Create instance without calling __init__
    manager._radio = None
    manager._use_fsk = mock_use_fsk

    # Flag is False (LoRa)
    mock_use_fsk.toggle(False)
    assert manager.get_modulation() == RadioModulation.LORA

    # Flag is True (FSK)
    mock_use_fsk.toggle(True)
    assert manager.get_modulation() == RadioModulation.FSK


# Test get_temperature Method
@pytest.mark.parametrize(
    "raw_value, expected_temperature",
    [
        (0b00011001, 168.0),  # Positive temp: 25 -> 25 + 143 = 168
        # (0b11100111, 118.0),  # Negative temp: 231 -> -25 -> -25 + 143 = 118
        (0x00, 143.0),  # Zero
        (0x7F, 270.0),  # Max positive (127)
        # (0x80, 15.0),         # Max negative (-128) -> -128 + 143 = 15
    ],
)
def test_get_temperature_success(
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: Flag,
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
        mock_use_fsk,
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
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: Flag,
):
    """Test handling exception during radio.read_u8()."""
    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
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


@patch("pysquared.hardware.radio.manager.rfm9x.RFM9x")  # Patch LoRa for simplicity
def test_receive_success(
    mock_rfm9x: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: Flag,
):
    """Test successful reception of a message."""
    mock_use_fsk.toggle(False)  # Use LoRa
    mock_radio_instance = MagicMock(spec=RFM9x)
    expected_data = b"Received Data"
    mock_radio_instance.receive = MagicMock()
    mock_radio_instance.receive.return_value = expected_data
    mock_rfm9x.return_value = mock_radio_instance

    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )

    received_data = manager.receive()

    assert received_data == expected_data
    mock_radio_instance.receive.assert_called_once_with(
        keep_listening=True, with_ack=True, timeout=10
    )
    mock_logger.error.assert_not_called()


@patch("pysquared.hardware.radio.manager.rfm9x.RFM9x")
def test_receive_no_message(
    mock_rfm9x: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: Flag,
):
    """Test receiving when no message is available (timeout)."""
    mock_use_fsk.toggle(False)
    mock_radio_instance = MagicMock(spec=RFM9x)
    mock_radio_instance.receive = MagicMock()
    mock_radio_instance.receive.return_value = None  # Simulate timeout
    mock_rfm9x.return_value = mock_radio_instance

    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )

    received_data = manager.receive()

    assert received_data is None
    mock_radio_instance.receive.assert_called_once_with(
        keep_listening=True, with_ack=True, timeout=10
    )
    mock_logger.error.assert_not_called()


@patch("pysquared.hardware.radio.manager.rfm9x.RFM9x")
def test_receive_exception(
    mock_rfm9x: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: Flag,
):
    """Test handling of exception during radio.receive()."""
    mock_use_fsk.toggle(False)
    mock_radio_instance = MagicMock(spec=RFM9x)
    mock_radio_instance.receive = MagicMock()
    receive_error = RuntimeError("Receive Error")
    mock_radio_instance.receive.side_effect = receive_error
    mock_rfm9x.return_value = mock_radio_instance

    manager = RFM9xManager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
        mock_spi,
        mock_chip_select,
        mock_reset,
    )

    received_data = manager.receive()

    assert received_data is None
    mock_radio_instance.receive.assert_called_once_with(
        keep_listening=True, with_ack=True, timeout=10
    )
    mock_logger.error.assert_called_once_with("Error receiving data", receive_error)
