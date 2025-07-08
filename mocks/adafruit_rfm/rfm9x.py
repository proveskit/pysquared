"""Mock for the Adafruit RFM9x LoRa radio module.

This module provides a mock implementation of the Adafruit RFM9x LoRa radio module
for testing purposes. It allows for simulating the behavior of the RFM9x without the
need for actual hardware.

Usage:
    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    cs = digitalio.DigitalInOut(board.D5)
    reset = digitalio.DigitalInOut(board.D6)
    rfm9x = RFM9x(spi, cs, reset, 433.0)
    rfm9x.send(b"Hello world!")
"""

from .rfm_common import RFMSPI

# Type hinting only
try:
    from typing import Literal
except ImportError:
    pass


class RFM9x(RFMSPI):
    """A mock RFM9x LoRa radio module."""

    ack_delay: float | None = None
    enable_crc: bool
    spreading_factor: Literal[6, 7, 8, 9, 10, 11, 12]
    tx_power: int
    preamble_length: int
    low_datarate_optimize: int
    max_packet_length: int
    last_rssi: float
    tx_power: int
    radiohead: bool

    def __init__(self, spi, cs, reset, frequency) -> None:
        """Initializes the mock RFM9x.

        Args:
            spi: The SPI bus to use.
            cs: The chip select pin.
            reset: The reset pin.
            frequency: The frequency to operate on.
        """
        ...
