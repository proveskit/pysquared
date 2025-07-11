"""
Base Solar Panel Manager
=======================

This module provides a base class for solar panel managers to eliminate code duplication.
"""

import time

from ...logger import Logger
from ...protos.loadswitch import LoadSwitchProto
from ...protos.solar_panel import SolarPanelProto
from ..exception import NotPowered


class BaseSolarPanelManager(SolarPanelProto, LoadSwitchProto):
    """Base class for solar panel managers to eliminate code duplication."""

    def __init__(
        self,
        logger: Logger,
        panel_name: str,
        temperature_sensor=None,
        light_sensor=None,
        torque_coils=None,
        load_switch_pin=None,
        enable_high=True,
    ) -> None:
        """
        Initializes the base solar panel manager.

        :param Logger logger: Logger instance for logging messages.
        :param str panel_name: Name of the solar panel (e.g., "XY", "Z").
        :param temperature_sensor: Temperature sensor instance (can be None).
        :param light_sensor: Light sensor instance (can be None).
        :param torque_coils: Torque coils instance (can be None).
        :param load_switch_pin: GPIO pin for controlling the load switch (can be None).
        :param enable_high: If True, load switch enables when pin is HIGH. If False, enables when LOW.
        """
        self._log: Logger = logger
        self._panel_name = panel_name
        self._temperature_sensor = temperature_sensor
        self._light_sensor = light_sensor
        self._torque_coils = torque_coils
        self._load_switch_pin = load_switch_pin
        # Store the pin values directly
        self._enable_pin_value = enable_high
        self._disable_pin_value = not enable_high

        # Load switch state (initially disabled for safety)
        self._load_enabled = False

        # Error tracking
        self._error_count = 0

        # Sensor states
        self._sensor_states = {
            "temperature": "OK" if temperature_sensor else "NOT_AVAILABLE",
            "light": "OK" if light_sensor else "NOT_AVAILABLE",
        }

    def get_temperature(self) -> float | None:
        """Gets the current temperature of the solar panel.

        :return: The current temperature of the solar panel or None if sensor unavailable/failed
        :rtype: float | None

        :raises NotPowered: If the load switch is disabled.
        :raises Exception: Any exception from the underlying temperature sensor driver will be reraised.
        """
        if not self._load_enabled:
            raise NotPowered(f"{self._panel_name} solar panel is not powered")

        if self._temperature_sensor is None:
            return None

        try:
            temperature = self._temperature_sensor.temperature
            self._sensor_states["temperature"] = "OK"
            return temperature
        except Exception as e:
            self._sensor_states["temperature"] = "ERROR"
            self._error_count += 1
            self._log.error(
                f"Failed to read {self._panel_name} solar panel temperature", err=e
            )
            raise e

    def get_light_level(self) -> float | None:
        """Gets the current light level of the solar panel.

        :return: The current light level of the solar panel or None if sensor unavailable/failed
        :rtype: float | None

        :raises NotPowered: If the load switch is disabled.
        :raises Exception: Any exception from the underlying light sensor driver will be reraised.
        """
        if not self._load_enabled:
            raise NotPowered(f"{self._panel_name} solar panel is not powered")

        if self._light_sensor is None:
            return None

        try:
            light_level = self._light_sensor.light
            self._sensor_states["light"] = "OK"
            return light_level
        except Exception as e:
            self._sensor_states["light"] = "ERROR"
            self._error_count += 1
            self._log.error(
                f"Failed to read {self._panel_name} solar panel light level", err=e
            )
            raise e

    def get_all_data(self) -> tuple[float | None, float | None]:
        """Gets all the data from the solar panel.

        :return: A tuple containing the temperature and light level of the solar panel
        :rtype: tuple[float | None, float | None]

        :raises NotPowered: If the load switch is disabled.
        :raises Exception: Any exception from the underlying sensor drivers will be reraised.
        """
        if not self._load_enabled:
            raise NotPowered(f"{self._panel_name} solar panel is not powered")

        temp = self.get_temperature()
        light = self.get_light_level()
        return (temp, light)

    def drive_torque_coils(self, **kwargs) -> bool:
        """Drives the torque coils.

        :param **kwargs: Additional parameters for torque coil operation.
        :return: A Boolean indicating whether the torque coils were driven successfully
        :rtype: bool

        :raises NotPowered: If the load switch is disabled.
        :raises NotImplementedError: If torque coils are not available.
        :raises Exception: Any exception from the underlying torque coil driver will be reraised.
        """
        if not self._load_enabled:
            raise NotPowered(f"{self._panel_name} solar panel is not powered")

        if self._torque_coils is None:
            raise NotImplementedError(
                f"Torque coils not available for {self._panel_name} solar panel"
            )

        try:
            result = self._torque_coils.drive(**kwargs)
            return result
        except Exception as e:
            self._error_count += 1
            self._log.error(
                f"Failed to drive {self._panel_name} solar panel torque coils", err=e
            )
            raise e

    def get_sensor_states(self) -> dict:
        """Gets the current state of the sensors on the solar panel.

        :return: A dictionary containing the states of the sensors on the solar panel
        :rtype: dict
        """
        return self._sensor_states.copy()

    def get_error_count(self) -> int:
        """Gets the number of errors that have occurred on the solar panel since the last rese

        :return: The number of errors that have occurred on the solar panel since the last reset
        :rtype: int
        """
        return self._error_count

    # Load Switch Methods
    def enable_load(self) -> bool:
        """Enables the load switch.

        :return: A Boolean indicating whether the enable command was successful
        :rtype: bool

        :raises NotImplementedError: If no load switch pin is provided.
        """
        if self._load_switch_pin is None:
            raise NotImplementedError(
                f"Load switch pin is required for {self._panel_name} solar panel"
            )

        try:
            self._load_switch_pin.value = self._enable_pin_value
            self._log.debug(
                f"{self._panel_name} solar panel load switch pin set to {self._enable_pin_value}"
            )

            self._load_enabled = True
            self._log.debug(f"{self._panel_name} solar panel load switch enabled")
            return True
        except Exception as e:
            self._log.error(
                f"Failed to enable {self._panel_name} solar panel load switch", err=e
            )
            return False

    def disable_load(self) -> bool:
        """Disables the load switch.

        :return: A Boolean indicating whether the disable command was successful
        :rtype: bool

        :raises NotImplementedError: If no load switch pin is provided.
        """
        if self._load_switch_pin is None:
            raise NotImplementedError(
                f"Load switch pin is required for {self._panel_name} solar panel"
            )

        try:
            self._load_switch_pin.value = self._disable_pin_value
            self._log.debug(
                f"{self._panel_name} solar panel load switch pin set to {self._disable_pin_value}"
            )

            self._load_enabled = False
            self._log.debug(f"{self._panel_name} solar panel load switch disabled")
            return True
        except Exception as e:
            self._log.error(
                f"Failed to disable {self._panel_name} solar panel load switch", err=e
            )
            return False

    def reset_load(self) -> bool:
        """Resets the load switch by temporarily disabling it for 0.1 seconds then re-enabling it.

        :return: A Boolean indicating whether the reset command was successful
        :rtype: bool

        :raises NotImplementedError: If no load switch pin is provided.
        """
        if self._load_switch_pin is None:
            raise NotImplementedError(
                f"Load switch pin is required for {self._panel_name} solar panel"
            )

        try:
            # Store the current state
            was_enabled = self._load_enabled

            # Temporarily disable the load switch
            self._load_switch_pin.value = self._disable_pin_value
            self._log.debug(
                f"{self._panel_name} solar panel load switch pin temporarily set to {self._disable_pin_value}"
            )
            self._load_enabled = False

            # Wait for 0.1 seconds
            time.sleep(0.1)

            # Re-enable the load switch if it was previously enabled
            if was_enabled:
                self._load_switch_pin.value = self._enable_pin_value
                self._log.debug(
                    f"{self._panel_name} solar panel load switch pin re-enabled to {self._enable_pin_value}"
                )
                self._load_enabled = True

            self._log.debug(
                f"{self._panel_name} solar panel load switch reset completed"
            )
            return True
        except Exception as e:
            self._log.error(
                f"Failed to reset {self._panel_name} solar panel load switch", err=e
            )
            return False

    def get_load_state(self) -> bool:
        """Gets the current state of the load switch.

        :return: A Boolean indicating whether the load is enabled
        :rtype: bool
        """
        return self._load_enabled
