# Type hinting only
try:
    from pysquared.hardware.load_switchs.factory import ShiftRegister74HC595Factory
    from pysquared.logger import Logger
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
        shift_register_factory: ShiftRegister74HC595Factory,
    ) -> None:
        """
        Initialize the LoadSwitchManager.

        :param Logger logger: Logger instance for logging messages.
        :param ShiftRegister74HC595Factory shift_register_factory: Factory for creating enable pins for the load switches.
        """
        self._log = logger
        self._shift_register_factory = shift_register_factory

        self._enable_pins = self.load_switch_enable_pins
        self._pin_name_map = {}

    @property
    def load_switch_enable_pins(self) -> list:
        """Get the current list of load switch enable pins, creating it if needed.
        :return List of pins: The load switch enable pins.
        """
        if self._enable_pins is None:
            self._enable_pins = self._shift_register_factory.create(self._log)

        return self._enable_pins

    def turn_on(self, switch_id):
        """
        Turn on the load switch with the given ID.
        """
        if switch_id in self._enable_pins:
            self._enable_pins[switch_id].value = False
        else:
            raise ValueError(f"Load switch {switch_id} not found.")

    def turn_off(self, switch_id):
        """
        Turn off the load switch with the given ID.
        """
        if switch_id in self._enable_pins:
            self._enable_pins[switch_id].value = True
        else:
            raise ValueError(f"Load switch {switch_id} not found.")

    def turn_on_all(self):
        """
        Turn on all load switches.
        """
        for pin in self._enable_pins:
            time.sleep(
                0.05
            )  # Adding a small delay to ensure the switches are turned on sequentially
            pin.value = False
        self._log.info("All load switches turned on.")

    def turn_off_all(self):
        """
        Turn off all load switches.
        """
        for pin in self._enable_pins:
            time.sleep(0.05)
            pin.value = True
        self._log.info("All load switches turned off.")

    def assign_names_to_pins(self, pin_names: dict):
        """
        Assign unique names to each load switch enable pin.

        :param pin_names: A dictionary where keys are unique names (str) and values are pin indices (int).
        """
        for name, index in pin_names.items():
            if index < 0 or index >= len(self._enable_pins):
                raise ValueError(f"Invalid pin index {index} for name '{name}'.")
            self._pin_name_map[name] = self._enable_pins[index]

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
