from .modulation import RFM9xModulation

# Type hinting only
try:
    from typing import Any

    from adafruit_rfm.rfm_common import RFMSPI

    from pysquared.hardware.rfm9x.factory import RFM9xFactory
    from pysquared.logger import Logger
    from pysquared.nvm.flag import Flag
except ImportError:
    pass


class RFM9xManager:
    """Manages the lifecycle and mode switching of the RFM9x radio."""

    _radio: RFMSPI | None = None

    def __init__(
        self,
        logger: Logger,
        use_fsk: Flag,
        radio_factory: RFM9xFactory,
        is_licensed: bool,
    ) -> None:
        """Initialize the rfm9x manager.

        Stores configuration but doesn't create radio until needed.

        :param Logger logger: Logger instance for logging messages.
        :param Flag use_fsk: Flag to determine whether to use FSK or LoRa mode.
        :param RFM9xFactory radio_factory: Factory for creating RFM9x radio instances.

        :raises HardwareInitializationError: If the radio fails to initialize.
        """
        self._log = logger
        self._use_fsk = use_fsk
        self._radio_factory = radio_factory
        self._is_licensed = is_licensed

        self._radio = self.radio

    @property
    def radio(self) -> RFMSPI:
        """Get the current radio instance, creating it if needed.
        :return ~adafruit_rfm.rfm_common.RFMSPI: The RFM9x radio instance.
        """
        if self._radio is None:
            self._radio = self._radio_factory.create(
                self._log,
                self.get_modulation(),
            )

            # Always toggle back to LoRa on reboot
            self.set_modulation(RFM9xModulation.LORA)

        return self._radio

    def beacon_radio_message(self, msg: Any) -> None:
        """Beacon a radio message and log the result."""
        try:
            if not self._is_licensed:
                raise ValueError("Radio is not licensed")

            sent = self.radio.send(bytes(msg, "UTF-8"))
        except Exception as e:
            self._log.error("There was an error while beaconing", e)
            return

        self._log.info("I am beaconing", beacon=str(msg), success=str(sent))

    def get_modulation(self) -> str:
        """Get the current radio modulation.
        :return str: The current radio modulation.
        """
        if self._radio is None:
            return RFM9xModulation.FSK if self._use_fsk.get() else RFM9xModulation.LORA

        return self._radio_factory.get_instance_modulation(self.radio)

    def set_modulation(self, req_modulation: RFM9xModulation) -> None:
        """
        Set the radio modulation.
        Takes effect on the next reboot.
        :param radio.RFM9xModulation req_modulation: The modulation to switch to.
        :return: None
        """
        if self.get_modulation() != req_modulation:
            self._use_fsk.toggle(req_modulation == RFM9xModulation.FSK)
            self._log.info(
                "Radio modulation change requested", modulation=req_modulation
            )

    def get_temperature(self) -> int:
        """Get the temperature from the radio.
        :return int: The temperature in degrees Celsius.
        """
        raw_temp = self.radio.read_u8(0x5B)
        temp = raw_temp & 0x7F
        if (raw_temp & 0x80) == 0x80:
            temp = ~temp + 0x01

        prescaler = 143
        return temp + prescaler
