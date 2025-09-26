"""This module provides the Watchdog class for managing the hardware watchdog timer
on the PySquared satellite. The watchdog helps ensure system reliability by
requiring periodic "petting" to prevent system resets.
"""

import time

from digitalio import DigitalInOut, Direction
from microcontroller import Pin

from .hardware.digitalio import initialize_pin
from .logger import Logger


class Watchdog:
    """
    Watchdog class for managing the hardware watchdog timer.

    Attributes:
        _log (Logger): Logger instance for logging messages.
        _digital_in_out (DigitalInOut): Digital output for controlling the watchdog pin.
    """

    def __init__(self, logger: Logger, pin: Pin) -> None:
        """
        Initializes the Watchdog timer.

        Args:
            logger (Logger): Logger instance for logging messages.
            pin (Pin): Pin to use for the watchdog timer.

        Raises:
            HardwareInitializationError: If the pin fails to initialize.
        """
        self._log = logger

        self._log.debug("Initializing watchdog", pin=pin)

        self._digital_in_out: DigitalInOut = initialize_pin(
            logger,
            pin,
            Direction.OUTPUT,
            False,
        )

    def pet(self) -> None:
        """
        Pets (resets) the watchdog timer to prevent system reset.
        """
        self._log.debug("Petting watchdog")
        self._digital_in_out.value = True
        time.sleep(0.01)
        self._digital_in_out.value = False
