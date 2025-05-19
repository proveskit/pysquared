from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from busio import SPI
from digitalio import DigitalInOut

from mocks.adafruit_rfm.rfm9x import RFM9x
from mocks.circuitpython.byte_array import ByteArray
from mocks.proves_sx1280.sx1280 import SX1280
from pysquared.config.radio import RadioConfig
from pysquared.hardware.exception import HardwareInitializationError
from pysquared.hardware.radio.manager.sx1280 import SX1280Manager
from pysquared.hardware.radio.modulation import FSK, LoRa
from pysquared.logger import Logger
from pysquared.nvm.flag import Flag


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
def mock_busy() -> MagicMock:
    return MagicMock(spec=DigitalInOut)


@pytest.fixture
def mock_txen() -> MagicMock:
    return MagicMock(spec=DigitalInOut)


@pytest.fixture
def mock_rxen() -> MagicMock:
    return MagicMock(spec=DigitalInOut)


@pytest.fixture
def mock_logger() -> MagicMock:
    return MagicMock(spec=Logger)


@pytest.fixture
def mock_use_fsk() -> MagicMock:
    return MagicMock(spec=Flag)


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
                "spreading_factor": 7,
                "transmit_power": 23,
            },
        }
    )


@pytest.fixture
def mock_sx1280(
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_busy: MagicMock,
    mock_txen: MagicMock,
    mock_rxen: MagicMock,
) -> Generator[MagicMock, None, None]:
    with patch("pysquared.hardware.radio.manager.sx1280.SX1280") as mock_class:
        mock_class.return_value = SX1280(
            mock_spi,
            mock_chip_select,
            mock_reset,
            mock_busy,
            frequency=2.4,
            txen=mock_txen,
            rxen=mock_rxen,
        )
        yield mock_class


def test_init_fsk_success(
    mock_sx1280: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_busy: MagicMock,
    mock_txen: MagicMock,
    mock_rxen: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: MagicMock,
):
    """Test successful initialization when use_fsk flag is True."""
    mock_use_fsk.get.return_value = True
    mock_radio_instance = MagicMock(spec=SX1280)
    mock_sx1280.return_value = mock_radio_instance

    manager = SX1280Manager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
        mock_spi,
        mock_chip_select,
        mock_reset,
        mock_busy,
        2.4,
        mock_txen,
        mock_rxen,
    )

    mock_sx1280.assert_called_once_with(
        mock_spi,
        mock_chip_select,
        mock_reset,
        mock_busy,
        frequency=2.4,
        txen=mock_txen,
        rxen=mock_rxen,
    )
    assert manager._radio == mock_radio_instance
    mock_logger.debug.assert_called_with(
        "Initializing radio", radio_type="SX1280Manager", modulation="FSK"
    )


def test_init_lora_success(
    mock_sx1280: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_busy: MagicMock,
    mock_txen: MagicMock,
    mock_rxen: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: MagicMock,
):
    """Test successful initialization when use_fsk flag is False."""
    mock_use_fsk.get.return_value = False
    mock_radio_instance = MagicMock(spec=SX1280)
    mock_sx1280.return_value = mock_radio_instance

    manager = SX1280Manager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
        mock_spi,
        mock_chip_select,
        mock_reset,
        mock_busy,
        2.4,
        mock_txen,
        mock_rxen,
    )

    mock_sx1280.assert_called_once_with(
        mock_spi,
        mock_chip_select,
        mock_reset,
        mock_busy,
        frequency=2.4,
        txen=mock_txen,
        rxen=mock_rxen,
    )
    assert manager._radio == mock_radio_instance
    mock_logger.debug.assert_called_with(
        "Initializing radio", radio_type="SX1280Manager", modulation="LoRa"
    )


