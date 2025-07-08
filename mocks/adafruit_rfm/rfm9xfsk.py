"""Mock for the Adafruit RFM9xFSK radio module.

This module provides a mock implementation of the Adafruit RFM9xFSK radio module
for testing purposes. It allows for simulating the behavior of the RFM9xFSK without the
need for actual hardware.

Usage:
    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    cs = digitalio.DigitalInOut(board.D5)
    reset = digitalio.DigitalInOut(board.D6)
    rfm9xfsk = RFM9xFSK(spi, cs, reset, 433.0)
    rfm9xfsk.send(b"Hello world!")
"""

from .rfm_common import RFMSPI


class RFM9xFSK(RFMSPI):
    """A mock RFM9xFSK radio module."""

    modulation_type: int
    fsk_broadcast_address: int
    fsk_node_address: int
    max_packet_length: int
    last_rssi: float
    tx_power: int
    radiohead: bool

    def __init__(self, spi, cs, reset, frequency) -> None:
        """Initializes the mock RFM9xFSK.

        Args:
            spi: The SPI bus to use.
            cs: The chip select pin.
            reset: The reset pin.
            frequency: The frequency to operate on.
        """
        ...
