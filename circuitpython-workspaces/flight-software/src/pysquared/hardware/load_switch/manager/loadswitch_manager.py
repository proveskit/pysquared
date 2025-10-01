"""This is a generic load switch manager for controlling power to components."""

import time

from digitalio import DigitalInOut

from pysquared.protos.loadswitch import LoadSwitchManagerProto


class LoadSwitchManager(LoadSwitchManagerProto):
    """Manages load switch operations for any component or group of components that
    has an independent load switch for power control.

    This class provides methods to enable, disable, and reset the load switch,
    as well as check its current state. It is designed to work with a digital pin
    that controls the load switch, allowing for high or low enable logic.
    """

    def __init__(self, load_switch_pin: DigitalInOut, enable_high: bool = True) -> None:
        """Initialize the load switch manager.
        :param load_switch_pin: DigitalInOut pin controlling the load switch
        :param enable_high: If True, load switch enables when pin is HIGH. If False, enables when LOW
        """
        self._load_switch_pin = load_switch_pin
        self._enable_pin_value = enable_high
        self._disable_pin_value = not enable_high

    def enable_load(self) -> None:
        """Enables the load switch, allowing power to flow.
        :raises RuntimeError: If the load switch cannot be enabled due to hardware issues
        """
        try:
            self._load_switch_pin.value = self._enable_pin_value
        except Exception as e:
            raise RuntimeError(f"Failed to enable load switch: {e}") from e

    def disable_load(self) -> None:
        """Disables the load switch, cutting power.
        :raises RuntimeError: If the load switch cannot be disabled due to hardware issues
        """
        try:
            self._load_switch_pin.value = self._disable_pin_value
        except Exception as e:
            raise RuntimeError(f"Failed to disable load switch: {e}") from e

    def reset_load(self) -> None:
        """Reset the load switch by momentarily disabling then re-enabling it.
        This method performs a momentary power cycle (0.1s) to reset the load switch
        and any connected components. Errors from underlying drivers are reraised.
        :raises RuntimeError: If the load switch cannot be reset due to hardware issues
        """
        try:
            was_enabled = self.is_enabled
            self.disable_load()
            time.sleep(0.1)
            if was_enabled:
                self.enable_load()
        except Exception as e:
            raise RuntimeError(f"Failed to reset load switch: {e}") from e

    @property
    def is_enabled(self) -> bool:
        """Check if the load switch is currently enabled.
        :raises RuntimeError: If the load switch state cannot be read due to hardware issues
        :return: True if the load switch is enabled, False otherwise
        """
        try:
            pin_value = self._load_switch_pin.value
            return pin_value == self._enable_pin_value
        except Exception as e:
            raise RuntimeError(f"Failed to read load switch state: {e}") from e