@pytest.mark.slow
def test_init_with_retries_fsk(
    mock_sx1280: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_busy: MagicMock,
    mock_txen: MagicMock,
    mock_rxen: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: MagicMock,
):
    """Test successful initialization when use_fsk flag is True."""
    mock_use_fsk.get.return_value = True
    mock_sx1280.side_effect = Exception("Simulated FSK failure")

    with pytest.raises(HardwareInitializationError):
        SX1280Manager(
            mock_logger,
            mock_radio_config,
            mock_use_fsk,
            mock_spi,
            mock_chip_select,
            mock_reset,
            mock_busy,
            2.4,
            mock_txen,
            mock_rxen,
        )

    mock_logger.debug.assert_called_with(
        "Initializing radio", radio_type="SX1280Manager", modulation="FSK"
    )
    assert mock_sx1280.call_count == 3


@pytest.mark.slow
def test_init_with_retries_lora(
    mock_sx1280: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_busy: MagicMock,
    mock_txen: MagicMock,
    mock_rxen: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: MagicMock,
):
    """Test successful initialization when use_fsk flag is False."""
    mock_use_fsk.get.return_value = True
    mock_sx1280.side_effect = Exception("Simulated FSK failure")

    with pytest.raises(HardwareInitializationError):
        SX1280Manager(
            mock_logger,
            mock_radio_config,
            mock_use_fsk,
            mock_spi,
            mock_chip_select,
            mock_reset,
            mock_busy,
            2.4,
            mock_txen,
            mock_rxen,
        )

    mock_logger.debug.assert_called_with(
        "Initializing radio", radio_type="SX1280Manager", modulation="FSK"
    )
    assert mock_sx1280.call_count == 3


# Test send Method
def test_send_success_bytes(
    mock_sx1280: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_busy: MagicMock,
    mock_txen: MagicMock,
    mock_rxen: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: MagicMock,
):
    """Test successful sending of bytes."""
    mock_use_fsk.get.return_value = False
    mock_radio_instance = MagicMock(spec=RFM9x)
    mock_radio_instance.send = MagicMock()
    mock_radio_instance.send.return_value = True  # Simulate successful send
    mock_sx1280.return_value = mock_radio_instance

    manager = SX1280Manager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
        mock_spi,
        mock_chip_select,
        mock_reset,
        mock_busy,
        2.4,
        mock_txen,
        mock_rxen,
    )

    msg = b"Hello Radio"
    result = manager.send(msg)

    license_bytes: bytes = bytes(mock_radio_config.license, "UTF-8")
    expected_msg: bytes = b" ".join([license_bytes, msg, license_bytes])

    assert result is True
    mock_radio_instance.send.assert_called_once_with(expected_msg)
    mock_logger.info.assert_called_once_with("Radio message sent")


def test_send_success_string(
    mock_sx1280: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_busy: MagicMock,
    mock_txen: MagicMock,
    mock_rxen: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: MagicMock,
):
    """Test successful sending of a string (should be converted to bytes)."""
    mock_use_fsk.get.return_value = False
    mock_radio_instance = MagicMock(spec=RFM9x)
    mock_radio_instance.send = MagicMock()
    mock_radio_instance.send.return_value = True
    mock_sx1280.return_value = mock_radio_instance

    manager = SX1280Manager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
        mock_spi,
        mock_chip_select,
        mock_reset,
        mock_busy,
        2.4,
        mock_txen,
        mock_rxen,
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
    mock_sx1280: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_busy: MagicMock,
    mock_txen: MagicMock,
    mock_rxen: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: MagicMock,
):
    """Test successful sending of a string (should be converted to bytes)."""
    mock_use_fsk.get.return_value = False
    mock_radio_instance = MagicMock(spec=RFM9x)
    mock_radio_instance.send = MagicMock()
    mock_radio_instance.send.return_value = True
    mock_sx1280.return_value = mock_radio_instance

    manager = SX1280Manager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
        mock_spi,
        mock_chip_select,
        mock_reset,
        mock_busy,
        2.4,
        mock_txen,
        mock_rxen,
    )

    result = manager.send(manager)
    assert result is True

    mock_radio_instance.send.assert_called_once_with(
        bytes(f"testlicense {manager} testlicense", "UTF-8")
    )
    mock_logger.warning.assert_called_once_with(
        "Attempting to send non-bytes/str data type: <class 'pysquared.hardware.radio.manager.sx1280.SX1280Manager'>",
    )


