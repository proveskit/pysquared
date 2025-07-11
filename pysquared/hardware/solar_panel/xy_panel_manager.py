"""
XY Solar Panel Manager
=====================

This module provides a manager for controlling XY solar panels on PySquared satellite hardware.
The manager handles temperature and light sensors, torque coils, and load switch functionality.

Usage Example:

from pysquared.hardware.solar_panel.xy_panel_manager import XYSolarPanelManager
from pysquared.hardware.digitalio import initialize_pin
from pysquared.hardware.temperature_sensor import TemperatureSensor
from pysquared.hardware.light_sensor import LightSensor
from pysquared.hardware.torque_coils import TorqueCoils

# Initialize sensors and components externally
temp_sensor = TemperatureSensor(i2c, address=0x48)
light_sensor = LightSensor(i2c, address=0x10)
torque_coils = TorqueCoils(pin1, pin2, pin3)
load_switch_pin = initialize_pin(logger, board.LOAD_SWITCH_XY, Direction.OUTPUT, False)

# Create the manager
xy_panel = XYSolarPanelManager(
    logger=logger,
    temperature_sensor=temp_sensor,
    light_sensor=light_sensor,
    torque_coils=torque_coils,
    load_switch_pin=load_switch_pin,
    enable_high=True
)

# Control power and read sensors
try:
    xy_panel.enable_load()  # Raises RuntimeError on hardware failure

    # Check if load is enabled
    if xy_panel.is_enabled:
        temp = xy_panel.get_temperature()  # Returns float or None
        light = xy_panel.get_light_level()  # Returns float or None

        # Get all sensor data at once
        temp, light = xy_panel.get_all_data()

        # Drive torque coils if available
        xy_panel.drive_torque_coils(duration=5.0, intensity=0.8)

    # Reset load switch (momentary power cycle)
    xy_panel.reset_load()

    # Disable power
    xy_panel.disable_load()

except RuntimeError as e:
    logger.error("Hardware error occurred", err=e)
except NotImplementedError as e:
    logger.error("Feature not available", err=e)
"""

from .base_manager import BaseSolarPanelManager


class XYSolarPanelManager(BaseSolarPanelManager):
    """Class for managing XY solar panel operations."""

    def __init__(
        self,
        logger,
        temperature_sensor=None,
        light_sensor=None,
        torque_coils=None,
        load_switch_pin=None,
        enable_high=True,
    ) -> None:
        """
        Initializes the XY solar panel manager.

        :param logger: Logger instance for logging messages.
        :param temperature_sensor: Temperature sensor instance (can be None).
        :param light_sensor: Light sensor instance (can be None).
        :param torque_coils: Torque coils instance (can be None).
        :param load_switch_pin: GPIO pin for controlling the load switch (can be None).
        :param enable_high: If True, load switch enables when pin is HIGH. If False, enables when LOW.
        """
        super().__init__(
            logger=logger,
            panel_name="XY",
            temperature_sensor=temperature_sensor,
            light_sensor=light_sensor,
            torque_coils=torque_coils,
            load_switch_pin=load_switch_pin,
            enable_high=enable_high,
        )
