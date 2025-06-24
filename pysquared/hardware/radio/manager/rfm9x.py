from busio import SPI
from digitalio import DigitalInOut

try:
    from mocks.adafruit_rfm.rfm9x import RFM9x
    from mocks.adafruit_rfm.rfm9xfsk import RFM9xFSK
except ImportError:
    from adafruit_rfm.rfm9x import RFM9x
    from adafruit_rfm.rfm9xfsk import RFM9xFSK

from ....config.radio import FSKConfig, LORAConfig, RadioConfig
from ....logger import Logger
from ....protos.temperature_sensor import TemperatureSensorProto
from ..modulation import FSK, LoRa, RadioModulation
from .base import BaseRadioManager

# Type hinting only
try:
    from typing import Optional, Type
except ImportError:
    pass


class RFM9xManager(BaseRadioManager, TemperatureSensorProto):
    """Manager class implementing RadioProto for RFM9x radios."""

    _radio: RFM9xFSK | RFM9x

    def __init__(
        self,
        logger: Logger,
        radio_config: RadioConfig,
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
        self._spi = spi
        self._chip_select = chip_select
        self._reset = reset

        super().__init__(
            logger=logger,
            radio_config=radio_config,
        )

    def _initialize_radio(self, modulation: Type[RadioModulation]) -> None:
        """Initialize the specific RFM9x radio hardware."""

        if modulation == FSK:
            self._radio = self._create_fsk_radio(
                self._spi,
                self._chip_select,
                self._reset,
                self._radio_config.transmit_frequency,
                self._radio_config.fsk,
            )
        else:
            self._radio = self._create_lora_radio(
                self._spi,
                self._chip_select,
                self._reset,
                self._radio_config.transmit_frequency,
                self._radio_config.lora,
            )

        self._radio.radiohead = False

    def _send_internal(self, data: bytes) -> bool:
        """Send data using the RFM9x radio."""
        return bool(self._radio.send(data))

    def modify_config(self, key: str, value) -> None:
        """Modify a specific radio configuration parameter.

        :param str key: The configuration parameter key to modify.
        :param object value: The new value to set for the parameter.
        :raises ValueError: If the key is not recognized or invalid for the current radio type.
        """
        self._radio_config.validate(key, value)

        # Handle FSK-specific parameters
        if isinstance(self._radio, RFM9xFSK):
            if key == "broadcast_address":
                self._radio.fsk_broadcast_address = value
            elif key == "node_address":
                self._radio.fsk_node_address = value
            elif key == "modulation_type":
                self._radio.modulation_type = value

        # Handle LoRa-specific parameters
        elif isinstance(self._radio, RFM9x):
            if key == "ack_delay":
                self._radio.ack_delay = value
            elif key == "cyclic_redundancy_check":
                self._radio.enable_crc = value
            elif key == "spreading_factor":
                self._radio.spreading_factor = value
                if value > 9:
                    self._radio.preamble_length = value
                else:
                    self._radio.preamble_length = 8  # Default preamble length
            elif key == "transmit_power":
                self._radio.tx_power = value

    def get_modulation(self) -> Type[RadioModulation]:
        """Get the modulation mode from the initialized RFM9x radio."""
        return FSK if self._radio.__class__.__name__ == "RFM9xFSK" else LoRa

    def get_temperature(self) -> float:
        """Get the temperature reading from the radio sensor."""
        try:
            raw_temp = self._radio.read_u8(0x5B)
            temp = raw_temp & 0x7F  # Mask out sign bit
            if (raw_temp & 0x80) == 0x80:  # Check sign bit (if 1, it's negative)
                # Perform two's complement for negative numbers
                # Invert bits, add 1, mask to 8 bits
                temp = -((~raw_temp + 1) & 0xFF)

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
        radio.spreading_factor = lora_config.spreading_factor
        radio.tx_power = lora_config.transmit_power

        if radio.spreading_factor > 9:
            radio.preamble_length = radio.spreading_factor

        return radio

    def receive(self, timeout: Optional[int] = None) -> bytes | None:
        """Receive data from the radio.

        :param int | None timeout: Optional receive timeout in seconds. If None, use the default timeout.
        :return: The received data as bytes, or None if no data was received.
        """
        _timeout = timeout if timeout is not None else self._receive_timeout
        self._log.debug(f"Attempting to receive data with timeout: {_timeout}s")
        try:
            msg: bytearray | None = self._radio.receive(
                keep_listening=True,
                timeout=_timeout,
            )

            if msg is None:
                self._log.debug("No message received")
                return None

            return bytes(msg)
        except Exception as e:
            self._log.error("Error receiving data", e)
            return None

    def get_max_packet_size(self) -> int:
        # Max packet lenght minus 4 bytes for radiohead compatibility enforced by the RFM9x library
        # https://github.com/adafruit/Adafruit_CircuitPython_RFM/issues/14
        return self._radio.max_packet_length - 4

    def get_rssi(self) -> int:
        """Get the RSSI of the last received packet."""
        # library reads rssi from an unsigned byte, so we know it's in the range 0-255
        # it is safe to cast it to int
        return int(self._radio.last_rssi)
