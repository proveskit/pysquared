"""
CircuitPython driver for PySquared satellite board.
PySquared Hardware Version: Flight Controller V4c
CircuitPython Version: 9.0.0
Library Repo:

* Author(s): Nicole Maggard, Michael Pham, and Rachel Sarmiento
"""

# Common CircuitPython Libs
import asyncio  # Add asyncio import
import sys
import time
from collections import OrderedDict
from os import chdir, mkdir, stat

import board
import busio
import digitalio
import microcontroller
import sdcardio
from micropython import const
from storage import VfsFat, mount, umount

import lib.adafruit_lis2mdl as adafruit_lis2mdl  # Magnetometer
import lib.adafruit_tca9548a as adafruit_tca9548a  # I2C Multiplexer
import lib.neopixel as neopixel  # RGB LED
import lib.pysquared.nvm.register as register
import lib.rv3028.rv3028 as rv3028  # Real Time Clock
from lib.adafruit_lsm6ds.lsm6dsox import LSM6DSOX  # IMU
from lib.pysquared.config.config import Config  # Configs
from lib.pysquared.nvm.counter import Counter
from lib.pysquared.nvm.flag import Flag

try:
    from typing import Any, Callable, Optional, OrderedDict, TextIO, Union

    import circuitpython_typing
except Exception:
    pass

