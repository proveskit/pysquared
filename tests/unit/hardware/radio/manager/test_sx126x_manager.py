from unittest.mock import MagicMock, patch

import pytest

from mocks.circuitpython.byte_array import ByteArray

# Import the mock directly
from mocks.proves_sx126.sx126x import ERR_NONE
from mocks.proves_sx126.sx1262 import SX1262
from pysquared.config.radio import RadioConfig
from pysquared.hardware.exception import HardwareInitializationError
from pysquared.hardware.radio.manager.sx126x import SX126xManager
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
def mock_irq() -> MagicMock:
    return MagicMock(spec=DigitalInOut)


@pytest.fixture
def mock_gpio() -> MagicMock:
    return MagicMock(spec=DigitalInOut)


@pytest.fixture
def mock_logger() -> MagicMock:
    return MagicMock(spec=Logger)


@pytest.fixture
def mock_use_fsk() -> Flag:
    return Flag(index=0, bit_index=0, datastore=ByteArray(size=8))


@pytest.fixture
def mock_radio_config() -> RadioConfig:
    # Using the same config as RFM9x for consistency, adjust if needed
    return RadioConfig(
        {
            "license": "test license",
            "sender_id": 1,  # Not directly used by SX126xManager init
            "receiver_id": 2,  # Not directly used by SX126xManager init
            "transmit_frequency": 915.0,  # Needs to be float for SX126x
            "start_time": 0,
            "fsk": {
                "broadcast_address": 255,
                "node_address": 1,
                "modulation_type": 0,
            },  # node/mod_type not used by SX126x
            "lora": {
                "ack_delay": 0.2,  # Not used by SX126x
                "coding_rate": 5,
                "cyclic_redundancy_check": True,
                "max_output": True,  # Not used by SX126x
                "spreading_factor": 7,
                "transmit_power": 14,  # Default power for SX126x begin()
            },
        }
    )


@patch(
    "pysquared.hardware.radio.manager.sx126x.SX1262",
    new_callable=MagicMock(spec=SX1262),
)
def test_init_fsk_success(
    mock_sx1262: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_irq: MagicMock,
    mock_gpio: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: Flag,
):
    """Test successful initialization when use_fsk flag is True."""
    mock_use_fsk.toggle(True)
    mock_sx1262_instance = mock_sx1262.return_value

    manager = SX126xManager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
        mock_spi,
        mock_chip_select,
        mock_irq,
        mock_reset,
        mock_gpio,
    )

    mock_sx1262.assert_called_once_with(
        mock_spi, mock_chip_select, mock_irq, mock_reset, mock_gpio
    )
    mock_sx1262_instance.beginFSK.assert_called_once_with(
        freq=mock_radio_config.transmit_frequency,
        addr=mock_radio_config.fsk.broadcast_address,
    )
    mock_sx1262_instance.begin.assert_not_called()
    assert manager._radio == mock_sx1262_instance
    mock_logger.debug.assert_any_call(
        "Initializing radio", radio_type="SX126xManager", modulation=RadioModulation.FSK
    )


@patch(
    "pysquared.hardware.radio.manager.sx126x.SX1262",
    new_callable=MagicMock(spec=SX1262),
)
def test_init_lora_success(
    mock_sx1262: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_irq: MagicMock,
    mock_gpio: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: Flag,
):
    """Test successful initialization when use_fsk flag is False."""
    mock_use_fsk.toggle(False)
    mock_sx1262_instance = mock_sx1262.return_value

    manager = SX126xManager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
        mock_spi,
        mock_chip_select,
        mock_irq,
        mock_reset,
        mock_gpio,
    )

    mock_sx1262.assert_called_once_with(
        mock_spi, mock_chip_select, mock_irq, mock_reset, mock_gpio
    )
    mock_sx1262_instance.begin.assert_called_once_with(
        freq=mock_radio_config.transmit_frequency,
        cr=mock_radio_config.lora.coding_rate,
        crcOn=mock_radio_config.lora.cyclic_redundancy_check,
        sf=mock_radio_config.lora.spreading_factor,
        power=mock_radio_config.lora.transmit_power,
    )
    mock_sx1262_instance.beginFSK.assert_not_called()
    assert manager._radio == mock_sx1262_instance
    mock_logger.debug.assert_any_call(
        "Initializing radio",
        radio_type="SX126xManager",
        modulation=RadioModulation.LORA,
    )


