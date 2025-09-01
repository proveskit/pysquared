"""Mock for the CircuitPython sdcardio module.

This module provides a mock implementation of the CircuitPython sdcardio module
for testing purposes. It allows for simulating the behavior of the sdcardio
module without the need for actual hardware.
"""


class SDCard:
    """A mock class representing an SD card."""

    def __init__(self, spi, cs, baudrate):
        """Initializes the mock SD card.

        Args:
            spi: The SPI bus.
            cs: The chip select pin.
            baudrate: The communication speed.
        """
        pass
