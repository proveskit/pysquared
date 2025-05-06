from busio import SPI
from digitalio import DigitalInOut
from proves_sx1280.sx1280 import SX1280

from ....config.radio import RadioConfig
from ....logger import Logger
from ....nvm.flag import Flag
from ..modulation import LoRa, RadioModulation
from .base import BaseRadioManager

# Type hinting only
try:
    from typing import Optional, Type
except ImportError:
    pass


class SX1280Manager(BaseRadioManager):
    """Manager class implementing RadioProto for SX1280 radios."""

    _radio: SX1280

    def __init__(
        self,
        logger: Logger,
        radio_config: RadioConfig,
        use_fsk: Flag,
        spi: SPI,
        chip_select: DigitalInOut,
        reset: DigitalInOut,
        busy: DigitalInOut,
        frequency: float,
        txen: DigitalInOut,
        rxen: DigitalInOut,
    ) -> None:
        """Initialize the manager class and the underlying radio hardware.

        :param Logger logger: Logger instance for logging messages.
        :param RadioConfig radio_config: Radio configuration object.
        :param Flag use_fsk: Flag to determine whether to use FSK or LoRa mode.
        :param busio.SPI spi: The SPI bus connected to the chip. Ensure SCK, MOSI, and MISO are connected.
        :param ~digitalio.DigitalInOut chip_select: Chip select pin.
        :param ~digitalio.DigitalInOut busy: Interrupt request pin.
        :param ~digitalio.DigitalInOut reset: Reset pin.
        :param ~digitalio.DigitalInOut gpio: General purpose IO pin (used by SX1280).

        :raises HardwareInitializationError: If the radio fails to initialize after retries.
        """
        self._spi = spi
        self._chip_select = chip_select
        self._reset = reset
        self._busy = busy
        self._frequency = frequency
        self._txen = txen
        self._rxen = rxen

        super().__init__(
            logger=logger,
            radio_config=radio_config,
            use_fsk=use_fsk,
        )

    def _initialize_radio(self, modulation: Type[RadioModulation]) -> None:
        """Initialize the specific SX1280 radio hardware."""
        self._radio = SX1280(
            self._spi,
            self._chip_select,
            self._reset,
            self._busy,
            frequency=self._frequency,
            txen=self._txen,
            rxen=self._rxen,
        )

    def _send_internal(self, payload: bytes) -> bool:
        """Send data using the SX1280 radio."""
        return bool(self._radio.send(payload))

    def get_modulation(self) -> Type[RadioModulation]:
        """Get the modulation mode from the initialized SX1280 radio."""
        self._log.warning("SX1280 library does not support FSK modulation, using LoRa")
        return LoRa

    def receive(self, timeout: Optional[int] = None) -> bytes | None:
        """Receive data from the radio.

        :param int | None timeout: Optional receive timeout in seconds. If None, use the default timeout.
        :return: The received data as bytes, or None if no data was received.
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
