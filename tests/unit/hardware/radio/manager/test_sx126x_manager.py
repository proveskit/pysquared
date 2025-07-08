"""Unit tests for the SX126xManager class.

This module contains unit tests for the `SX126xManager` class, which manages
SX126x radios. The tests cover initialization, sending and receiving data,
and retrieving the current modulation.
"""

from typing import Generator
from unittest.mock import MagicMock, call, patch

import pytest
from busio import SPI
from digitalio import DigitalInOut

from mocks.proves_sx126.sx126x import ERR_NONE
from mocks.proves_sx126.sx1262 import SX1262
from pysquared.config.radio import RadioConfig
from pysquared.hardware.exception import HardwareInitializationError
from pysquared.hardware.radio.manager.sx126x import SX126xManager
from pysquared.hardware.radio.modulation import FSK, LoRa
from pysquared.logger import Logger


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
def mock_irq() -> MagicMock:
    """Mocks the IRQ DigitalInOut pin."""
    return MagicMock(spec=DigitalInOut)


@pytest.fixture
def mock_gpio() -> MagicMock:
    """Mocks the GPIO DigitalInOut pin."""
    return MagicMock(spec=DigitalInOut)


@pytest.fixture
def mock_logger() -> MagicMock:
    """Mocks the Logger class."""
    return MagicMock(spec=Logger)


@pytest.fixture
def mock_radio_config() -> RadioConfig:
    """Provides a mock RadioConfig instance with default values."""
    # Using the same config as RFM9x for consistency, adjust if needed
    return RadioConfig(
        {
            "license": "test license",
            "modulation": "FSK",
            "transmit_frequency": 915,
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
                "spreading_factor": 7,
                "transmit_power": 14,  # Default power for SX126x begin()
            },
        }
    )


@pytest.fixture
def mock_sx1262(
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_irq: MagicMock,
    mock_gpio: MagicMock,
) -> Generator[MagicMock, None, None]:
    """Mocks the SX1262 class.

    Args:
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.
        mock_irq: Mocked IRQ pin.
        mock_gpio: Mocked GPIO pin.

    Yields:
        A MagicMock instance of SX1262.
    """
    with patch("pysquared.hardware.radio.manager.sx126x.SX1262") as mock_class:
        mock_class.return_value = SX1262(
            mock_spi, mock_chip_select, mock_reset, mock_irq, mock_gpio
        )
        yield mock_class


