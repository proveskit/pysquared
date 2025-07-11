"""
XY Solar Panel Manager
=====================

This module provides a manager for controlling XY solar panels on PySquared satellite hardware.
The manager handles temperature and light sensors, torque coils, and load switch functionality.

Usage Example:

from lib.pysquared.hardware.solar_panel.xy_panel_manager import XYSolarPanelManager
from lib.pysquared.hardware.temperature_sensor import TemperatureSensor
from lib.pysquared.hardware.light_sensor import LightSensor
from lib.pysquared.hardware.torque_coils import TorqueCoils

# Initialize sensors and components externally
temp_sensor = TemperatureSensor(i2c, address=0x48)
light_sensor = LightSensor(i2c, address=0x10)
torque_coils = TorqueCoils(pin1, pin2, pin3)

# Create the manager
xy_panel = XYSolarPanelManager(
    logger=logger,
    temperature_sensor=temp_sensor,
    light_sensor=light_sensor,
    torque_coils=torque_coils
)

# Control power
xy_panel.enable_load()
temp = xy_panel.get_temperature()
light = xy_panel.light()
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
