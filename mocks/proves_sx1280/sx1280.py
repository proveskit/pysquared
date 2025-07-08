"""Mock for the PROVES SX1280 radio module.

This module provides a mock implementation of the PROVES SX1280 radio module for
testing purposes. It allows for simulating the behavior of the SX1280 without the
need for actual hardware.

Usage:
    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    cs = digitalio.DigitalInOut(board.D5)
    reset = digitalio.DigitalInOut(board.D6)
    busy = digitalio.DigitalInOut(board.D7)
    sx1280 = SX1280(spi, cs, reset, busy, 2400.0)
    sx1280.send(b"Hello world!")
"""

from busio import SPI
from digitalio import DigitalInOut


class SX1280:
    """A mock SX1280 radio module."""

    def __init__(
        self,
        spi: SPI,
        cs: DigitalInOut,
        reset: DigitalInOut,
        busy: DigitalInOut,
        frequency: float,
        *,
        debug: bool = False,
        txen: DigitalInOut | bool = False,
        rxen: DigitalInOut | bool = False,
    ) -> None:
        """Initializes the mock SX1280.

        Args:
            spi: The SPI bus to use.
            cs: The chip select pin.
            reset: The reset pin.
            busy: The busy pin.
            frequency: The frequency to operate on.
            debug: Whether to enable debug mode.
            txen: The transmit enable pin.
            rxen: The receive enable pin.
        """
        ...

    def send(
        self,
        data,
        pin=None,
        irq=False,
        header=True,
        ID=0,
        target=0,
        action=0,
        keep_listening=False,
    ):
        """Sends data over the radio."""
        ...

    def receive(self, continuous=True, keep_listening=True) -> bytearray | None:
        """Receives data from the radio."""
        ...
