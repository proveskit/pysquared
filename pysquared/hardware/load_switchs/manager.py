# Type hinting only
try:
    from ...logger import Logger
except ImportError:
    pass

from lib.adafruit_74hc595 import ShiftRegister74HC595

from ..decorators import with_retries
from ..exception import HardwareInitializationError

try:
    import digitalio
    from busio import SPI
except ImportError:
    pass

import time


class LoadSwitchManager:
    """
    This class manages the load switches for the Pysquared hardware.
    It provides methods to turn on and off the load switches.
    """

    def __init__(
        self,
        logger: Logger,
        spi: SPI,
        latch: digitalio.DigitalInOut,
    ) -> None:
        """
        Initialize the LoadSwitchManager.

        :param Logger logger: Logger instance for logging messages.
        :param ShiftRegister74HC595Factory shift_register_factory: Factory for creating enable pins for the load switches.
        """
        self._log = logger
        self._spi = spi
        self._latch = latch

        # Initialize _enable_pins to None
        self._enable_pins = self.create(logger)
        self._pin_name_map = {}

    @with_retries(max_attempts=1, initial_delay=1)
    def create(
        self,
        logger: Logger,
    ) -> list[digitalio.DigitalInOut]:
        """Create a ShiftRegister74HC595 instance.

        :param Logger logger: Logger instance for logging messages.

        :return: pins: A list of pins that can now be toggled via the shift register.

        :raises HardwareInitializationError: If the ShiftRegister74HC595 fails to initialize.
        """
        try:
            _shift_register = ShiftRegister74HC595(
                spi=self._spi,
                latch=self._latch,
            )

            pins = [_shift_register.get_pin(n) for n in range(8)]

            for pin in pins:
                pin.direction = digitalio.Direction.OUTPUT
                pin.value = False

            logger.info("ShiftRegister74HC595 initialized successfully")
            return pins

        except Exception as e:
            logger.error(
                "There was an error while initializing the ShiftRegister74HC595", e
            )
            raise HardwareInitializationError("ShiftRegister74HC595") from e

    def turn_on(self, switch_id):
        """
        Turn on the load switch with the given ID.
        """
        enable_pins = self._enable_pins
        if switch_id in enable_pins:
            enable_pins[switch_id].value = False
        else:
            raise ValueError(f"Load switch {switch_id} not found.")

    def turn_off(self, switch_id):
        """
        Turn off the load switch with the given ID.
        """
        enable_pins = self._enable_pins
        if switch_id in enable_pins:
            enable_pins[switch_id].value = True
        else:
            raise ValueError(f"Load switch {switch_id} not found.")

    def turn_on_all(self):
        """
        Turn on all load switches.
        """
        for pin in self._enable_pins:  # Use the property to ensure initialization
            time.sleep(
                0.05
            )  # Adding a small delay to ensure the switches are turned on sequentially
            pin.value = False
        self._log.info("All load switches turned on.")

    def turn_off_all(self):
        """
        Turn off all load switches.
        """
        for pin in self._enable_pins:  # Use the property to ensure initialization
            time.sleep(0.05)
            pin.value = True
        self._log.info("All load switches turned off.")

    def assign_names_to_pins(self, pin_names: dict):
        """
        Assign unique names to each load switch enable pin.

        :param pin_names: A dictionary where keys are unique names (str) and values are pin indices (int).
        """
        enable_pins = self._enable_pins  # Use the property to ensure initialization
        for name, index in pin_names.items():
            if index < 0 or index >= len(enable_pins):
                raise ValueError(f"Invalid pin index {index} for name '{name}'.")
            self._pin_name_map[name] = enable_pins[index]

        self._log.debug(
            "Assigned names to load switch pins",
            pin_names=self._pin_name_map,
        )

    def turn_on_by_name(self, name: str):
        """
        Turn on the load switch with the given name.

        :param name: The unique name of the load switch.
        """
        if name in self._pin_name_map:
            self._pin_name_map[name].value = False
        else:
            raise ValueError(f"Load switch with name '{name}' not found.")

    def turn_off_by_name(self, name: str):
        """
        Turn off the load switch with the given name.

        :param name: The unique name of the load switch.
        """
        if name in self._pin_name_map:
            self._pin_name_map[name].value = True
        else:
            raise ValueError(f"Load switch with name '{name}' not found.")
