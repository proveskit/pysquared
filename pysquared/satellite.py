"""
CircuitPython driver for PySquared satellite board.
PySquared Hardware Version: Flight Controller V4c
CircuitPython Version: 9.0.0
Library Repo:

* Author(s): Nicole Maggard, Michael Pham, and Rachel Sarmiento
"""

# Common CircuitPython Libs
import time

import microcontroller
from micropython import const

from .config.config import Config  # Configs
from .nvm.counter import Counter
from .nvm.flag import Flag
from .nvm.register import Flag1, Register

try:
    from typing import Optional
except Exception:
    pass

from .logger import Logger


class Satellite:
    """
    NVM (Non-Volatile Memory) Register Definitions
    """

    # General NVM counters
    boot_count: Counter = Counter(index=Register.BOOTCNT)

    # Define NVM flags
    f_softboot: Flag = Flag(index=Register.FLAG1, bit_index=Flag1.SOFTBOOT)
    f_brownout: Flag = Flag(index=Register.FLAG1, bit_index=Flag1.BROWNOUT)
    f_shtdwn: Flag = Flag(index=Register.FLAG1, bit_index=Flag1.SHUTDOWN)
    f_burned: Flag = Flag(index=Register.FLAG1, bit_index=Flag1.BURNED)

    def __init__(
        self,
        logger: Logger,
        config: Config,
    ) -> None:
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
        self.current_draw: float = config.current_draw
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
        self.battery_voltage: Optional[float] = None
        self.charge_current: Optional[float] = None
        self.power_mode: str = "normal"

        """
        Define the boot time and current time
        """

        self.BOOTTIME: float = time.time()
        self.logger.debug("Booting up!", boot_time=f"{self.BOOTTIME}s")
        self.CURRENTTIME: float = self.BOOTTIME

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
        self.CURRENTTIME: float = const(time.time())
        return self.CURRENTTIME - self.BOOTTIME

    """
    Maintenence Functions
    """

    def check_reboot(self) -> None:
        self.UPTIME: float = self.get_system_uptime
        self.logger.debug("Current up time stat:", uptime=self.UPTIME)
        if self.UPTIME > self.reboot_time:
            microcontroller.reset()

    def powermode(self, mode: str) -> None:
        """
        Configure the hardware for minimum or normal power consumption
        Add custom modes for mission-specific control
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