def test_init_fsk_success(
    mock_sx1262: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_irq: MagicMock,
    mock_gpio: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Tests successful initialization when radio_config.modulation is FSK.

    Args:
        mock_sx1262: Mocked SX1262 class.
        mock_logger: Mocked Logger instance.
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.
        mock_irq: Mocked IRQ pin.
        mock_gpio: Mocked GPIO pin.
        mock_radio_config: Mocked RadioConfig instance.
    """
    mock_sx1262_instance = mock_sx1262.return_value
    mock_sx1262_instance.beginFSK = MagicMock()
    mock_sx1262_instance.begin = MagicMock()

    manager = SX126xManager(
        mock_logger,
        mock_radio_config,
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
    manager._radio
    assert manager._radio == mock_sx1262_instance
    mock_logger.debug.assert_any_call(
        "Initializing radio", radio_type="SX126xManager", modulation=FSK.__name__
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
):
    """Tests successful initialization when radio_config.modulation is LoRa.

    Args:
        mock_sx1262: Mocked SX1262 class.
        mock_logger: Mocked Logger instance.
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.
        mock_irq: Mocked IRQ pin.
        mock_gpio: Mocked GPIO pin.
        mock_radio_config: Mocked RadioConfig instance.
    """
    mock_radio_config.modulation = "LoRa"
    mock_sx1262_instance = mock_sx1262.return_value
    mock_sx1262_instance.beginFSK = MagicMock()
    mock_sx1262_instance.begin = MagicMock()

    manager = SX126xManager(
        mock_logger,
        mock_radio_config,
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
        modulation=LoRa.__name__,
    )


@pytest.mark.slow
def test_init_with_retries_fsk(
    mock_sx1262: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_irq: MagicMock,
    mock_gpio: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Tests __init__ retries on FSK initialization failure.

    Args:
        mock_sx1262: Mocked SX1262 class.
        mock_logger: Mocked Logger instance.
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.
        mock_irq: Mocked IRQ pin.
        mock_gpio: Mocked GPIO pin.
        mock_radio_config: Mocked RadioConfig instance.
    """
    mock_sx1262_instance = mock_sx1262.return_value
    mock_sx1262_instance.beginFSK = MagicMock()
    mock_sx1262_instance.beginFSK.side_effect = Exception("SPI Error")

    with pytest.raises(HardwareInitializationError):
        SX126xManager(
            mock_logger,
            mock_radio_config,
            mock_spi,
            mock_chip_select,
            mock_irq,
            mock_reset,
            mock_gpio,
        )

    mock_logger.debug.assert_any_call(
        "Initializing radio", radio_type="SX126xManager", modulation=FSK.__name__
    )
    assert mock_sx1262_instance.beginFSK.call_count == 3


@pytest.mark.slow
def test_init_with_retries_lora(
    mock_sx1262: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_irq: MagicMock,
    mock_gpio: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Tests __init__ retries on FSK initialization failure.

    Args:
        mock_sx1262: Mocked SX1262 class.
        mock_logger: Mocked Logger instance.
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.
        mock_irq: Mocked IRQ pin.
        mock_gpio: Mocked GPIO pin.
        mock_radio_config: Mocked RadioConfig instance.
    """
    mock_radio_config.modulation = "LoRa"
    mock_sx1262_instance = mock_sx1262.return_value
    mock_sx1262_instance.begin = MagicMock()
    mock_sx1262_instance.begin.side_effect = Exception("SPI Error")

    with pytest.raises(HardwareInitializationError):
        SX126xManager(
            mock_logger,
            mock_radio_config,
            mock_spi,
            mock_chip_select,
            mock_irq,
            mock_reset,
            mock_gpio,
        )

    mock_logger.debug.assert_any_call(
        "Initializing radio",
        radio_type="SX126xManager",
        modulation=LoRa.__name__,
    )
    assert mock_sx1262_instance.begin.call_count == 3


@pytest.fixture
def initialized_manager(
    mock_sx1262: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_irq: MagicMock,
    mock_gpio: MagicMock,
    mock_radio_config: RadioConfig,
) -> SX126xManager:
    """Provides an initialized SX126xManager instance with a mock radio.

    Args:
        mock_sx1262: Mocked SX1262 class.
        mock_logger: Mocked Logger instance.
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.
        mock_irq: Mocked IRQ pin.
        mock_gpio: Mocked GPIO pin.
        mock_radio_config: Mocked RadioConfig instance.

    Returns:
        An initialized SX126xManager instance.
    """
    return SX126xManager(
        mock_logger,
        mock_radio_config,
        mock_spi,
        mock_chip_select,
        mock_irq,
        mock_reset,
        mock_gpio,
    )


def test_send_success_bytes(
    initialized_manager: SX126xManager,
    mock_logger: MagicMock,
):
    """Tests successful sending of bytes.

    Args:
        initialized_manager: Initialized SX126xManager instance.
        mock_logger: Mocked Logger instance.
    """
    data_bytes = b"Hello SX126x"

    initialized_manager._radio = MagicMock(spec=SX1262)
    initialized_manager._radio.send = MagicMock()
    initialized_manager._radio.send.return_value = (len(data_bytes), ERR_NONE)

    assert initialized_manager.send(data_bytes)


def test_send_unlicensed(
    mock_sx1262: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_irq: MagicMock,
    mock_gpio: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Tests send attempt when not licensed.

    Args:
        mock_sx1262: Mocked SX1262 class.
        mock_logger: Mocked Logger instance.
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.
        mock_irq: Mocked IRQ pin.
        mock_gpio: Mocked GPIO pin.
        mock_radio_config: Mocked RadioConfig instance.
    """
    mock_radio_config.license = ""  # Simulate unlicensed state

    manager = SX126xManager(
        mock_logger,
        mock_radio_config,
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
    """Tests handling of error code returned by radio.send().

    Args:
        initialized_manager: Initialized SX126xManager instance.
        mock_logger: Mocked Logger instance.
        mock_radio_config: Mocked RadioConfig instance.
    """
    initialized_manager._radio = MagicMock(spec=SX1262)
    initialized_manager._radio.send = MagicMock()
    initialized_manager._radio.send.return_value = (0, -1)

    msg = b"test"
    assert not initialized_manager.send(msg)

    initialized_manager._radio.send.assert_called_once_with(msg)

    mock_logger.warning.assert_has_calls(
        [call("SX126x radio send failed", error_code=-1)]
    )


def test_send_exception(
    initialized_manager: SX126xManager,
    mock_logger: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Tests handling of exception during radio.send().

    Args:
        initialized_manager: Initialized SX126xManager instance.
        mock_logger: Mocked Logger instance.
        mock_radio_config: Mocked RadioConfig instance.
    """
    initialized_manager._radio = MagicMock(spec=SX1262)
    initialized_manager._radio.send = MagicMock()

    send_error = Exception("Send error")
    initialized_manager._radio.send.side_effect = send_error

    msg = b"test"
    assert not initialized_manager.send(msg)

    initialized_manager._radio.send.assert_called_once_with(msg)
    mock_logger.error.assert_called_once_with("Error sending radio message", send_error)


@patch("pysquared.hardware.radio.manager.sx126x.time")
def test_receive_success(
    mock_time: MagicMock,
    initialized_manager: SX126xManager,
    mock_logger: MagicMock,
):
    """Tests successful reception of a message.

    Args:
        mock_time: Mocked time module.
        initialized_manager: Initialized SX126xManager instance.
        mock_logger: Mocked Logger instance.
    """
    expected_data = b"SX Received"
    initialized_manager._radio = MagicMock(spec=SX1262)
    initialized_manager._radio.recv = MagicMock()
    initialized_manager._radio.recv.return_value = (expected_data, ERR_NONE)

    mock_time.time.side_effect = [0.0, 0.1]  # Start time, time after first check

    received_data = initialized_manager.receive(timeout=10)

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
    """Tests receiving when no message arrives before timeout.

    Args:
        mock_time: Mocked time module.
        initialized_manager: Initialized SX126xManager instance.
        mock_logger: Mocked Logger instance.
    """
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
    received_data = initialized_manager.receive()

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
    """Tests handling of error code returned by radio.recv().

    Args:
        mock_time: Mocked time module.
        initialized_manager: Initialized SX126xManager instance.
        mock_logger: Mocked Logger instance.
    """
    error_code = -5
    initialized_manager._radio = MagicMock(spec=SX1262)
    initialized_manager._radio.recv = MagicMock()
    initialized_manager._radio.recv.return_value = (b"some data", error_code)
    mock_time.time.side_effect = [0.0, 0.1]

    received_data = initialized_manager.receive(timeout=10)

    assert received_data is None
    initialized_manager._radio.recv.assert_called_once()
    mock_logger.warning.assert_called_once_with(
        "Radio receive failed", error_code=error_code
    )


@patch("pysquared.hardware.radio.manager.sx126x.time")
def test_receive_exception(
    mock_time: MagicMock,
    initialized_manager: SX126xManager,
    mock_logger: MagicMock,
):
    """Tests handling of exception during radio.recv().

    Args:
        mock_time: Mocked time module.
        initialized_manager: Initialized SX126xManager instance.
        mock_logger: Mocked Logger instance.
    """
    initialized_manager._radio = MagicMock(spec=SX1262)
    receive_error = RuntimeError("SPI Comms Failed")
    initialized_manager._radio.recv = MagicMock()
    initialized_manager._radio.recv.side_effect = receive_error

    # Mock time just enough to enter the loop once
    mock_time.time.side_effect = [0.0, 0.1]

    received_data = initialized_manager.receive(timeout=10)

    assert received_data is None
    initialized_manager._radio.recv.assert_called_once()
    mock_logger.error.assert_called_once_with("Error receiving data", receive_error)


def test_get_modulation_initialized(
    mock_sx1262: MagicMock,
    mock_logger: MagicMock,
    mock_spi: MagicMock,
    mock_chip_select: MagicMock,
    mock_reset: MagicMock,
    mock_irq: MagicMock,
    mock_gpio: MagicMock,
    mock_radio_config: RadioConfig,
):
    """Tests get_modulation when radio is initialized.

    Args:
        mock_sx1262: Mocked SX1262 class.
        mock_logger: Mocked Logger instance.
        mock_spi: Mocked SPI bus.
        mock_chip_select: Mocked chip select pin.
        mock_reset: Mocked reset pin.
        mock_irq: Mocked IRQ pin.
        mock_gpio: Mocked GPIO pin.
        mock_radio_config: Mocked RadioConfig instance.
    """

    manager = SX126xManager(
        mock_logger,
        mock_radio_config,
        mock_spi,
        mock_chip_select,
        mock_irq,
        mock_reset,
        mock_gpio,
    )
    assert manager.get_modulation() == FSK
