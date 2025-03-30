from ....config.radio import FSKConfig, LORAConfig, RadioConfig
from ....logger import Logger
from ....nvm.flag import Flag
from ....protos.radio import RadioProto
from ...decorators import with_retries
from ...exception import HardwareInitializationError
from ..modulation import RadioModulation

try:
    # TODO(nateinaction): Replace with mock when available
    # from mocks.proves_sx126.sx1262 import SX1262 # type: ignore
    raise ImportError
except ImportError:
    from lib.proves_sx126._sx126x import ERR_NONE
    from lib.proves_sx126.sx1262 import SX1262

# Type hinting only
try:
    from typing import Any

    from busio import SPI
    from digitalio import DigitalInOut
except ImportError:
    pass


class SX126xManager(RadioProto):
    """Manager class implementing RadioProto for SX126x radios.
    This class handles the initialization and interaction with SX126x FSK or LoRa radios.
    """

    @with_retries(max_attempts=3, initial_delay=1)
    def __init__(
        self,
        logger: Logger,
        spi: SPI,
        chip_select: DigitalInOut,
        irq: DigitalInOut,
        reset: DigitalInOut,
        gpio: DigitalInOut,
        radio_config: RadioConfig,
        use_fsk: Flag,
        is_licensed: bool,
    ) -> None:
        """Initialize the manager class and the underlying radio hardware.

        :param Logger logger: Logger instance for logging messages.
        :param busio.SPI spi: The SPI bus connected to the chip. Ensure SCK, MOSI, and MISO are connected.
        :param ~digitalio.DigitalInOut chip_select: Chip select pin.
        :param ~digitalio.DigitalInOut irq: Interrupt request pin.
        :param ~digitalio.DigitalInOut reset: Reset pin.
        :param ~digitalio.DigitalInOut gpio: General purpose IO pin (used by SX126x).
        :param RadioConfig radio_config: Radio configuration object.
        :param Flag use_fsk: Flag to determine whether to use FSK or LoRa mode.
        :param bool is_licensed: Flag indicating if radio operation is licensed.

        :raises HardwareInitializationError: If the radio fails to initialize after retries.
        """
        self._log = logger
        self._spi = spi
        self._chip_select = chip_select
        self._irq = irq
        self._reset = reset
        self._gpio = gpio
        self._radio_config = radio_config
        self._use_fsk = use_fsk
        self._is_licensed = is_licensed

        initial_modulation = self.get_modulation()

        self._log.debug(
            message="Initializing SX126x radio", modulation=initial_modulation
        )

        try:
            radio: SX1262 = SX1262(
                self._spi, self._chip_select, self._irq, self._reset, self._gpio
            )

            if initial_modulation == RadioModulation.FSK:
                self._configure_fsk(self._radio_config.fsk)
            else:
                self._configure_lora(self._radio_config.lora)

            self._radio: SX1262 = radio

        except Exception as e:
            raise HardwareInitializationError(
                f"Failed to initialize SX126x radio with modulation {initial_modulation}"
            ) from e

    def send(self, data: Any) -> bool:
        """Send data over the radio."""
        try:
            if not self._is_licensed:
                self._log.warning("Radio send attempt failed: Not licensed.")
                return False

            # Convert data to bytes if it's not already
            if isinstance(data, str):
                payload = bytes(data, "UTF-8")
            elif isinstance(data, bytes):
                payload = data
            else:
                # Attempt to convert other types, log warning if ambiguous
                self._log.warning(
                    f"Attempting to send non-bytes/str data type: {type(data)}"
                )
                payload = bytes(str(data), "UTF-8")

            _, err = self._radio.send(payload)
            if err != ERR_NONE:
                raise RuntimeError(f"Radio send failed with error: {err}")

            self._log.info("SX126x message sent", len=len(payload))
            return True
        except Exception as e:
            self._log.error("Error sending SX126x message", e)
            return False

    def set_modulation(self, req_modulation: RadioModulation) -> None:
        """Request a change in the radio modulation mode (takes effect on next init)."""
        current_modulation = self.get_modulation()
        if current_modulation != req_modulation:
            self._use_fsk.toggle(req_modulation == RadioModulation.FSK)
            self._log.info(
                "SX126x modulation change requested for next init",
                requested=req_modulation,
                current=current_modulation,
            )

    def get_modulation(self) -> RadioModulation:
        """Get the currently configured radio modulation mode."""
        if self._radio is None:
            return RadioModulation.FSK if self._use_fsk.get() else RadioModulation.LORA

        return self._radio.radio_modulation

    def _configure_fsk(self, fsk_config: FSKConfig) -> None:
        """Configure the radio for FSK mode.

        :param FSKConfig fsk_config: FSK configuration object.
        """
        self._radio.beginFSK(
            freq=self._radio_config.transmit_frequency,
            addr=fsk_config.broadcast_address,
        )

    def _configure_lora(self, lora_config: LORAConfig) -> None:
        """Configure the radio for LoRa mode.

        :param LORAConfig lora_config: LoRa configuration object.
        """
        self._radio.begin(
            freq=self._radio_config.transmit_frequency,
            cr=lora_config.coding_rate,
            crcOn=lora_config.cyclic_redundancy_check,
            sf=lora_config.spreading_factor,
            power=lora_config.transmit_power,
        )
