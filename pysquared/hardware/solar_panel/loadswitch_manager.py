"""Load switch manager for solar panel systems."""

import time
from typing import Optional

from digitalio import DigitalInOut

from pysquared.protos.loadswitch import LoadSwitchManagerProto


class LoadSwitchManager(LoadSwitchManagerProto):
    """Manages load switch operations for solar panel systems.

    This class handles enabling, disabling, and resetting load switches that control
    power to solar panel components. It provides a unified interface for load switch
    management across different solar panel configurations.
    """

    def __init__(
        self, load_switch_pin: Optional[DigitalInOut], enable_high: bool = True
    ) -> None:
        """Initialize the load switch manager.

        :param load_switch_pin: DigitalInOut pin controlling the load switch (can be None)
        :param enable_high: If True, load switch enables when pin is HIGH. If False, enables when LOW
        """
        self._load_switch_pin = load_switch_pin
        self._enable_pin_value = enable_high
        self._disable_pin_value = not enable_high
        self._load_enabled = False

    def enable_load(self) -> None:
        """Enable the load switch to provide power to the solar panel.

        :raises RuntimeError: If the load switch cannot be enabled due to hardware issues
        :raises NotImplementedError: If no load switch pin is provided
        """
        if self._load_switch_pin is None:
            raise NotImplementedError("Load switch pin is required")

        try:
            self._load_switch_pin.value = self._enable_pin_value
            self._load_enabled = True
        except Exception as e:
            raise RuntimeError(f"Failed to enable load switch: {e}") from e

    def disable_load(self) -> None:
        """Disable the load switch to cut power to the solar panel.

        :raises RuntimeError: If the load switch cannot be disabled due to hardware issues
        :raises NotImplementedError: If no load switch pin is provided
        """
        if self._load_switch_pin is None:
            raise NotImplementedError("Load switch pin is required")

        try:
            self._load_switch_pin.value = self._disable_pin_value
            self._load_enabled = False
        except Exception as e:
            raise RuntimeError(f"Failed to disable load switch: {e}") from e

    def reset_load(self) -> None:
        """Reset the load switch by momentarily disabling then re-enabling it.

        This method performs a momentary power cycle (0.1s) to reset the load switch
        and any connected components. Errors from underlying drivers are reraised.

        :raises RuntimeError: If the load switch cannot be reset due to hardware issues
        :raises NotImplementedError: If no load switch pin is provided
        """
        if self._load_switch_pin is None:
            raise NotImplementedError("Load switch pin is required")

        try:
            was_enabled = self._load_enabled
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
        if self._load_switch_pin is None:
            return self._load_enabled

        try:
            return self._load_switch_pin.value is self._enable_pin_value
        except Exception as e:
            raise RuntimeError(f"Failed to read load switch state: {e}") from e
