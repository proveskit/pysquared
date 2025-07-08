"""This module provides a manager for SX1280 radios.

This module defines the `SX1280Manager` class, which implements the `RadioProto`
interface for SX1280 radios. It handles the initialization and configuration of
the radio, as well as sending and receiving data.

**Usage:**
```python
logger = Logger()
radio_config = RadioConfig()
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.D5)
reset = digitalio.DigitalInOut(board.D6)
busy = digitalio.DigitalInOut(board.D7)
txen = digitalio.DigitalInOut(board.D8)
rxen = digitalio.DigitalInOut(board.D9)
sx1280_manager = SX1280Manager(logger, radio_config, spi, cs, reset, busy, 2400.0, txen, rxen)
sx1280_manager.send(b"Hello world!")
```
"""

from busio import SPI
from digitalio import DigitalInOut
from proves_sx1280.sx1280 import SX1280

from pysquared.config.radio import RadioConfig

from ....logger import Logger
from ..modulation import LoRa, RadioModulation
from .base import BaseRadioManager

# Type hinting only
try:
    from typing import Optional, Type
except ImportError:
    pass


class SX1280Manager(BaseRadioManager):
    """Manages SX1280 radios, implementing the RadioProto interface."""

    _radio: SX1280

    def __init__(
        self,
        logger: Logger,
        radio_config: RadioConfig,
        spi: SPI,
        chip_select: DigitalInOut,
        reset: DigitalInOut,
        busy: DigitalInOut,
        frequency: float,
        txen: DigitalInOut,
        rxen: DigitalInOut,
    ) -> None:
        """Initializes the SX1280Manager and the underlying radio hardware.

        Args:
            logger: Logger instance for logging messages.
            radio_config: Radio configuration object.
            spi: The SPI bus connected to the chip.
            chip_select: Chip select pin.
            reset: Reset pin.
            busy: Busy pin.
            frequency: The frequency to operate on.
            txen: Transmit enable pin.
            rxen: Receive enable pin.
        """
        self._spi = spi
        self._chip_select = chip_select
        self._reset = reset
        self._busy = busy
        self._frequency = frequency
        self._txen = txen
        self._rxen = rxen

        super().__init__(logger=logger, radio_config=radio_config)

    def _initialize_radio(self, modulation: Type[RadioModulation]) -> None:
        """Initializes the specific SX1280 radio hardware.

        Args:
            modulation: The modulation mode to initialize with.
        """
        self._radio = SX1280(
            self._spi,
            self._chip_select,
            self._reset,
            self._busy,
            frequency=self._frequency,
            txen=self._txen,
            rxen=self._rxen,
        )

    def _send_internal(self, data: bytes) -> bool:
        """Sends data using the SX1280 radio.

        Args:
            data: The data to send.

        Returns:
            True if the data was sent successfully, False otherwise.
        """
        return bool(self._radio.send(data))

    def get_modulation(self) -> Type[RadioModulation]:
        """Gets the modulation mode from the initialized SX1280 radio.

        Returns:
            The current modulation mode of the hardware.
        """
        return LoRa

    def receive(self, timeout: Optional[int] = None) -> bytes | None:
        """Receives data from the radio.

        Args:
            timeout: Optional receive timeout in seconds. If None, use the default timeout.

        Returns:
            The received data as bytes, or None if no data was received.
        """
        try:
            msg = self._radio.receive(keep_listening=True)

            if msg is None:
                self._log.debug("No message received")
                return None

            return bytes(msg)
        except Exception as e:
            self._log.error("Error receiving data", e)
            return None