def test_send_unlicensed(
    mock_sx1280: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_busy: MagicMock,
    mock_txen: MagicMock,
    mock_rxen: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: MagicMock,
):
    """Test send attempt when not licensed."""
    mock_use_fsk.get.return_value = False
    mock_radio_instance = MagicMock(spec=RFM9x)
    mock_radio_instance.send = MagicMock()
    mock_sx1280.return_value = mock_radio_instance

    mock_radio_config.license = ""  # Simulate unlicensed state

    manager = SX1280Manager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
        mock_spi,
        mock_chip_select,
        mock_reset,
        mock_busy,
        2.4,
        mock_txen,
        mock_rxen,
    )

    result = manager.send(b"test")

    assert result is False
    mock_radio_instance.send.assert_not_called()
    mock_logger.warning.assert_called_once_with(
        "Radio send attempt failed: Not licensed."
    )


def test_send_exception(
    mock_sx1280: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_busy: MagicMock,
    mock_txen: MagicMock,
    mock_rxen: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: MagicMock,
):
    """Test handling of exception during radio.send()."""
    mock_use_fsk.get.return_value = False
    mock_radio_instance = MagicMock(spec=RFM9x)
    mock_radio_instance.send = MagicMock()
    send_error = RuntimeError("SPI Error")
    mock_radio_instance.send.side_effect = send_error
    mock_sx1280.return_value = mock_radio_instance

    manager = SX1280Manager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
        mock_spi,
        mock_chip_select,
        mock_reset,
        mock_busy,
        2.4,
        mock_txen,
        mock_rxen,
    )

    result = manager.send(b"test")

    assert result is False
    mock_logger.error.assert_called_once_with("Error sending radio message", send_error)


@patch("pysquared.nvm.flag.microcontroller")
def test_set_modulation_lora_to_fsk(
    mock_microcontroller: MagicMock,
    mock_sx1280: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_busy: MagicMock,
    mock_txen: MagicMock,
    mock_rxen: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: MagicMock,
):
    """Test toggling the modulation flag."""
    mock_microcontroller.nvm = ByteArray(size=1)
    use_fsk = Flag(0, 0)

    # Start as LoRa
    use_fsk.toggle(False)
    manager = SX1280Manager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
        mock_spi,
        mock_chip_select,
        mock_reset,
        mock_busy,
        2.4,
        mock_txen,
        mock_rxen,
    )
    assert manager.get_modulation() == LoRa
    assert use_fsk.get() is False

    # Request FSK
    manager.set_modulation(FSK)
    assert use_fsk.get() is False
    mock_logger.info.assert_called_with(
        "Radio modulation change requested for next init",
        requested=FSK,
        current=LoRa,
    )


@patch("pysquared.nvm.flag.microcontroller")
def test_set_modulation_fsk_to_lora(
    mock_microcontroller: MagicMock,
    mock_sx1280: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_busy: MagicMock,
    mock_txen: MagicMock,
    mock_rxen: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: MagicMock,
):
    """Test toggling the modulation flag."""
    mock_microcontroller.nvm = ByteArray(size=1)
    use_fsk = Flag(0, 0)

    # Start as FSK
    use_fsk.toggle(True)
    manager = SX1280Manager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
        mock_spi,
        mock_chip_select,
        mock_reset,
        mock_busy,
        2.4,
        mock_txen,
        mock_rxen,
    )
    assert manager.get_modulation() == LoRa
    assert use_fsk.get() is True

    # Request LoRa
    manager.set_modulation(LoRa)
    mock_logger.info.assert_not_called()
    mock_logger.warning.assert_called_with(
        "SX1280 library does not support FSK modulation, using LoRa"
    )


