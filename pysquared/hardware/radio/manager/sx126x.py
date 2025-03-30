from ....config.radio import FSKConfig, LORAConfig
from ....logger import Logger
from ..modulation import RadioModulation
from .base import BaseRadioManager

try:
    from mocks.proves_sx126.sx126x import ERR_NONE  # type: ignore
    from mocks.proves_sx126.sx1262 import SX1262  # type: ignore
except ImportError:
    from lib.proves_sx126._sx126x import ERR_NONE
    from lib.proves_sx126.sx1262 import SX1262

# Type hinting only
try:
    from typing import Any

    from busio import SPI
    from digitalio import DigitalInOut

    from ....config.radio import RadioConfig
    from ....nvm.flag import Flag
except ImportError:
    pass


class SX126xManager(BaseRadioManager):
    """Manager class implementing RadioProto for SX126x radios."""

    def __init__(
        self,
        logger: Logger,
        radio_config: RadioConfig,
        use_fsk: Flag,
        is_licensed: bool,
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
        :param bool is_licensed: Flag indicating if radio operation is licensed.
        :param busio.SPI spi: The SPI bus connected to the chip. Ensure SCK, MOSI, and MISO are connected.
        :param ~digitalio.DigitalInOut chip_select: Chip select pin.
        :param ~digitalio.DigitalInOut irq: Interrupt request pin.
        :param ~digitalio.DigitalInOut reset: Reset pin.
        :param ~digitalio.DigitalInOut gpio: General purpose IO pin (used by SX126x).

        :raises HardwareInitializationError: If the radio fails to initialize after retries.
        """
        super().__init__(
            logger=logger,
            radio_config=radio_config,
            use_fsk=use_fsk,
            is_licensed=is_licensed,
            spi=spi,
            chip_select=chip_select,
            irq=irq,
            reset=reset,
            gpio=gpio,
        )

    def _initialize_radio(self, modulation: RadioModulation, **kwargs: Any) -> Any:
        """Initialize the specific SX126x radio hardware."""
        spi: SPI = kwargs["spi"]
        cs: DigitalInOut = kwargs["chip_select"]
        irq: DigitalInOut = kwargs["irq"]
        rst: DigitalInOut = kwargs["reset"]
        gpio: DigitalInOut = kwargs["gpio"]

        radio: SX1262 = SX1262(spi, cs, irq, rst, gpio)

        if modulation == RadioModulation.FSK:
            self._configure_fsk(radio, self._radio_config.fsk)
        else:
            self._configure_lora(radio, self._radio_config.lora)

        return radio

    def _send_internal(self, payload: bytes) -> bool:
        """Send data using the SX126x radio."""
        _, err = self._radio.send(payload)
        if err != ERR_NONE:
            self._log.error(f"Radio send failed with error code: {err}")
            return False
        return True

    def _get_current_modulation(self) -> RadioModulation:
        """Get the modulation mode from the initialized SX126x radio."""
        return self._radio.radio_modulation

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
