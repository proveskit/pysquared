"""
Load Switch Manager
==================

This module provides a manager for controlling load switches on PySquared satellite hardware.
Load switches are used to control power to various subsystems and components.

Usage Example:

from lib.pysquared.hardware.load_switch.manager.load_switch import LoadSwitchManager
from digitalio import DigitalInOut
import board

# Define your load switches with custom names
load_switches = {
    "radio": DigitalInOut(board.RADIO_ENABLE),
    "imu": DigitalInOut(board.IMU_ENABLE),
    "magnetometer": DigitalInOut(board.MAG_ENABLE),
    "camera": DigitalInOut(board.CAMERA_ENABLE),
}

# Initialize the manager
load_switch_manager = LoadSwitchManager(logger, load_switches, enable_logic=True)

# Control individual switches
load_switch_manager.turn_on("radio")
load_switch_manager.turn_off("camera")

# Control all switches
load_switch_manager.turn_all_off()
load_switch_manager.turn_all_on()

# Check states
radio_state = load_switch_manager.get_switch_state("radio")
all_states = load_switch_manager.get_all_states()
"""

from typing import Dict

from digitalio import DigitalInOut

from ....logger import Logger
from ....protos.load_switch import LoadSwitchProto
from ...decorators import with_retries
from ...exception import HardwareInitializationError


class LoadSwitchManager(LoadSwitchProto):
    """Class for managing load switch ports."""

    def __init__(
        self,
        logger: Logger,
        load_switches: Dict[str, DigitalInOut],
        enable_logic: bool = True,
    ) -> None:
        """
        Initializes the load switch manager class.

        :param Logger logger: Logger instance for logging messages.
        :param Dict[str, DigitalInOut] load_switches: Dictionary mapping switch names to their DigitalInOut pins.
        :param bool enable_logic: Boolean defining whether the load switches are enabled when True or False. Defaults to `True`.
        """
        self._log: Logger = logger
        self._enable_logic: bool = enable_logic
        self._load_switches: Dict[str, DigitalInOut] = load_switches

        # Initialize all switches to the off state
        self._initialize_switches()

        # Public dictionary to track switch states
        self.switch_states: Dict[str, bool] = {
            name: False for name in load_switches.keys()
        }

    def turn_on(self, switch_name: str) -> bool:
        """Turn on a specific load switch.

        :param str switch_name: The name of the load switch to turn on.

        :return: A Boolean indicating whether the operation was successful
        :rtype: bool

        :raises Exception: If there is an error toggling the load switch.
        """
        if switch_name not in self._load_switches:
            self._log.warning(f"Load switch '{switch_name}' not found")
            return False

        try:
            self._load_switches[switch_name].value = self._enable_logic
            self.switch_states[switch_name] = True
            self._log.debug(f"Turned on load switch: {switch_name}")
            return True
        except Exception as e:
            self._log.error(f"Failed to turn on load switch '{switch_name}'", err=e)
            return False

    def turn_off(self, switch_name: str) -> bool:
        """Turn off a specific load switch.

        :param str switch_name: The name of the load switch to turn off.

        :return: A Boolean indicating whether the operation was successful
        :rtype: bool

        :raises Exception: If there is an error toggling the load switch.
        """
        if switch_name not in self._load_switches:
            self._log.warning(f"Load switch '{switch_name}' not found")
            return False

        try:
            self._load_switches[switch_name].value = not self._enable_logic
            self.switch_states[switch_name] = False
            self._log.debug(f"Turned off load switch: {switch_name}")
            return True
        except Exception as e:
            self._log.error(f"Failed to turn off load switch '{switch_name}'", err=e)
            return False

    def turn_all_on(self) -> bool:
        """Turn on all load switches.

        :return: A Boolean indicating whether the operation was successful
        :rtype: bool

        :raises Exception: If there is an error toggling the load switches.
        """
        success = True
        for switch_name in self._load_switches.keys():
            if not self.turn_on(switch_name):
                success = False

        if success:
            self._log.info("Turned on all load switches")
        else:
            self._log.warning("Some load switches failed to turn on")

        return success

    def turn_all_off(self) -> bool:
        """Turn off all load switches.

        :return: A Boolean indicating whether the operation was successful
        :rtype: bool

        :raises Exception: If there is an error toggling the load switches.
        """
        success = True
        for switch_name in self._load_switches.keys():
            if not self.turn_off(switch_name):
                success = False

        if success:
            self._log.info("Turned off all load switches")
        else:
            self._log.warning("Some load switches failed to turn off")

        return success

    def get_switch_state(self, switch_name: str) -> bool | None:
        """Get the current state of a specific load switch.

        :param str switch_name: The name of the load switch to check.

        :return: The current state of the load switch (True for on, False for off) or None if not found
        :rtype: bool | None
        """
        if switch_name not in self.switch_states:
            self._log.warning(f"Load switch '{switch_name}' not found")
            return None

        return self.switch_states[switch_name]

    def get_all_states(self) -> Dict[str, bool]:
        """Get the current state of all load switches.

        :return: A dictionary mapping switch names to their current states
        :rtype: Dict[str, bool]
        """
        return self.switch_states.copy()

    @with_retries(max_attempts=3, initial_delay=0.1)
    def _initialize_switches(self) -> None:
        """Initialize all load switches to the off state.

        :raises HardwareInitializationError: If any switch fails to initialize.
        """
        try:
            for switch_name, switch_pin in self._load_switches.items():
                # Set all switches to the off state initially
                switch_pin.value = not self._enable_logic
                self._log.debug(f"Initialized load switch '{switch_name}' to off state")
        except Exception as e:
            raise HardwareInitializationError(
                "Failed to initialize load switches"
            ) from e

    def add_switch(self, switch_name: str, switch_pin: DigitalInOut) -> bool:
        """Add a new load switch to the manager.

        :param str switch_name: The name for the new load switch.
        :param DigitalInOut switch_pin: The DigitalInOut pin for the new switch.

        :return: A Boolean indicating whether the operation was successful
        :rtype: bool
        """
        if switch_name in self._load_switches:
            self._log.warning(f"Load switch '{switch_name}' already exists")
            return False

        try:
            # Initialize the new switch to off state
            switch_pin.value = not self._enable_logic

            # Add to internal dictionaries
            self._load_switches[switch_name] = switch_pin
            self.switch_states[switch_name] = False

            self._log.debug(f"Added new load switch: {switch_name}")
            return True
        except Exception as e:
            self._log.error(f"Failed to add load switch '{switch_name}'", err=e)
            return False

    def remove_switch(self, switch_name: str) -> bool:
        """Remove a load switch from the manager.

        :param str switch_name: The name of the load switch to remove.

        :return: A Boolean indicating whether the operation was successful
        :rtype: bool
        """
        if switch_name not in self._load_switches:
            self._log.warning(f"Load switch '{switch_name}' not found")
            return False

        try:
            # Turn off the switch before removing
            self.turn_off(switch_name)

            # Remove from internal dictionaries
            del self._load_switches[switch_name]
            del self.switch_states[switch_name]

            self._log.debug(f"Removed load switch: {switch_name}")
            return True
        except Exception as e:
            self._log.error(f"Failed to remove load switch '{switch_name}'", err=e)
            return False

    def get_switch_names(self) -> list[str]:
        """Get a list of all load switch names.

        :return: A list of all load switch names
        :rtype: list[str]
        """
        return list(self._load_switches.keys())
