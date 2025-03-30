from ....config.radio import FSKConfig, LORAConfig, RadioConfig
from ....logger import Logger
from ....nvm.flag import Flag
from ....protos.radio import RadioProto
from ....protos.temperature_sensor import TemperatureSensorProto
from ...decorators import with_retries
from ...exception import HardwareInitializationError
from ..modulation import RadioModulation

try:
    from mocks.adafruit_rfm.rfm9x import RFM9x  # type: ignore
    from mocks.adafruit_rfm.rfm9xfsk import RFM9xFSK  # type: ignore
except ImportError:
    from lib.adafruit_rfm.rfm9x import RFM9x
    from lib.adafruit_rfm.rfm9xfsk import RFM9xFSK

# Type hinting only
try:
    from typing import Any

    from busio import SPI
    from digitalio import DigitalInOut
except ImportError:
    pass


class RFM9xManager(RadioProto, TemperatureSensorProto):
    """Manager class implementing RadioProto for RFM9x radios.
    This class handles the initialization and interaction with RFM9x FSK or LoRa radios.
    """

    @with_retries(max_attempts=3, initial_delay=1)
    def __init__(
        self,
        logger: Logger,
        spi: SPI,
        chip_select: DigitalInOut,
        reset: DigitalInOut,
        radio_config: RadioConfig,
        use_fsk: Flag,
        is_licensed: bool,
    ) -> None:
        """Initialize the manager class and the underlying radio hardware.

        :param Logger logger: Logger instance for logging messages.
        :param busio.SPI spi: The SPI bus connected to the chip. Ensure SCK, MOSI, and MISO are connected.
        :param ~digitalio.DigitalInOut cs: A DigitalInOut object connected to the chip's CS/chip select line.
        :param ~digitalio.DigitalInOut reset: A DigitalInOut object connected to the chip's RST/reset line.
        :param RadioConfig radio_config: Radio config object.
        :param Flag use_fsk: Flag to determine whether to use FSK or LoRa mode.
        :param bool is_licensed: Flag indicating if radio operation is licensed.

        :raises HardwareInitializationError: If the radio fails to initialize after retries.
        """
        self._log = logger
        self._spi = spi
        self._chip_select = chip_select
        self._reset = reset
        self._radio_config = radio_config
        self._use_fsk = use_fsk
        self._is_licensed = is_licensed

        initial_modulation = self.get_modulation()

        self._log.debug(message="Initializing radio", modulation=initial_modulation)

        try:
            if initial_modulation == RadioModulation.FSK:
                radio: RFM9xFSK = self._create_fsk_radio(
                    self._spi,
                    self._chip_select,
                    self._reset,
                    self._radio_config.transmit_frequency,
                    self._radio_config.fsk,
                )
            else:
                radio: RFM9x = self._create_lora_radio(
                    self._spi,
                    self._chip_select,
                    self._reset,
                    self._radio_config.transmit_frequency,
                    self._radio_config.lora,
                )

            radio.node = self._radio_config.sender_id
            radio.destination = self._radio_config.receiver_id

            self._radio: RFM9x | RFM9x = radio

        except Exception as e:
            raise HardwareInitializationError(
                f"Failed to initialize radio with modulation {initial_modulation}"
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

            sent = self._radio.send(
                payload
            )  # Assuming send returns bool or similar truthy/falsy
            self._log.info("Radio message sent", success=bool(sent), len=len(payload))
            return bool(sent)
        except Exception as e:
            self._log.error("Error sending radio message", e)
            return False

    def set_modulation(self, req_modulation: RadioModulation) -> None:
        """Request a change in the radio modulation mode (takes effect on next init)."""
        current_modulation = self.get_modulation()
        if current_modulation != req_modulation:
            self._use_fsk.toggle(req_modulation == RadioModulation.FSK)
            self._log.info(
                "Radio modulation change requested for next init",
                requested=req_modulation,
                current=current_modulation,
            )

    def get_modulation(self) -> RadioModulation:
        """Get the currently configured radio modulation mode."""
        if self._radio is None:
            return RadioModulation.FSK if self._use_fsk.get() else RadioModulation.LORA

        if isinstance(self._radio, RFM9xFSK):
            return RadioModulation.FSK
        elif isinstance(self._radio, RFM9x):
            return RadioModulation.LORA
        else:
            raise TypeError(f"Unknown radio instance type: {type(self._radio)}")

    def get_temperature(self) -> float:
        """Get the temperature reading from the radio sensor."""
        try:
            raw_temp = self._radio.read_u8(0x5B)
            temp = raw_temp & 0x7F  # Mask out sign bit
            if (raw_temp & 0x80) == 0x80:  # Check sign bit (if 1, it's negative)
                # Perform two's complement for negative numbers
                # Invert bits, add 1, mask to 8 bits
                temp = -((~temp + 1) & 0xFF)

            # This prescaler seems specific and might need verification/context.
            prescaler = 143.0  # Use float for calculation
            result = float(temp) + prescaler
            self._log.debug("Radio temperature read", temp=result)
            return result
        except AttributeError:
            self._log.error("Radio instance does not support read_u8 for temperature.")
            return float("nan")
        except Exception as e:
            self._log.error("Error reading radio temperature", e)
            return float("nan")

    @staticmethod
    def _create_fsk_radio(
        spi: SPI,
        cs: DigitalInOut,
        rst: DigitalInOut,
        transmit_frequency: int,
        fsk_config: FSKConfig,
    ) -> RFM9xFSK:
        """Create a FSK radio instance."""
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
    def _create_lora_radio(
        spi: SPI,
        cs: DigitalInOut,
        rst: DigitalInOut,
        transmit_frequency: int,
        lora_config: LORAConfig,
    ) -> RFM9x:
        """Create a LoRa radio instance."""
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