@pytest.mark.slow
@patch(
    "pysquared.hardware.radio.manager.sx126x.SX1262",
    new_callable=MagicMock(spec=SX1262),
)
def test_init_with_retries_fsk(
    mock_sx1262: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_irq: MagicMock,
    mock_gpio: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: Flag,
):
    """Test __init__ retries on FSK initialization failure."""
    mock_use_fsk.toggle(True)
    mock_sx1262_instance = mock_sx1262.return_value
    mock_sx1262_instance.beginFSK.side_effect = Exception("SPI Error")

    with pytest.raises(HardwareInitializationError):
        SX126xManager(
            mock_logger,
            mock_radio_config,
            mock_use_fsk,
            mock_spi,
            mock_chip_select,
            mock_irq,
            mock_reset,
            mock_gpio,
        )

    mock_logger.debug.assert_any_call(
        "Initializing radio", radio_type="SX126xManager", modulation=RadioModulation.FSK
    )
    assert mock_sx1262_instance.beginFSK.call_count == 3


@pytest.mark.slow
@patch(
    "pysquared.hardware.radio.manager.sx126x.SX1262",
    new_callable=MagicMock(spec=SX1262),
)
def test_init_with_retries_lora(
    mock_sx1262: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_irq: MagicMock,
    mock_gpio: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: Flag,
):
    """Test __init__ retries on FSK initialization failure."""
    mock_use_fsk.toggle(False)
    mock_sx1262_instance = mock_sx1262.return_value
    mock_sx1262_instance.begin.side_effect = Exception("SPI Error")

    with pytest.raises(HardwareInitializationError):
        SX126xManager(
            mock_logger,
            mock_radio_config,
            mock_use_fsk,
            mock_spi,
            mock_chip_select,
            mock_irq,
            mock_reset,
            mock_gpio,
        )

    mock_logger.debug.assert_any_call(
        "Initializing radio",
        radio_type="SX126xManager",
        modulation=RadioModulation.LORA,
    )
    assert mock_sx1262_instance.begin.call_count == 3


@pytest.fixture
def initialized_manager(
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_irq: MagicMock,
    mock_gpio: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: Flag,
) -> SX126xManager:
    """Provides an initialized SX126xManager instance with a mock radio."""
    return SX126xManager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
        mock_spi,
        mock_chip_select,
        mock_irq,
        mock_reset,
        mock_gpio,
    )


def test_send_success_bytes(
    initialized_manager: SX126xManager,
    mock_logger: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Test successful sending of bytes."""
    data_bytes = b"Hello SX126x"

    initialized_manager._radio = MagicMock(spec=SX1262)
    initialized_manager._radio.send = MagicMock()
    initialized_manager._radio.send.return_value = (len(data_bytes), ERR_NONE)

    assert initialized_manager.send(data_bytes)

    expected_bytes: bytes = b" ".join(
        [
            bytes(mock_radio_config.license, "UTF-8"),
            data_bytes,
            bytes(mock_radio_config.license, "UTF-8"),
        ]
    )

    mock_logger.info.assert_called_once_with(
        "Radio message sent", success=True, len=len(expected_bytes)
    )


def test_send_success_string(
    initialized_manager: SX126xManager,
    mock_logger: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Test successful sending of a string (should be converted to bytes)."""
    data_str = "Hello Saidi"
    expected_bytes = bytes(
        f"{mock_radio_config.license} {data_str} {mock_radio_config.license}", "UTF-8"
    )

    initialized_manager._radio = MagicMock(spec=SX1262)
    initialized_manager._radio.send = MagicMock()
    initialized_manager._radio.send.return_value = (len(expected_bytes), ERR_NONE)

    assert initialized_manager.send(data_str)
    initialized_manager._radio.send.assert_called_once_with(expected_bytes)
    mock_logger.info.assert_called_once_with(
        "Radio message sent", success=True, len=len(expected_bytes)
    )


def test_send_unlicensed(
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_irq: MagicMock,
    mock_gpio: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: Flag,
):
    """Test send attempt when not licensed."""
    mock_radio_config.license = ""  # Simulate unlicensed state

    manager = SX126xManager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
        mock_spi,
        mock_chip_select,
        mock_irq,
        mock_reset,
        mock_gpio,
    )
    manager._radio = MagicMock(spec=SX1262)
    manager._radio.send = MagicMock()

    assert not manager.send(b"test")
    manager._radio.send.assert_not_called()
    mock_logger.warning.assert_called_once_with(
        "Radio send attempt failed: Not licensed."
    )


