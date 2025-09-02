"""Mock for the CircuitPython busio module.

This module provides a mock implementation of the CircuitPython busio module for
testing purposes. It allows for simulating the behavior of the busio module without
the need for actual hardware.
"""

from typing import Optional

import microcontroller


class SPI:
    """A mock SPI bus."""

    def __init__(
        self,
        clock: microcontroller.Pin,
        MOSI: Optional[microcontroller.Pin] = None,
        MISO: Optional[microcontroller.Pin] = None,
        half_duplex: bool = False,
    ) -> None:
        """Initializes the mock SPI bus.

        Args:
            clock: The clock pin.
            MOSI: The MOSI pin.
            MISO: The MISO pin.
            half_duplex: Whether to use half-duplex mode.
        """
        ...
