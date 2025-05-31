# Satellite Hardware Management

### satellite Module
This module provides the `Satellite` class for managing hardware configuration, non-volatile memory (NVM) flags and counters, power modes, and system uptime for the PySquared satellite.

#### Imports
```py title="satellite.py"
import time
import microcontroller
from micropython import const

from .config.config import Config
from .nvm import register
from .nvm.counter import Counter
from .nvm.flag import Flag

try:
    from typing import Optional
except Exception:
    pass

from .logger import Logger
```

### Satellite Class
Manages hardware configuration, NVM, power modes, and system uptime.

#### Attributes
- **boot_count** (Counter): NVM counter for boot count.
- **f_softboot** (Flag): NVM flag for soft boot.
- **f_brownout** (Flag): NVM flag for brownout detection.
- **f_shtdwn** (Flag): NVM flag for shutdown state.
- **f_burned** (Flag): NVM flag for burn wire status.
- **logger** (Logger): Logger instance for logging events and errors.
- **config** (Config): Configuration object.
- **normal_temp** (int): Normal operating temperature.
- **normal_battery_temp** (int): Normal battery temperature.
- **normal_micro_temp** (int): Normal microcontroller temperature.
- **normal_charge_current** (float): Normal charge current.
- **normal_battery_voltage** (float): Normal battery voltage.
- **critical_battery_voltage** (float): Critical battery voltage threshold.
- **reboot_time** (int): Time before automatic reboot.
- **turbo_clock** (bool): Whether to use turbo clock speed.
- **cubesat_name** (str): Name of the CubeSat.
- **heating** (bool): Heating status.
- **charge_current** (Optional[float]): Current charge current.
- **power_mode** (str): Current power mode.
- **BOOTTIME** (float): System boot time.
- **CURRENTTIME** (float): Current system time.

### Initialization of Satellite Instance

#### Arguments
- **logger** (Logger): Logger instance for logging events and errors.
- **config** (Config): Configuration object.

```py title="satellite.py"
def __init__(self, logger: Logger, config: Config) -> None:
    self.logger: Logger = logger
    self.config: Config = config

    # Define the normal power modes
    self.normal_temp: int = config.normal_temp
    self.normal_battery_temp: int = config.normal_battery_temp
    self.normal_micro_temp: int = config.normal_micro_temp
    self.normal_charge_current: float = config.normal_charge_current
    self.normal_battery_voltage: float = config.normal_battery_voltage
    self.critical_battery_voltage: float = config.critical_battery_voltage
    self.reboot_time: int = config.reboot_time
    self.turbo_clock: bool = config.turbo_clock
    self.cubesat_name: str = config.cubesat_name
    self.heating: bool = config.heating

    # Data buffers for state of health
    self.charge_current: Optional[float] = None
    self.power_mode: str = "normal"

    # Define the boot time and current time
    self.BOOTTIME: float = time.time()
    self.logger.debug("Booting up!", boot_time=f"{self.BOOTTIME}s")
    self.CURRENTTIME: float = self.BOOTTIME

    # Clear softboot flag if set
    if self.f_softboot.get():
        self.f_softboot.toggle(False)

    # Set the CPU Clock Speed
    cpu_freq: int = 125000000 if self.turbo_clock else 62500000
    for cpu in microcontroller.cpus:
        cpu.frequency = cpu_freq
```

### System Uptime

#### Property: `get_system_uptime`
Returns the system uptime since boot.

##### Returns
- **float**: System uptime in seconds.

```py title="satellite.py"
@property
def get_system_uptime(self) -> float:
    self.CURRENTTIME: float = const(time.time())
    return self.CURRENTTIME - self.BOOTTIME
```

### Maintenance Functions

#### Function: `check_reboot`
Checks if the system uptime exceeds the reboot time and resets if needed.

```py title="satellite.py"
def check_reboot(self) -> None:
    """
    Checks if the system uptime exceeds the reboot time and resets if needed.
    """
    self.UPTIME: float = self.get_system_uptime
    self.logger.debug("Current up time stat:", uptime=self.UPTIME)
    if self.UPTIME > self.reboot_time:
        microcontroller.reset()
```

#### Function: `powermode`
Configures the hardware for minimum, normal, critical, or maximum power consumption.

##### Arguments
- **mode** (str): Desired power mode ("critical", "minimum", "normal", "maximum").

```py title="satellite.py"
def powermode(self, mode: str) -> None:
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
```