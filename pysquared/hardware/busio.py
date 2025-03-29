from busio import I2C, SPI
from microcontroller import Pin

from ..logger import Logger
from .decorators import with_retries
from .exception import HardwareInitializationError

try:
    from typing import Optional
except ImportError:
    pass


def initialize_spi_bus(
    logger: Logger,
    clock: Pin,
    mosi: Optional[Pin] = None,
    miso: Optional[Pin] = None,
    baudrate: Optional[int] = 100000,
    phase: Optional[int] = 0,
    polarity: Optional[int] = 0,
    bits: Optional[int] = 8,
) -> SPI:
    """Initializes a SPI bus

    :param Logger logger: The logger instance to log messages.
    :param Pin clock: The pin to use for the clock signal.
    :param Pin mosi: The pin to use for the MOSI signal.
    :param Pin miso: The pin to use for the MISO signal.
    :param int baudrate: The baudrate of the SPI bus (default is 100000).
    :param int phase: The phase of the SPI bus (default is 0).
    :param int polarity: The polarity of the SPI bus (default is 0).
    :param int bits: The number of bits per transfer (default is 8).

    :raises HardwareInitializationError: If the SPI bus fails to initialize.

    :return ~busio.SPI: The initialized SPI object.
    """
    try:
        return _spi_configure(
            logger,
            _spi_init(logger, clock, mosi, miso),
            baudrate,
            phase,
            polarity,
            bits,
        )
    except Exception as e:
        raise HardwareInitializationError(
            "Failed to initialize and configure spi bus"
        ) from e


@with_retries(max_attempts=3, initial_delay=1)
def _spi_init(
    logger: Logger,
    clock: Pin,
    mosi: Optional[Pin] = None,
    miso: Optional[Pin] = None,
) -> SPI:
    """Initializes a SPI bus, does not configure

    :param Logger logger: The logger instance to log messages.
    :param Pin clock: The pin to use for the clock signal.
    :param Pin mosi: The pin to use for the MOSI signal.
    :param Pin miso: The pin to use for the MISO signal.

    :raises HardwareInitializationError: If the SPI bus fails to initialize.

    :return ~busio.SPI: The initialized SPI object.
    """
    logger.debug("Initializing spi bus")

    try:
        return SPI(clock, mosi, miso)
    except Exception as e:
        raise HardwareInitializationError("Failed to initialize spi bus") from e


@with_retries(max_attempts=3, initial_delay=1)
def _spi_configure(
    logger: Logger,
    spi: SPI,
    baudrate: Optional[int] = 100000,
    phase: Optional[int] = 0,
    polarity: Optional[int] = 0,
    bits: Optional[int] = 8,
) -> SPI:
    """Configure SPI bus

    :param Logger logger: The logger instance to log messages.
    :param ~busio.SPI: SPI bus to configure
    :param int baudrate: The baudrate of the SPI bus (default is 100000).
    :param int phase: The phase of the SPI bus (default is 0).
    :param int polarity: The polarity of the SPI bus (default is 0).
    :param int bits: The number of bits per transfer (default is 8).

    :raises HardwareInitializationError: If the SPI bus cannot be configured.

    :return ~busio.SPI: The initialized SPI object.
    """
    logger.debug("Configuring spi bus")

    try:
        if not spi.try_lock():
            raise RuntimeError("Unable to lock spi bus")

        spi.configure(baudrate, phase, polarity, bits)
        spi.unlock()
        return spi
    except Exception as e:
        raise HardwareInitializationError("Failed to configure spi bus") from e


@with_retries(max_attempts=3, initial_delay=1)
def initialize_i2c_bus(
    logger: Logger,
    scl: Pin,
    sda: Pin = None,
    frequency: Optional[int] = 100000,
) -> I2C:
    """Initializes a I2C bus"

    :param Logger logger: The logger instance to log messages.
    :param Pin scl: The pin to use for the scl signal.
    :param Pin sda: The pin to use for the sda signal.
    :param int frequency: The baudrate of the I2C bus (default is 100000).

    :raises HardwareInitializationError: If the I2C bus fails to initialize.

    :return ~busio.I2C: The initialized I2C object.
    """
    logger.debug("Initializing i2c")

    try:
        return I2C(scl, sda, frequency=frequency)
    except Exception as e:
        raise HardwareInitializationError("Failed to initialize spi") from e
