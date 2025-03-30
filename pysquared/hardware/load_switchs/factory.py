from ...logger import Logger
from ..decorators import with_retries
from ..exception import HardwareInitializationError

try:
    from ....lib.adafruit_74hc595 import ShiftRegister74HC595
except ImportError:
    pass

try:
    import digitalio
    from busio import SPI

except ImportError:
    pass


class ShiftRegister74HC595Factory:
    """Factory class for creating ShiftRegister74HC595 instances."""

    def __init__(
        self,
        spi: SPI,
        latch: digitalio.DigitalInOut,
    ) -> None:
        """Initialize the factory class.

        :param busio.SPI spi: The SPI bus connected to the chip. Ensure SCK, MOSI, and MISO are connected.
        :param ~digitalio.DigitalInOut latch: A DigitalInOut object connected to the chip's LATCH line.
        """
        self._spi = spi
        self._latch = latch

    @with_retries(max_attempts=1, initial_delay=1)
    def create(
        self,
        logger: Logger,
    ) -> list[digitalio.DigitalInOut]:
        """Create a ShiftRegister74HC595 instance.

        :param Logger logger: Logger instance for logging messages.

        :return: pins: A list of pins that can now be toggled via the shift register.

        :raises HardwareInitializationError: If the ShiftRegister74HC595 fails to initialize.
        """
        try:
            _shift_register = ShiftRegister74HC595(
                spi=self._spi,
                latch=self._latch,
            )

            pins = [_shift_register.get_pin(n) for n in range(8)]

            for pin in pins:
                pin.direction = digitalio.Direction.OUTPUT
                pin.value = False

            logger.info("ShiftRegister74HC595 initialized successfully")
            return pins

        except Exception as e:
            logger.error(
                "There was an error while initializing the ShiftRegister74HC595", e
            )
            raise HardwareInitializationError("ShiftRegister74HC595") from e
