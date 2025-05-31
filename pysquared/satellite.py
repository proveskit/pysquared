"""
satellite Module
================

CircuitPython driver for PySquared satellite board.
PySquared Hardware Version: Flight Controller V4c
CircuitPython Version: 9.0.0

This module defines the Satellite class, which manages hardware configuration,
non-volatile memory (NVM) flags and counters, power modes, and system uptime.

* Author(s): Nicole Maggard, Michael Pham, and Rachel Sarmiento
"""

# Common CircuitPython Libs
import time

import microcontroller
from micropython import const

from .config.config import Config  # Configs
from .nvm import register
from .nvm.counter import Counter
from .nvm.flag import Flag

try:
    from typing import Optional
except Exception:
    pass

from .logger import Logger


class Satellite:
    """
    Satellite class for managing hardware configuration, NVM, and power modes.

    Attributes:
        boot_count (Counter): NVM counter for boot count.
        f_softboot (Flag): NVM flag for soft boot.
        f_brownout (Flag): NVM flag for brownout detection.
        f_shtdwn (Flag): NVM flag for shutdown state.
        f_burned (Flag): NVM flag for burn wire status.
        logger (Logger): Logger instance for logging events and errors.
        config (Config): Configuration object.
        normal_temp (int): Normal operating temperature.
        normal_battery_temp (int): Normal battery temperature.
        normal_micro_temp (int): Normal microcontroller temperature.
        normal_charge_current (float): Normal charge current.
        normal_battery_voltage (float): Normal battery voltage.
        critical_battery_voltage (float): Critical battery voltage threshold.
        reboot_time (int): Time before automatic reboot.
        turbo_clock (bool): Whether to use turbo clock speed.
        cubesat_name (str): Name of the CubeSat.
        heating (bool): Heating status.
        charge_current (Optional[float]): Current charge current.
        power_mode (str): Current power mode.
        BOOTTIME (float): System boot time.
        CURRENTTIME (float): Current system time.
    """

    # General NVM counters
    boot_count: Counter = Counter(index=register.BOOTCNT)

    # Define NVM flags
    f_softboot: Flag = Flag(index=register.FLAG, bit_index=0)
    f_brownout: Flag = Flag(index=register.FLAG, bit_index=3)
    f_shtdwn: Flag = Flag(index=register.FLAG, bit_index=5)
    f_burned: Flag = Flag(index=register.FLAG, bit_index=6)

    def __init__(
        self,
        logger: Logger,
        config: Config,
    ) -> None:
        """
        Initializes the Satellite instance with configuration and logger.

        Args:
            logger (Logger): Logger instance for logging events and errors.
            config (Config): Configuration object.
        """
        self.logger: Logger = logger
        self.config: Config = config

        """
        Define the normal power modes
        """
        self.normal_temp: int = config.normal_temp
        self.normal_battery_temp: int = config.normal_battery_temp
        self.normal_micro_temp: int = config.normal_micro_temp
        self.normal_charge_current: float = config.normal_charge_current
        self.normal_battery_voltage: float = config.normal_battery_voltage
        self.critical_battery_voltage: float = config.critical_battery_voltage
        # self.current_draw: float = config.current_draw
        self.reboot_time: int = config.reboot_time
        self.turbo_clock: bool = config.turbo_clock
        self.cubesat_name: str = config.cubesat_name
        self.heating: bool = config.heating

        """
        Setting up data buffers
        """
        # These are here because of problems integrating the battery board on Orphues.
        # They should be moved to the battery board in the future.
        # They are only used in state of health

        # self.battery_voltage: Optional[float] = None
        self.charge_current: Optional[float] = None
        self.power_mode: str = "normal"

        """
        Define the boot time and current time
        """

        self.BOOTTIME: float = time.time()
        self.logger.debug("Booting up!", boot_time=f"{self.BOOTTIME}s")
        self.CURRENTTIME: float = self.BOOTTIME

        # Clear softboot flag if set 
        if self.f_softboot.get():
            self.f_softboot.toggle(False)

        """
        Set the CPU Clock Speed
        """
        cpu_freq: int = 125000000 if self.turbo_clock else 62500000
        for cpu in microcontroller.cpus:  # type: ignore # Needs fix in CircuitPython stubs
            cpu.frequency = cpu_freq

    """
    Code to call satellite parameters
    """

    @property
    def get_system_uptime(self) -> float:
        """
        Returns the system uptime since boot.

        Returns:
            float: System uptime in seconds.
        """
        self.CURRENTTIME: float = const(time.time())
        return self.CURRENTTIME - self.BOOTTIME

    """
    Maintenence Functions
    """

    def check_reboot(self) -> None:
        """
        Checks if the system uptime exceeds the reboot time and resets if needed.
        """
        self.UPTIME: float = self.get_system_uptime
        self.logger.debug("Current up time stat:", uptime=self.UPTIME)
        if self.UPTIME > self.reboot_time:
            microcontroller.reset()

    def powermode(self, mode: str) -> None:
        """
        Configure the hardware for minimum, normal, critical, or maximum power consumption.
        Add custom modes for mission-specific control. 
        
        Args:
            mode (str): Desired power mode ("critical", "minimum", "normal", "maximum").
        """
        try:
            if "crit" in mode:
                self.power_mode: str = "critical"

            elif "min" in mode:
                self.power_mode: str = "minimum"

            elif "norm" in mode:
                self.power_mode: str = "normal"
                # don't forget to reconfigure radios, gps, etc...

            elif "max" in mode:
                self.power_mode: str = "maximum"
        except Exception as e:
            self.logger.error(
                "There was an Error in changing operations of powermode",
                e,
                mode=mode,
            )
