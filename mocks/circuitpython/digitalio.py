"""Mock for the CircuitPython digitalio module.

This module provides a mock implementation of the CircuitPython digitalio module for
testing purposes. It allows for simulating the behavior of the digitalio module without
the need for actual hardware.
"""

from __future__ import annotations

import mocks.circuitpython.microcontroller as microcontroller


class DriveMode:
    """A mock DriveMode."""

    pass


class DigitalInOut:
    """A mock DigitalInOut."""

    def __init__(self, pin: microcontroller.Pin) -> None:
        """Initializes the mock DigitalInOut.

        Args:
            pin: The pin to use.
        """
        ...


class Direction:
    """A mock Direction."""

    pass


class Pull:
    """A mock Pull."""

    pass