def test_get_modulation_initialized(
    mock_sx1280: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_busy: MagicMock,
    mock_txen: MagicMock,
    mock_rxen: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: MagicMock,
):
    """Test get_modulation when radio is initialized."""
    # Test FSK instance
    mock_use_fsk.get.return_value = True
    manager = SX1280Manager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
        mock_spi,
        mock_chip_select,
        mock_reset,
        mock_busy,
        2.4,
        mock_txen,
        mock_rxen,
    )
    assert manager.get_modulation() == LoRa

    # Test LoRa instance
    mock_use_fsk.get.return_value = False
    manager = SX1280Manager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
        mock_spi,
        mock_chip_select,
        mock_reset,
        mock_busy,
        2.4,
        mock_txen,
        mock_rxen,
    )
    assert manager.get_modulation() == LoRa


def test_receive_success(
    mock_sx1280: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_busy: MagicMock,
    mock_txen: MagicMock,
    mock_rxen: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: MagicMock,
):
    """Test successful reception of a message."""
    mock_use_fsk.get.return_value = False
    mock_radio_instance = MagicMock(spec=RFM9x)
    expected_data = b"Received Data"
    mock_radio_instance.receive = MagicMock()
    mock_radio_instance.receive.return_value = expected_data
    mock_sx1280.return_value = mock_radio_instance

    manager = SX1280Manager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
        mock_spi,
        mock_chip_select,
        mock_reset,
        mock_busy,
        2.4,
        mock_txen,
        mock_rxen,
    )

    received_data = manager.receive(timeout=10)

    assert received_data == expected_data
    mock_radio_instance.receive.assert_called_once_with(keep_listening=True)
    mock_logger.error.assert_not_called()


def test_receive_no_message(
    mock_sx1280: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_busy: MagicMock,
    mock_txen: MagicMock,
    mock_rxen: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: MagicMock,
):
    """Test receiving when no message is available (timeout)."""
    mock_use_fsk.get.return_value = False
    mock_radio_instance = MagicMock(spec=RFM9x)
    mock_radio_instance.receive = MagicMock()
    mock_radio_instance.receive.return_value = None  # Simulate timeout
    mock_sx1280.return_value = mock_radio_instance

    manager = SX1280Manager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
        mock_spi,
        mock_chip_select,
        mock_reset,
        mock_busy,
        2.4,
        mock_txen,
        mock_rxen,
    )

    received_data = manager.receive(timeout=10)

    assert received_data is None
    mock_radio_instance.receive.assert_called_once_with(keep_listening=True)
    mock_logger.debug.assert_called_with("No message received")
    mock_logger.error.assert_not_called()


def test_receive_exception(
    mock_sx1280: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_busy: MagicMock,
    mock_txen: MagicMock,
    mock_rxen: MagicMock,
    mock_radio_config: RadioConfig,
    mock_use_fsk: MagicMock,
):
    """Test handling of exception during radio.receive()."""
    mock_use_fsk.get.return_value = False
    mock_radio_instance = MagicMock(spec=RFM9x)
    mock_radio_instance.receive = MagicMock()
    receive_error = RuntimeError("Receive Error")
    mock_radio_instance.receive.side_effect = receive_error
    mock_sx1280.return_value = mock_radio_instance

    manager = SX1280Manager(
        mock_logger,
        mock_radio_config,
        mock_use_fsk,
        mock_spi,
        mock_chip_select,
        mock_reset,
        mock_busy,
        2.4,
        mock_txen,
        mock_rxen,
    )

    received_data = manager.receive()

    assert received_data is None
    mock_radio_instance.receive.assert_called_once_with(keep_listening=True)
    mock_logger.error.assert_called_once_with("Error receiving data", receive_error)