def test_send_radio_error(
    initialized_manager: SX126xManager,
    mock_logger: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Test handling of error code returned by radio.send()."""
    initialized_manager._radio = MagicMock(spec=SX1262)
    initialized_manager._radio.send = MagicMock()
    initialized_manager._radio.send.return_value = (0, -1)

    msg = b"test"
    assert not initialized_manager.send(msg)

    license_bytes = bytes(mock_radio_config.license, "UTF-8")
    expected_bytes = b" ".join([license_bytes, msg, license_bytes])
    initialized_manager._radio.send.assert_called_once_with(expected_bytes)

    mock_logger.error.assert_called_once_with("Radio send failed with error code: -1")
    # TODO(nateinaction): Prevent this message from being logged on send failure
    # Base class logs the info message regardless of internal success/failure
    mock_logger.info.assert_called_once_with(
        "Radio message sent", success=False, len=len(expected_bytes)
    )


def test_send_exception(
    initialized_manager: SX126xManager,
    mock_logger: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Test handling of exception during radio.send()."""
    initialized_manager._radio = MagicMock(spec=SX1262)
    initialized_manager._radio.send = MagicMock()

    send_error = Exception("Send error")
    initialized_manager._radio.send.side_effect = send_error

    msg = b"test"
    assert not initialized_manager.send(msg)

    license_bytes = bytes(mock_radio_config.license, "UTF-8")
    expected_bytes = b" ".join([license_bytes, msg, license_bytes])
    initialized_manager._radio.send.assert_called_once_with(expected_bytes)
    mock_logger.error.assert_called_once_with("Error sending radio message", send_error)


def test_set_modulation_lora_to_fsk(
    initialized_manager: SX126xManager,
    mock_logger: MagicMock,
    mock_use_fsk: Flag,
):
    """Test toggling the modulation flag from LoRa to FSK."""
    initialized_manager._radio = MagicMock(spec=SX1262)
    initialized_manager._radio.radio_modulation = RadioModulation.LORA

    assert initialized_manager.get_modulation() == RadioModulation.LORA

    initialized_manager.set_modulation(RadioModulation.FSK)
    assert mock_use_fsk.get() is True

    mock_logger.info.assert_called_with(
        "Radio modulation change requested for next init",
        requested=RadioModulation.FSK,
        current=RadioModulation.LORA,
    )


def test_set_modulation_fsk_to_lora(
    initialized_manager: SX126xManager,
    mock_logger: MagicMock,
    mock_use_fsk: Flag,
):
    """Test toggling the modulation flag from LoRa to FSK."""
    initialized_manager._radio = MagicMock(spec=SX1262)
    initialized_manager._radio.radio_modulation = RadioModulation.FSK

    assert initialized_manager.get_modulation() == RadioModulation.FSK

    initialized_manager.set_modulation(RadioModulation.LORA)
    assert mock_use_fsk.get() is False

    mock_logger.info.assert_called_with(
        "Radio modulation change requested for next init",
        requested=RadioModulation.LORA,
        current=RadioModulation.FSK,
    )


def test_get_modulation_not_initialized(
    mock_use_fsk: Flag,
    mock_logger: MagicMock,
):
    """Test get_modulation when radio is not initialized (relies on flag)."""
    manager = SX126xManager.__new__(
        SX126xManager
    )  # Create instance without calling __init__
    manager._radio = None
    manager._use_fsk = mock_use_fsk
    manager._log = mock_logger

    mock_use_fsk.toggle(False)
    assert manager.get_modulation() == RadioModulation.LORA

    mock_use_fsk.toggle(True)
    assert manager.get_modulation() == RadioModulation.FSK


@patch("pysquared.hardware.radio.manager.sx126x.time")
def test_receive_success(
    mock_time: MagicMock,
    initialized_manager: SX126xManager,
    mock_logger: MagicMock,
):
    """Test successful reception of a message."""
    expected_data = b"SX Received"
    initialized_manager._radio = MagicMock(spec=SX1262)
    initialized_manager._radio.recv = MagicMock()
    initialized_manager._radio.recv.return_value = (expected_data, ERR_NONE)

    mock_time.time.side_effect = [0.0, 0.1]  # Start time, time after first check

    received_data = initialized_manager.receive(timeout=10.0)

    assert received_data == expected_data
    initialized_manager._radio.recv.assert_called_once()
    mock_logger.error.assert_not_called()
    mock_time.sleep.assert_not_called()


@patch("pysquared.hardware.radio.manager.sx126x.time")
def test_receive_timeout(
    mock_time: MagicMock,
    initialized_manager: SX126xManager,
    mock_logger: MagicMock,
):
    """Test receiving when no message arrives before timeout."""
    initialized_manager._radio = MagicMock(spec=SX1262)
    initialized_manager._radio.recv = MagicMock()
    initialized_manager._radio.recv.return_value = (b"", ERR_NONE)

    mock_time.time.side_effect = [
        0.0,  # Initial start_time
        1.0,  # First check
        5.0,  # Second check
        10.1,  # Timeout check
    ]

    # Explicitly test with the default timeout
    received_data = initialized_manager.receive(timeout=10.0)

    assert received_data is None
    assert initialized_manager._radio.recv.call_count > 1
    mock_logger.error.assert_not_called()
    mock_time.sleep.assert_called_with(0)
    assert mock_time.sleep.call_count == 2


@patch("pysquared.hardware.radio.manager.sx126x.time")
def test_receive_radio_error(
    mock_time: MagicMock,
    initialized_manager: SX126xManager,
    mock_logger: MagicMock,
):
    """Test handling of error code returned by radio.recv()."""
    error_code = -5
    initialized_manager._radio = MagicMock(spec=SX1262)
    initialized_manager._radio.recv = MagicMock()
    initialized_manager._radio.recv.return_value = (b"some data", error_code)
    mock_time.time.side_effect = [0.0, 0.1]

    received_data = initialized_manager.receive(timeout=10.0)

    assert received_data is None
    initialized_manager._radio.recv.assert_called_once()
    mock_logger.error.assert_called_once_with(
        f"Radio receive failed with error code: {error_code}"
    )


@patch("pysquared.hardware.radio.manager.sx126x.time")
def test_receive_exception(
    mock_time: MagicMock,
    initialized_manager: SX126xManager,
    mock_logger: MagicMock,
):
    """Test handling of exception during radio.recv()."""
    initialized_manager._radio = MagicMock(spec=SX1262)
    receive_error = RuntimeError("SPI Comms Failed")
    initialized_manager._radio.recv = MagicMock()
    initialized_manager._radio.recv.side_effect = receive_error

    # Mock time just enough to enter the loop once
    mock_time.time.side_effect = [0.0, 0.1]

    received_data = initialized_manager.receive(timeout=10.0)

    assert received_data is None
    initialized_manager._radio.recv.assert_called_once()
    mock_logger.error.assert_called_once_with("Error receiving data", receive_error)
