"""This module provides functions for initializing and configuring SPI and I2C buses
on the PySquared satellite hardware. Includes retry logic for robust hardware
initialization and error handling.
"""

import time

from busio import I2C, SPI
from microcontroller import Pin

from ..logger import Logger
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
    """
    Initializes and configures an SPI bus with the specified parameters.

    Args:
        logger (Logger): Logger instance to log messages.
        clock (Pin): The pin to use for the clock signal.
        mosi (Optional[Pin]): The pin to use for the MOSI signal.
        miso (Optional[Pin]): The pin to use for the MISO signal.
        baudrate (Optional[int]): The baudrate of the SPI bus (default 100000).
        phase (Optional[int]): The phase of the SPI bus (default 0).
        polarity (Optional[int]): The polarity of the SPI bus (default 0).
        bits (Optional[int]): The number of bits per transfer (default 8).

    Raises:
        HardwareInitializationError: If the SPI bus fails to initialize.

    Returns:
        SPI: The initialized SPI object.
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


def _spi_init(
    logger: Logger,
    clock: Pin,
    mosi: Optional[Pin] = None,
    miso: Optional[Pin] = None,
) -> SPI:
    """
    Initializes an SPI bus (without configuration). Includes retry logic.

    Args:
        logger (Logger): Logger instance.
        clock (Pin): Clock pin.
        mosi (Optional[Pin]): MOSI pin.
        miso (Optional[Pin]): MISO pin.

    Raises:
        HardwareInitializationError: If the SPI bus fails to initialize.

    Returns:
        SPI: The initialized SPI object.
    """
    logger.debug("Initializing spi bus")

    try:
        return SPI(clock, mosi, miso)
    except Exception as e:
        raise HardwareInitializationError("Failed to initialize spi bus") from e


def _spi_configure(
    logger: Logger,
    spi: SPI,
    baudrate: Optional[int],
    phase: Optional[int],
    polarity: Optional[int],
    bits: Optional[int],
) -> SPI:
    """
    Configures an SPI bus with the specified parameters.

    Args:
        logger (Logger): Logger instance.
        spi (SPI): SPI bus to configure.
        baudrate (Optional[int]): Baudrate.
        phase (Optional[int]): Phase.
        polarity (Optional[int]): Polarity.
        bits (Optional[int]): Bits per transfer.

    Raises:
        HardwareInitializationError: If the SPI bus cannot be configured.

    Returns:
        SPI: The configured SPI object.
    """
    logger.debug("Configuring spi bus")

    baudrate = baudrate if baudrate else 100000
    phase = phase if phase else 0
    polarity = polarity if polarity else 0
    bits = bits if bits else 8

    # Mirroring how tca multiplexer initializes the i2c bus with lock retries
    tries = 0
    while not spi.try_lock():
        if tries >= 200:
            raise RuntimeError("Unable to lock spi bus.")
        tries += 1
        time.sleep(0)

    try:
        spi.configure(baudrate=baudrate, phase=phase, polarity=polarity, bits=bits)
    except Exception as e:
        raise HardwareInitializationError("Failed to configure spi bus") from e
    finally:
        spi.unlock()

    return spi


def initialize_i2c_bus(
    logger: Logger,
    scl: Pin,
    sda: Pin,
    frequency: Optional[int],
) -> I2C:
    """
    Initializes an I2C bus with the specified parameters. Includes retry logic.

    Args:
        logger (Logger): Logger instance to log messages.
        scl (Pin): The pin to use for the SCL signal.
        sda (Pin): The pin to use for the SDA signal.
        frequency (Optional[int]): The baudrate of the I2C bus (default 100000).

    Raises:
        HardwareInitializationError: If the I2C bus fails to initialize.

    Returns:
        I2C: The initialized I2C object.
    """
    logger.debug("Initializing i2c")

    frequency = frequency if frequency else 100000

    try:
        return I2C(scl, sda, frequency=frequency)
    except Exception as e:
        raise HardwareInitializationError("Failed to initialize i2c bus") from e
