# Type hinting only
try:
    from pysquared.hardware.load_switchs.factory import ShiftRegister74HC595Factory
    from pysquared.logger import Logger
except ImportError:
    pass


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
