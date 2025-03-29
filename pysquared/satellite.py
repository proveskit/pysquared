"""
CircuitPython driver for PySquared satellite board.
PySquared Hardware Version: Flight Controller V4c
CircuitPython Version: 9.0.0
Library Repo:

* Author(s): Nicole Maggard, Michael Pham, and Rachel Sarmiento
"""

# Common CircuitPython Libs
import time
from collections import OrderedDict

import microcontroller
from micropython import const

import lib.adafruit_tca9548a as adafruit_tca9548a  # I2C Multiplexer
import lib.rv3028.rv3028 as rv3028  # Real Time Clock

from .config.config import Config  # Configs
from .nvm import register
from .nvm.counter import Counter
from .nvm.flag import Flag

try:
    from typing import Optional, OrderedDict, Union

except Exception:
    pass

from .logger import Logger

SEND_BUFF: bytearray = bytearray(252)


class Satellite:
    """
    NVM (Non-Volatile Memory) Register Definitions
    """

    # General NVM counters
    boot_count: Counter = Counter(index=register.BOOTCNT, datastore=microcontroller.nvm)

    # Define NVM flags
    f_softboot: Flag = Flag(
        index=register.FLAG, bit_index=0, datastore=microcontroller.nvm
    )
    f_brownout: Flag = Flag(
        index=register.FLAG, bit_index=3, datastore=microcontroller.nvm
    )
    f_shtdwn: Flag = Flag(
        index=register.FLAG, bit_index=5, datastore=microcontroller.nvm
    )
    f_burned: Flag = Flag(
        index=register.FLAG, bit_index=6, datastore=microcontroller.nvm
    )

    def init_rtc(self, hardware_key: str) -> None:
        self.rtc: rv3028.RV3028 = rv3028.RV3028(self.i2c1)

        # Still need to test these configs
        self.rtc.configure_backup_switchover(mode="level", interrupt=True)
        self.hardware[hardware_key] = True

    # Only used for face stuff, also needs more thought.
    def init_tca_multiplexer(self, hardware_key: str) -> None:
        try:
            self.tca: adafruit_tca9548a.TCA9548A = adafruit_tca9548a.TCA9548A(
                self.i2c1, address=int(0x77)
            )
            self.hardware[hardware_key] = True
        except OSError:
            self.logger.error(
                "TCA try_lock failed. TCA may be malfunctioning.",
                hardware_key=hardware_key,
            )
            self.hardware[hardware_key] = False
            return

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
        self.battery_voltage: float = config.battery_voltage
        self.current_draw: float = config.current_draw
        self.reboot_time: int = config.reboot_time
        self.turbo_clock: bool = config.turbo_clock
        self.cubesat_name: str = config.cubesat_name
        self.legacy: bool = config.legacy
        self.heating: bool = config.heating
        self.orpheus: bool = config.orpheus  # maybe change var name
        self.is_licensed: bool = config.is_licensed

        """
        Setting up data buffers
        """
        # Confused here, as self.battery_voltage was initialized to 3.3 in line 113(blakejameson)
        # NOTE(blakejameson): After asking Michael about the None variables below last night at software meeting, he mentioned they used
        # None as a state instead of the values to better manage some conditions with Orpheus.
        # I need to get a better understanding for the values and flow before potentially refactoring code here.
        self.battery_voltage: Optional[float] = None
        self.draw_current: Optional[float] = None
        self.charge_voltage: Optional[float] = None
        self.charge_current: Optional[float] = None
        self.is_charging: Optional[bool] = None
        self.battery_percentage: Optional[float] = None

        """
        Define the boot time and current time
        """

        self.BOOTTIME = time.time()
        self.logger.debug("Booting up!", boot_time=f"{self.BOOTTIME}s")
        self.CURRENTTIME: int = self.BOOTTIME
        self.UPTIME: int = 0

        self.hardware: OrderedDict[str, bool] = OrderedDict(
            [
                ("TCA", False),
                ("RTC", False),
            ]
        )

        if self.f_softboot.get():
            self.f_softboot.toggle(False)

        """
        Set the CPU Clock Speed
        """
        cpu_freq: int = 125000000 if self.turbo_clock else 62500000
        for cpu in microcontroller.cpus:
            cpu.frequency = cpu_freq

        """
        Face Initializations
        """
        self.scan_tca_channels()

        """
        Prints init State of PySquared Hardware
        """
        self.logger.debug("PySquared Hardware Initialization Complete!")

        for key, value in self.hardware.items():
            if value:
                self.logger.info(
                    "Successfully initialized hardware device",
                    device=key,
                    status=True,
                )
            else:
                self.logger.warning(
                    "Unable to initialize hardware device", device=key, status=False
                )
        # set power mode
        self.power_mode: str = "normal"

    """
    Init Helper Functions
    """

    def scan_tca_channels(self) -> None:
        if not self.hardware["TCA"]:
            self.logger.warning("TCA not initialized")
            return

        channel_to_face: dict[int, str] = {
            0: "Face0",
            1: "Face1",
            2: "Face2",
            3: "Face3",
            4: "Face4",
        }

        for channel in range(len(channel_to_face)):
            try:
                self._scan_single_channel(channel, channel_to_face)
            except OSError as os_error:
                self.logger.error(
                    "TCA try_lock failed. TCA may be malfunctioning.", os_error
                )
                self.hardware["TCA"] = False
                return
            except Exception as e:
                self.logger.error(
                    "There was an Exception during the scan_tca_channels function call",
                    e,
                    face=channel_to_face[channel],
                )

    def _scan_single_channel(
        self, channel: int, channel_to_face: dict[int, str]
    ) -> None:
        if not self.tca[channel].try_lock():
            return

        try:
            addresses: list[int] = self.tca[channel].scan()
            valid_addresses: list[int] = [
                addr for addr in addresses if addr not in [0x00, 0x19, 0x1E, 0x6B, 0x77]
            ]

            if not valid_addresses and 0x77 in addresses:
                self.logger.error(
                    "No Devices Found on channel", channel=channel_to_face[channel]
                )
                self.hardware[channel_to_face[channel]] = False
            else:
                self.logger.debug(
                    channel=channel,
                    valid_addresses=[hex(addr) for addr in valid_addresses],
                )
                if channel in channel_to_face:
                    self.hardware[channel_to_face[channel]] = True
        except Exception as e:
            self.logger.error(
                "There was an Exception during the _scan_single_channel function call",
                e,
                face=channel_to_face[channel],
            )
        finally:
            self.tca[channel].unlock()

    """
    Code to call satellite parameters
    """

    @property
    def get_system_uptime(self) -> int:
        self.CURRENTTIME: int = const(time.time())
        return self.CURRENTTIME - self.BOOTTIME

    @property
    def time(self) -> Union[tuple[int, int, int], None]:
        try:
            return self.rtc.get_time()
        except Exception as e:
            self.logger.error("There was an error retrieving the RTC time", e)

    @time.setter
    def time(self, hms: tuple[int, int, int]) -> None:
        """
        hms: A 3-tuple of ints containing data for the hours, minutes, and seconds respectively.
        """
        hours, minutes, seconds = hms
        if not self.hardware["RTC"]:
            self.logger.warning("The RTC is not initialized")
            return

        try:
            self.rtc.set_time(hours, minutes, seconds)
        except Exception as e:
            self.logger.error(
                "There was an error setting the RTC time",
                e,
                hms=hms,
                hour=hms[0],
                minutes=hms[1],
                seconds=hms[2],
            )

    @property
    def date(self) -> Union[tuple[int, int, int, int], None]:
        try:
            return self.rtc.get_date()
        except Exception as e:
            self.logger.error("There was an error retrieving RTC date", e)

    @date.setter
    def date(self, ymdw: tuple[int, int, int, int]) -> None:
        """
        ymdw: A 4-tuple of ints containing data for the year, month, date, and weekday respectively.
        """
        year, month, date, weekday = ymdw
        if not self.hardware["RTC"]:
            self.logger.warning("RTC not initialized")
            return

        try:
            self.rtc.set_date(year, month, date, weekday)
        except Exception as e:
            self.logger.error(
                "There was an error setting the RTC date",
                e,
                ymdw=ymdw,
                year=ymdw[0],
                month=ymdw[1],
                date=ymdw[2],
                weekday=ymdw[3],
            )

    """
    Maintenence Functions
    """

    def watchdog_pet(self) -> None:
        self.watchdog_pin.value = True
        time.sleep(0.01)
        self.watchdog_pin.value = False

    def check_reboot(self) -> None:
        self.UPTIME: int = self.get_system_uptime
        self.logger.debug("Current up time stat:", uptime=self.UPTIME)
        if self.UPTIME > self.reboot_time:
            self.micro.reset()

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
