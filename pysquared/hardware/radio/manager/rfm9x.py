from ....config.radio import FSKConfig, LORAConfig
from ....logger import Logger
from ....protos.temperature_sensor import TemperatureSensorProto
from ..modulation import RadioModulation
from .base import BaseRadioManager

try:
    from mocks.adafruit_rfm.rfm9x import RFM9x  # type: ignore
    from mocks.adafruit_rfm.rfm9xfsk import RFM9xFSK  # type: ignore
except ImportError:
    from adafruit_rfm.rfm9x import RFM9x
    from adafruit_rfm.rfm9xfsk import RFM9xFSK

# Type hinting only
try:
    from typing import Any, Optional

    from busio import SPI
    from digitalio import DigitalInOut

    from ....config.radio import RadioConfig
    from ....nvm.flag import Flag
except ImportError:
    pass


class RFM9xManager(BaseRadioManager, TemperatureSensorProto):
    """Manager class implementing RadioProto for RFM9x radios."""

    def __init__(
        self,
        logger: Logger,
        radio_config: RadioConfig,
        use_fsk: Flag,
        spi: SPI,
        chip_select: DigitalInOut,
        reset: DigitalInOut,
    ) -> None:
        """Initialize the manager class and the underlying radio hardware.

        :param Logger logger: Logger instance for logging messages.
        :param RadioConfig radio_config: Radio config object.
        :param Flag use_fsk: Flag to determine whether to use FSK or LoRa mode.
        :param busio.SPI spi: The SPI bus connected to the chip. Ensure SCK, MOSI, and MISO are connected.
        :param ~digitalio.DigitalInOut chip_select: A DigitalInOut object connected to the chip's CS/chip select line.
        :param ~digitalio.DigitalInOut reset: A DigitalInOut object connected to the chip's RST/reset line.

        :raises HardwareInitializationError: If the radio fails to initialize after retries.
        """
        super().__init__(
            logger=logger,
            radio_config=radio_config,
            use_fsk=use_fsk,
            spi=spi,
            chip_select=chip_select,
            reset=reset,
        )

    def _initialize_radio(self, modulation: RadioModulation, **kwargs: Any) -> Any:
        """Initialize the specific RFM9x radio hardware."""
        spi: SPI = kwargs["spi"]
        cs: DigitalInOut = kwargs["chip_select"]
        rst: DigitalInOut = kwargs["reset"]

        if modulation == RadioModulation.FSK:
            radio: RFM9xFSK = self._create_fsk_radio(
                spi,
                cs,
                rst,
                self._radio_config.transmit_frequency,
                self._radio_config.fsk,
            )
        else:
            radio: RFM9x = self._create_lora_radio(
                spi,
                cs,
                rst,
                self._radio_config.transmit_frequency,
                self._radio_config.lora,
            )

        radio.node = self._radio_config.sender_id
        radio.destination = self._radio_config.receiver_id

        return radio

    async def _send_internal(self, payload: bytes) -> bool:
        """Send data using the RFM9x radio."""

        sent = await self._radio.asyncio_send(payload)

        # Assuming send returns bool or similar truthy/falsy
        return bool(sent)

    def _get_current_modulation(self) -> RadioModulation:
        """Get the modulation mode from the initialized RFM9x radio."""
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

    async def receive(self, timeout: Optional[int] = None) -> Optional[bytes]:
        """Receive data from the radio.

        :param int | None timeout: Optional receive timeout in seconds. If None, use the default timeout.
        :return: The received data as bytes, or None if no data was received.
        """
        _timeout = timeout if timeout is not None else self._receive_timeout
        self._log.debug(f"Attempting to receive data with timeout: {_timeout}s")
        try:
            return await self._radio.asyncio_receive(
                keep_listening=True,
                timeout=_timeout,
            )
        except Exception as e:
            self._log.error("Error receiving data", e)
            return None
