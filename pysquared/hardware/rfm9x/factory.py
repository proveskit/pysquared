from ...config.radio import FSKConfig, LORAConfig, RadioConfig
from ...logger import Logger
from ..decorators import with_retries
from ..exception import HardwareInitializationError
from .modulation import RFM9xModulation

try:
    from mocks.circuitpython.adafruit_rfm.rfm9x import RFM9x  # type: ignore
    from mocks.circuitpython.adafruit_rfm.rfm9xfsk import RFM9xFSK  # type: ignore
except ImportError:
    from adafruit_rfm.rfm9x import RFM9x
    from adafruit_rfm.rfm9xfsk import RFM9xFSK

# Type hinting only
try:
    from adafruit_rfm.rfm_common import RFMSPI
    from busio import SPI
    from digitalio import DigitalInOut
except ImportError:
    pass


class RFM9xFactory:
    """Factory class for creating RFM9x radio instances.
    The purpose of the factory class is to hide the complexity of radio initialization from the caller.
    Specifically we should try to keep adafruit_rfm to only this factory class with the exception of the RFMSPI class.
    """

    def __init__(
        self,
        spi: SPI,
        chip_select: DigitalInOut,
        reset: DigitalInOut,
        radio_config: RadioConfig,
    ) -> None:
        """Initialize the factory class.

        :param busio.SPI spi: The SPI bus connected to the chip. Ensure SCK, MOSI, and MISO are connected.
        :param ~digitalio.DigitalInOut cs: A DigitalInOut object connected to the chip's CS/chip select line.
        :param ~digitalio.DigitalInOut reset: A DigitalInOut object connected to the chip's RST/reset line.
        :param RadioConfig radio_config: Radio config object.
        """
        self._spi = spi
        self._chip_select = chip_select
        self._reset = reset
        self._radio_config = radio_config

    @with_retries(max_attempts=3, initial_delay=1)
    def create(
        self,
        logger: Logger,
        modulation: RFM9xModulation,
    ) -> RFMSPI:
        """Create a RFM9x radio instance.

        :param Logger logger: Logger instance for logging messages.
        :param RFM9xModulation modulation: Either FSK or LoRa.

        :raises HardwareInitializationError: If the radio fails to initialize.

        :return An instance of the RFMSPI class, either RFM9xFSK or RFM9x based on the mode.
        """
        logger.debug(message="Initializing radio", modulation=modulation)

        try:
            if modulation == RFM9xModulation.FSK:
                radio: RFMSPI = self.create_fsk_radio(
                    self._spi,
                    self._chip_select,
                    self._reset,
                    self._radio_config.transmit_frequency,
                    self._radio_config.fsk,
                )
            else:
                radio: RFMSPI = self.create_lora_radio(
                    self._spi,
                    self._chip_select,
                    self._reset,
                    self._radio_config.transmit_frequency,
                    self._radio_config.lora,
                )

            radio.node = self._radio_config.sender_id
            radio.destination = self._radio_config.receiver_id

            return radio
        except Exception as e:
            raise HardwareInitializationError(
                "Failed to initialize radio with modulation {modulation}"
            ) from e

    @staticmethod
    def create_fsk_radio(
        spi: SPI,
        cs: DigitalInOut,
        rst: DigitalInOut,
        transmit_frequency: int,
        fsk_config: FSKConfig,
    ) -> RFMSPI:
        """Create a FSK radio instance.

        :param busio.SPI spi: The SPI bus connected to the chip. Ensure SCK, MOSI, and MISO are connected.
        :param ~digitalio.DigitalInOut cs: A DigitalInOut object connected to the chip's CS/chip select line.
        :param ~digitalio.DigitalInOut reset: A DigitalInOut object connected to the chip's RST/reset line.
        :param int transmit_frequency: Frequency at which the radio will transmit.
        :param FSKConfig config: FSK config object.

        :return An instance of :class:`~adafruit_rfm.rfm9xfsk.RFM9xFSK`.
        """
        radio: RFM9xFSK = RFM9xFSK(
            spi,
            cs,
            rst,
            transmit_frequency,
        )

        radio.fsk_broadcast_address = fsk_config.broadcast_address
        radio.fsk_node_address = fsk_config.node_address
        radio.modulation_type = fsk_config.modulation_type

        return radio

    @staticmethod
    def create_lora_radio(
        spi: SPI,
        cs: DigitalInOut,
        rst: DigitalInOut,
        transmit_frequency: int,
        lora_config: LORAConfig,
    ) -> RFMSPI:
        """Create a LoRa radio instance.

        :param busio.SPI spi: The SPI bus connected to the chip. Ensure SCK, MOSI, and MISO are connected.
        :param ~digitalio.DigitalInOut cs: A DigitalInOut object connected to the chip's CS/chip select line.
        :param ~digitalio.DigitalInOut reset: A DigitalInOut object connected to the chip's RST/reset line.
        :param int transmit_frequency: Frequency at which the radio will transmit.
        :param LORAConfig config: LoRa config object.

        :return An instance of the RFM9x class.
        """
        radio: RFM9x = RFM9x(
            spi,
            cs,
            rst,
            transmit_frequency,
        )

        radio.ack_delay = lora_config.ack_delay
        radio.enable_crc = lora_config.cyclic_redundancy_check
        radio.max_output = lora_config.max_output
        radio.spreading_factor = lora_config.spreading_factor
        radio.tx_power = lora_config.transmit_power

        if radio.spreading_factor > 9:
            radio.preamble_length = radio.spreading_factor
            radio.low_datarate_optimize = 1

        return radio

    @staticmethod
    def get_instance_modulation(radio: RFMSPI) -> RFM9xModulation:
        """Determine the radio modulation in use.

        :param RFMSPI radio: The radio instance to check.

        :return The modulation in use.
        """
        if isinstance(radio, RFM9xFSK):
            return RFM9xModulation.FSK

        return RFM9xModulation.LORA