from lib.pysquared.logger import Logger

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

    def safe_init(func: Callable[..., Any]):
        def wrapper(self, *args, **kwargs):
            hardware_key: str = kwargs.get("hardware_key", "UNKNOWN")
            self.logger.debug(
                "Initializing hardware component", hardware_key=hardware_key
            )

            try:
                device: Any = func(self, *args, **kwargs)
                return device

            except Exception as e:
                self.logger.error(
                    "There was an error initializing this hardware component",
                    e,
                    hardware_key=hardware_key,
                )
            return None

        return wrapper

    @safe_init
    def init_general_hardware(
        self,
        init_func: Callable[..., Any],
        *args: Any,
        hardware_key,
        orpheus_func: Callable[..., Any] = None,
        **kwargs: Any,
    ) -> Any:
        """
            Args:
            init_func (Callable[..., Any]): The function used to initialize the hardware.
            *args (Any): Positional arguments to pass to the `init_func`.
            hardware_key (str): A unique identifier for the hardware being initialized.
            orpheus_func (Callable[..., Any], optional): An alternative function to initialize
                the hardware if the `orpheus` flag is set. Defaults to `None`.
            **kwargs (Any): Additional keyword arguments to pass to the `init_func`.
                Must be placed before `hardware_key`.

            Returns:
                Any: The initialized hardware instance if successful, or `None` if an error occurs.

        Raises:
                Exception: Any exception raised by the `init_func` or `orpheus_func`
                will be caught and handled by the `@safe_init` decorator.
        """
        if self.orpheus and orpheus_func:
            return orpheus_func(hardware_key)

        hardware_instance = init_func(*args, **kwargs)
        self.hardware[hardware_key] = True
        return hardware_instance

    @safe_init
    def init_rtc(self, hardware_key: str) -> None:
        self.rtc: rv3028.RV3028 = rv3028.RV3028(self.i2c1)

        # Still need to test these configs
        self.rtc.configure_backup_switchover(mode="level", interrupt=True)
        self.hardware[hardware_key] = True

    @safe_init
    def init_sd_card(self, hardware_key: str) -> None:
        # Baud rate depends on the card, 4MHz should be safe
        _sd = sdcardio.SDCard(self.spi0, board.SPI0_CS1, baudrate=4000000)
        _vfs = VfsFat(_sd)
        mount(_vfs, "/sd")
        self.fs = _vfs
        sys.path.append("/sd")
        self.hardware[hardware_key] = True

    @safe_init
    def init_neopixel(self, hardware_key: str) -> None:
        self.neopwr: digitalio.DigitalInOut = digitalio.DigitalInOut(board.NEO_PWR)
        self.neopwr.switch_to_output(value=True)
        self.neopixel: neopixel.NeoPixel = neopixel.NeoPixel(
            board.NEOPIX, 1, brightness=0.2, pixel_order=neopixel.GRB
        )
        self.neopixel[0] = (0, 0, 255)
        self.hardware[hardware_key] = True

    @safe_init
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

    def __init__(self, config: Config, logger: Logger, version: str) -> None:
        self.config: Config = config
        self.cubesat_name: str = config.cubesat_name
        """
        Big init routine as the whole board is brought up. Starting with config variables.
        """
        self.legacy: bool = config.legacy
        self.heating: bool = config.heating
        self.orpheus: bool = config.orpheus  # maybe change var name
        self.is_licensed: bool = config.is_licensed
        self.logger = logger

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

        """
        Setting up data buffers
        """
        # TODO(cosmiccodon/blakejameson):
        # Data_cache, filenumbers, image_packets, and send_buff are variables that are not used in the codebase. They were put here for Orpheus last minute.
        # We are unsure if these will be used in the future, so we are keeping them here for now.
        self.data_cache: dict = {}
        self.filenumbers: dict = {}
        self.image_packets: int = 0
        self.uart_baudrate: int = 9600
        self.buffer: Optional[bytearray] = None
        self.buffer_size: int = 1
        self.send_buff: memoryview = memoryview(SEND_BUFF)
        self.micro: microcontroller = microcontroller

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
                ("I2C0", False),
                ("SPI0", False),
                ("I2C1", False),
                ("UART", False),
                ("IMU", False),
                ("Mag", False),
                ("SDcard", False),
                ("NEOPIX", False),
                ("WDT", False),
                ("TCA", False),
                ("Face0", False),
                ("Face1", False),
                ("Face2", False),
                ("Face3", False),
                ("Face4", False),
                ("RTC", False),
            ]
        )

        if self.f_softboot.get():
            self.f_softboot.toggle(False)

        """
        Setting up the watchdog pin.
        """

        self.watchdog_pin: digitalio.DigitalInOut = digitalio.DigitalInOut(
            board.WDT_WDI
        )
        self.watchdog_pin.direction = digitalio.Direction.OUTPUT
        self.watchdog_pin.value = False

        """
        Set the CPU Clock Speed
        """
        cpu_freq: int = 125000000 if self.turbo_clock else 62500000
        for cpu in microcontroller.cpus:
            cpu.frequency = cpu_freq

        """
        Intializing Communication Buses
        """

        # Alternative Implementations of hardware initialization specific for orpheus
        def orpheus_skip_i2c(hardware_key: str) -> None:
            self.logger.debug(
                "Hardware component not initialized",
                cubesat=self.cubesat_name,
                hardware_key=hardware_key,
            )
            return None

        def orpheus_init_uart(hardware_key: str):
            uart: circuitpython_typing.ByteStream = busio.UART(
                board.I2C0_SDA, board.I2C0_SCL, baudrate=self.uart_baudrate
            )
            self.hardware[hardware_key] = True
            return uart

        self.i2c0: busio.I2C = self.init_general_hardware(
            busio.I2C,
            board.I2C0_SCL,
            board.I2C0_SDA,
            hardware_key="I2C0",
            orpheus_func=orpheus_skip_i2c,
        )

        self.spi0: busio.SPI = self.init_general_hardware(
            busio.SPI,
            board.SPI0_SCK,
            board.SPI0_MOSI,
            board.SPI0_MISO,
            hardware_key="SPI0",
        )

        self.i2c1: busio.I2C = self.init_general_hardware(
            busio.I2C,
            board.I2C1_SCL,
            board.I2C1_SDA,
            frequency=100000,
            hardware_key="I2C1",
        )

        self.uart: circuitpython_typing.ByteStream = self.init_general_hardware(
            busio.UART,
            board.TX,
            board.RX,
            baud_rate=self.uart_baudrate,
            hardware_key="UART",
            orpheus_func=orpheus_init_uart,
        )

        ######## Temporary Fix for RF_ENAB ########
        #                                         #
        if self.legacy:
            self.enable_rf: digitalio.DigitalInOut = digitalio.DigitalInOut(
                board.RF_ENAB
            )
            # self.enable_rf.switch_to_output(value=False) # if U21
            self.enable_rf.switch_to_output(value=True)  # if U7
        else:
            self.enable_rf: bool = True
        #                                         #
        ######## Temporary Fix for RF_ENAB ########

        self.imu: LSM6DSOX = self.init_general_hardware(
            LSM6DSOX, i2c_bus=self.i2c1, address=0x6B, hardware_key="IMU"
        )
        self.mangetometer: adafruit_lis2mdl.LIS2MDL = self.init_general_hardware(
            adafruit_lis2mdl.LIS2MDL, self.i2c1, hardware_key="Mag"
        )
        self.init_rtc(hardware_key="RTC")
        self.init_sd_card(hardware_key="SD Card")
        self.init_neopixel(hardware_key="NEOPIX")
        self.init_tca_multiplexer(hardware_key="TCA")

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

        # Set current version
        self.version: str = version

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
    def rgb(self) -> tuple[int, int, int]:
        return self.neopixel[0]

    @rgb.setter
    def rgb(self, value: tuple[int, int, int]) -> None:
        if not self.hardware["NEOPIX"]:
            self.logger.warning("The NEOPIXEL device is not initialized")
            return

        # NEOPIX is initialized
        try:
            self.neopixel[0] = value
        except Exception as e:
            self.logger.error(
                "There was an error trying to set the new RGB value",
                e,
                value=value,
            )

    @property
    def get_system_uptime(self) -> int:
        self.CURRENTTIME: int = const(time.time())
        return self.CURRENTTIME - self.BOOTTIME

    @property
    def reset_vbus(self) -> None:
        # unmount SD card to avoid errors
        if self.hardware["SDcard"]:
            try:
                umount("/sd")
                time.sleep(3)
            except Exception as e:
                self.logger.error("There was an error unmounting the SD card", e)
        try:
            self.logger.debug(
                "Resetting VBUS [IMPLEMENT NEW FUNCTION HERE]",
            )
        except Exception as e:
            self.logger.error("There was a vbus reset error", e)

    @property
    def gyro(self) -> Union[tuple[float, float, float], None]:
        try:
            return self.imu.gyro
        except Exception as e:
            self.logger.error("There was an error retrieving the gyro values", e)

    @property
    def accel(self) -> Union[tuple[float, float, float], None]:
        try:
            return self.imu.acceleration
        except Exception as e:
            self.logger.error(
                "There was an error retrieving the accelerometer values", e
            )

    @property
    def internal_temperature(self) -> Union[float, None]:
        try:
            return self.imu.temperature
        except Exception as e:
            self.logger.error(
                "There was an error retrieving the internal temperature value", e
            )

    @property
    def mag(self) -> Union[tuple[float, float, float], None]:
        try:
            return self.mangetometer.magnetic
        except Exception as e:
            self.logger.error(
                "There was an error retrieving the magnetometer sensor values", e
            )

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

    async def watchdog_pet(self) -> None:
        """Pet the watchdog timer"""
        self.logger.debug("Petting watchdog")
        self.watchdog_pin.value = True
        await asyncio.sleep(0.01)
        self.watchdog_pin.value = False

    async def watchdog_pet_task(self) -> None:
        """Async task to continuously pet the watchdog"""
        self.logger.info("Starting watchdog petting background task")
        while self.hardware.get("WDT", False):
            await self.watchdog_pet()
            await asyncio.sleep(10.0)  # Pet watchdog every second
        self.logger.info("Watchdog petting task stopped")

    def check_watchdog(self) -> None:
        """
        Legacy method maintained for compatibility
        The actual petting is now handled by the background task
        """
        pass  # No-op as this is now handled by the async task

    def check_reboot(self) -> None:
        """Check if system needs to be rebooted"""
        # No need to check watchdog anymore as it's handled by the background task
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
                self.neopixel.brightness = 0
                self.enable_rf.value = False
                self.power_mode: str = "critical"

            elif "min" in mode:
                self.neopixel.brightness = 0
                self.enable_rf.value = False

                self.power_mode: str = "minimum"

            elif "norm" in mode:
                self.enable_rf.value = True
                self.power_mode: str = "normal"
                # don't forget to reconfigure radios, gps, etc...

            elif "max" in mode:
                self.enable_rf.value = True
                self.power_mode: str = "maximum"
        except Exception as e:
            self.logger.error(
                "There was an Error in changing operations of powermode",
                e,
                mode=mode,
            )

    """
    SD Card Functions
    """

    def print_file(self, filedir: str = None, binary: bool = False) -> None:
        try:
            if filedir is None:
                raise FileNotFoundError("file directory is empty")
            self.logger.debug("Printing File", file_dir=filedir)
            if binary:
                with open(filedir, "rb") as file:
                    self.logger.debug(
                        "Printing in binary mode", content=str(file.read())
                    )
            else:
                with open(filedir, "r") as file:
                    for line in file:
                        self.logger.info(line.strip())
        except Exception as e:
            self.logger.error(
                "Can't print file", e, filedir=filedir, binary_mode=binary
            )

    def read_file(
        self, filedir: str = None, binary: bool = False
    ) -> Union[bytes, TextIO, None]:
        try:
            if filedir is None:
                raise FileNotFoundError("file directory is empty")
            self.logger.debug("Reading a file", file_dir=filedir)
            if binary:
                with open(filedir, "rb") as file:
                    self.logger.debug(str(file.read()))
                    return file.read()
            else:
                with open(filedir, "r") as file:
                    for line in file:
                        self.logger.debug(str(line.strip()))
                    return file
        except Exception as e:
            self.logger.error("Can't read file", e, filedir=filedir, binary_mode=binary)

    def new_file(self, substring: str, binary: bool = False) -> Union[str, None]:
        """
        substring something like '/data/DATA_'
        directory is created on the SD!
        int padded with zeros will be appended to the last found file
        """
        if not self.hardware["SDcard"]:
            self.logger.warning("SD Card not initialized")

        # SDCard is initialized
        try:
            ff: str = ""
            n: int = 0
            _folder: str = substring[: substring.rfind("/") + 1]
            _file: str = substring[substring.rfind("/") + 1 :]
            self.logger.debug(
                "Creating new file in directory: /sd{} with file prefix: {}".format(
                    _folder, _file
                ),
            )
            try:
                chdir("/sd" + _folder)
            except OSError:
                self.logger.error(
                    "The directory was not found. Now Creating...",
                    directory=_folder,
                )
                try:
                    mkdir("/sd" + _folder)
                except Exception as e:
                    self.logger.error(
                        "Error with creating new file",
                        e,
                        filedir="/sd" + _folder,
                    )
                    return None
            for i in range(0xFFFF):
                ff: str = "/sd{}{}{:05}.txt".format(_folder, _file, (n + i) % 0xFFFF)
                try:
                    if n is not None:
                        stat(ff)
                except Exception as e:
                    self.logger.error(
                        "There was an error running the stat function on this file",
                        e,
                        filedir=ff,
                        file_num=n,
                    )
                    n: int = (n + i) % 0xFFFF
                    # print('file number is',n)
                    break
            self.logger.debug("creating a file...", file_dir=str(ff))
            if binary:
                b: str = "ab"
            else:
                b: str = "a"
            with open(ff, b) as f:
                f.tell()
            chdir("/")
            return ff
        except Exception as e:
            self.logger.error("Error creating file", e, filedir=ff, binary_mode=binary)
            return None
