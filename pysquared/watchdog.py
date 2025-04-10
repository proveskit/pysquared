import asyncio
import time

from digitalio import DigitalInOut, Direction

from .hardware.digitalio import initialize_pin

# type hinting only
try:
    from microcontroller import Pin

    from .logger import Logger
except ImportError:
    pass


class Watchdog:
    def __init__(self, logger: Logger, pin: Pin) -> None:
        """Initialize the watchdog timer.
        :param Logger logger: Logger instance for logging messages.
        :param Pin pin: Pin to use for the watchdog timer.

        :raises HardwareInitializationError: If the pin fails to initialize.

        :return: None
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
        """Pet the watchdog to reset the timer."""
        self._log.debug("Petting watchdog")
        self._digital_in_out.value = True
        time.sleep(0.01)
        self._digital_in_out.value = False

    async def async_petting_task(self) -> None:
        "Asynchronous task to continuously pet the watchdog"

        self._log.info("Starting watchdog petting task.")
        while not self._digital_in_out.value:
            self.pet()
            await asyncio.sleep(10.0)
        self._log.info("Stopped watchdog petting task.")
