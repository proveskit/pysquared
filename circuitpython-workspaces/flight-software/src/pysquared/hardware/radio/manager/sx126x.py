"""This module provides a manager for SX126x radios.

This module defines the `SX126xManager` class, which implements the `RadioProto`
interface for SX126x radios. It handles the initialization and configuration of
the radio, as well as sending and receiving data.

**Usage:**
```python
logger = Logger()
radio_config = RadioConfig()
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.D5)
irq = digitalio.DigitalInOut(board.D6)
reset = digitalio.DigitalInOut(board.D7)
gpio = digitalio.DigitalInOut(board.D8)
sx126x_manager = SX126xManager(logger, radio_config, spi, cs, irq, reset, gpio)
sx126x_manager.send(b"Hello world!")
```
"""

import time

from busio import SPI
from digitalio import DigitalInOut
from proves_sx126._sx126x import ERR_NONE
from proves_sx126.sx1262 import SX1262

from ....config.radio import FSKConfig, LORAConfig, RadioConfig
from ....logger import Logger
from ..modulation import FSK, LoRa, RadioModulation
from .base import BaseRadioManager

# Type hinting only
try:
    from typing import Optional, Type
except ImportError:
    pass


class SX126xManager(BaseRadioManager):
    """Manages SX126x radios, implementing the RadioProto interface."""

    _radio: SX1262

    def __init__(
        self,
        logger: Logger,
        radio_config: RadioConfig,
        spi: SPI,
        chip_select: DigitalInOut,
        irq: DigitalInOut,
        reset: DigitalInOut,
        gpio: DigitalInOut,
    ) -> None:
        """Initializes the SX126xManager and the underlying radio hardware.

        Args:
            logger: Logger instance for logging messages.
            radio_config: Radio configuration object.
            spi: The SPI bus connected to the chip.
            chip_select: Chip select pin.
            irq: Interrupt request pin.
            reset: Reset pin.
            gpio: General purpose IO pin (used by SX126x).

        Raises:
            HardwareInitializationError: If the radio fails to initialize after retries.
        """
        self._spi = spi
        self._chip_select = chip_select
        self._irq = irq
        self._reset = reset
        self._gpio = gpio

        super().__init__(logger=logger, radio_config=radio_config)

    def _initialize_radio(self, modulation: Type[RadioModulation]) -> None:
        """Initializes the specific SX126x radio hardware.

        Args:
            modulation: The modulation mode to initialize with.
        """
        self._radio = SX1262(
            self._spi, self._chip_select, self._irq, self._reset, self._gpio
        )

        if modulation == FSK:
            self._configure_fsk(self._radio, self._radio_config.fsk)
        else:
            self._configure_lora(self._radio, self._radio_config.lora)

    def _send_internal(self, data: bytes) -> bool:
        """Sends data using the SX126x radio.

        Args:
            data: The data to send.

        Returns:
            True if the data was sent successfully, False otherwise.
        """
        _, err = self._radio.send(data)
        if err != ERR_NONE:
            self._log.warning("SX126x radio send failed", error_code=err)
            return False
        return True

    def _configure_fsk(self, radio: SX1262, fsk_config: FSKConfig) -> None:
        """Configures the radio for FSK mode.

        Args:
            radio: The SX1262 radio instance.
            fsk_config: The FSK configuration.
        """
        radio.beginFSK(
            freq=self._radio_config.transmit_frequency,
            addr=fsk_config.broadcast_address,
        )

    def _configure_lora(self, radio: SX1262, lora_config: LORAConfig) -> None:
        """Configures the radio for LoRa mode.

        Args:
            radio: The SX1262 radio instance.
            lora_config: The LoRa configuration.
        """
        radio.begin(
            freq=self._radio_config.transmit_frequency,
            cr=lora_config.coding_rate,
            crcOn=lora_config.cyclic_redundancy_check,
            sf=lora_config.spreading_factor,
            power=lora_config.transmit_power,
        )

    def receive(self, timeout: Optional[int] = None) -> bytes | None:
        """Receives data from the radio.

        Args:
            timeout: Optional receive timeout in seconds. If None, use the default timeout.

        Returns:
            The received data as bytes, or None if no data was received.
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
                    self._log.debug(f"Received message ({len(msg)} bytes)")
                    return msg

                time.sleep(0)
        except Exception as e:
            self._log.error("Error receiving data", e)
            return None

    def get_modulation(self) -> Type[RadioModulation]:
        """Gets the modulation mode from the initialized SX126x radio.

        Returns:
            The current modulation mode of the hardware.
        """
        return FSK if self._radio.radio_modulation == "FSK" else LoRa
