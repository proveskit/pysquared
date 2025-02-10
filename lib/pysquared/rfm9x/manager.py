try:
    from stubs.circuitpython.busio import SPI
    from stubs.circuitpython.digitalio import DigitalInOut
except ImportError:
    from busio import SPI
    from digitalio import DigitalInOut

from lib.adafruit_rfm.rfm9xfsk import RFM9xFSK
from lib.adafruit_rfm.rfm_common import RFMSPI
from lib.pysquared.logger import Logger
from lib.pysquared.nvm.flag import Flag
from lib.pysquared.rfm9x.factory import RFM9xFactory
from lib.pysquared.rfm9x.modulation import RFM9xModulation


class RFM9xManager:
    """Manages the lifecycle and mode switching of the RFM9x radio."""

    _radio: RFMSPI | None = None

    def __init__(
        self,
        logger: Logger,
        spi: SPI,
        chip_select: DigitalInOut,
        reset: DigitalInOut,
        use_fsk: Flag,
        sender_id: int,
        receiver_id: int,
        frequency: int,
        transmit_power: int,
        lora_spreading_factor: int,
    ):
        """Initialize the rfm9x manager.

        Stores configuration but doesn't create radio until needed.

        :param Logger logger: Logger instance for logging messages.
        :param busio.SPI spi: The SPI bus connected to the chip. Ensure SCK, MOSI, and MISO are connected.
        :param ~digitalio.DigitalInOut cs: A DigitalInOut object connected to the chip's CS/chip select line.
        :param ~digitalio.DigitalInOut reset: A DigitalInOut object connected to the chip's RST/reset line.
        :param Flag use_fsk: Flag to determine whether to use FSK or LoRa mode.
        :param int sender_id: ID of the sender radio.
        :param int receiver_id: ID of the receiver radio.
        :param int frequency: Frequency at which the radio will transmit.
        :param int transmit_power: Transmit power level (applicable for LoRa only).
        :param int lora_spreading_factor: Spreading factor for LoRa modulation (applicable for LoRa only).

        :raises HardwareInitializationError: If the radio fails to initialize.
        """
        self._log = logger
        self._spi = spi
        self._chip_select = chip_select
        self._reset = reset
        self._use_fsk = use_fsk
        self._sender_id = sender_id
        self._receiver_id = receiver_id
        self._frequency = frequency
        self._transmit_power = transmit_power
        self._lora_spreading_factor = lora_spreading_factor

        self._radio = self.radio

    @property
    def radio(self) -> RFMSPI:
        """Get the current radio instance, creating it if needed.
        :return ~lib.adafruit_rfm.rfm_common.RFMSPI: The RFM9x radio instance.
        """
        if self._radio is None:
            self._radio = RFM9xFactory.create(
                self._log,
                self._spi,
                self._chip_select,
                self._reset,
                self.get_modulation(),
                self._sender_id,
                self._receiver_id,
                self._frequency,
                self._transmit_power,
                self._lora_spreading_factor,
            )

            # TODO: We should use some default modulation value set in the config file
            # instead of always toggling back to LoRa
            self.set_modulation(RFM9xModulation.LORA)

        return self._radio

    def get_modulation(self) -> str:
        """Get the current radio modulation.
        :return str: The current radio modulation.
        """
        if self._radio is None:
            return RFM9xModulation.FSK if self._use_fsk.get() else RFM9xModulation.LORA

        if isinstance(self._radio, RFM9xFSK):
            return RFM9xModulation.FSK

        return RFM9xModulation.LORA

    def set_modulation(self, req_modulation: RFM9xModulation) -> None:
        """
        Set the radio modulation.
        Takes effect on the next reboot.
        :param lib.radio.RFM9xModulation req_modulation: The modulation to switch to.
        :return: None
        """
        if self.get_modulation() != req_modulation:
            self._use_fsk.toggle(req_modulation == RFM9xModulation.FSK)
            self._log.info(
                "Radio modulation change requested", modulation=req_modulation
            )
