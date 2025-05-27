import time

from busio import SPI
from digitalio import DigitalInOut
from proves_sx126._sx126x import ERR_NONE
from proves_sx126.sx1262 import SX1262

from ....config.config import Config
from ....config.radio import FSKConfig, LORAConfig
from ....logger import Logger
from ..modulation import FSK, RadioModulation
from .base import BaseRadioManager

# Type hinting only
try:
    from typing import Optional, Type
except ImportError:
    pass


class SX126xManager(BaseRadioManager):
    """Manager class implementing RadioProto for SX126x radios."""

    _radio: SX1262

    def __init__(
        self,
        logger: Logger,
        config: Config,
        spi: SPI,
        chip_select: DigitalInOut,
        irq: DigitalInOut,
        reset: DigitalInOut,
        gpio: DigitalInOut,
    ) -> None:
        """Initialize the manager class and the underlying radio hardware.

        :param Logger logger: Logger instance for logging messages.
        :param RadioConfig radio_config: Radio configuration object.
        :param Flag use_fsk: Flag to determine whether to use FSK or LoRa mode.
        :param busio.SPI spi: The SPI bus connected to the chip. Ensure SCK, MOSI, and MISO are connected.
        :param ~digitalio.DigitalInOut chip_select: Chip select pin.
        :param ~digitalio.DigitalInOut irq: Interrupt request pin.
        :param ~digitalio.DigitalInOut reset: Reset pin.
        :param ~digitalio.DigitalInOut gpio: General purpose IO pin (used by SX126x).

        :raises HardwareInitializationError: If the radio fails to initialize after retries.
        """
        self._spi = spi
        self._chip_select = chip_select
        self._irq = irq
        self._reset = reset
        self._gpio = gpio

        super().__init__(
            logger=logger,
            config=config,
        )

    def _initialize_radio(self, modulation: Type[RadioModulation]) -> None:
        """Initialize the specific SX126x radio hardware."""
        self._radio = SX1262(
            self._spi, self._chip_select, self._irq, self._reset, self._gpio
        )

        if modulation == FSK:
            self._configure_fsk(self._radio, self._radio_config.fsk)
        else:
            self._configure_lora(self._radio, self._radio_config.lora)

    def _send_internal(self, payload: bytes) -> bool:
        """Send data using the SX126x radio."""
        _, err = self._radio.send(payload)
        if err != ERR_NONE:
            self._log.warning("Radio send failed", error_code=err)
            return False
        return True

    def _configure_fsk(self, radio: SX1262, fsk_config: FSKConfig) -> None:
        """Configure the radio for FSK mode."""
        radio.beginFSK(
            freq=self._radio_config.transmit_frequency,
            addr=fsk_config.broadcast_address,
        )

    def _configure_lora(self, radio: SX1262, lora_config: LORAConfig) -> None:
        """Configure the radio for LoRa mode."""
        radio.begin(
            freq=self._radio_config.transmit_frequency,
            cr=lora_config.coding_rate,
            crcOn=lora_config.cyclic_redundancy_check,
            sf=lora_config.spreading_factor,
            power=lora_config.transmit_power,
        )

    def receive(self, timeout: Optional[int] = None) -> bytes | None:
        """Receive data from the radio.

        :param int | None timeout: Optional receive timeout in seconds. If None, use the default timeout.
        :return: The received data as bytes, or None if no data was received.
        """
        if timeout is None:
            timeout = self._receive_timeout

        self._log.debug(
            "Attempting to receive data with timeout", timeout_seconds=timeout
        )

        try:
            start_time: float = time.time()
            while True:
                if time.time() - start_time > timeout:
                    self._log.debug("Receive timeout reached.")
                    return None

                msg: bytes
                err: int
                msg, err = self._radio.recv()

                if msg:
                    if err != ERR_NONE:
                        self._log.warning("Radio receive failed", error_code=err)
                        return None
                    self._log.info(f"Received message ({len(msg)} bytes)")
                    return msg

                time.sleep(0)
        except Exception as e:
            self._log.error("Error receiving data", e)
            return None
