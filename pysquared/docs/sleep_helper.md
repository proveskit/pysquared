# Satellite Sleep Helper

### sleep_helper Module
This module provides the `SleepHelper` class for managing safe sleep and hibernation modes for the PySquared satellite. It ensures the satellite sleeps for specified durations while maintaining system safety and watchdog activity.

#### Imports
```py title="sleep_helper.py"
import gc
import time

import alarm
from alarm import time as alarmTime
from alarm.time import TimeAlarm

from .config.config import Config
from .logger import Logger
from .satellite import Satellite
from .watchdog import Watchdog

try:
    from typing import Literal
except Exception:
    pass
```

### SleepHelper Class
Class responsible for sleeping the Satellite to conserve power.

#### Attributes
- **cubesat** (Satellite): The Satellite object.
- **logger** (Logger): Logger instance for logging events and errors.
- **watchdog** (Watchdog): Watchdog instance for system safety.
- **config** (Config): Configuration object.

### Initialization of SleepHelper Instance

#### Arguments
- **cubesat** (Satellite): The Satellite object.
- **logger** (Logger): Logger instance for logging events and errors.
- **watchdog** (Watchdog): Watchdog instance for system safety.
- **config** (Config): Configuration object.

```py title="sleep_helper.py"
def __init__(
    self, cubesat: Satellite, logger: Logger, watchdog: Watchdog, config: Config
) -> None:
    self.cubesat: Satellite = cubesat
    self.logger: Logger = logger
    self.watchdog: Watchdog = watchdog
    self.config = config
```

### Safe Sleep

#### Function: `safe_sleep`
Puts the Satellite to sleep for a specified duration, in seconds. Allows for a maximum sleep duration as specified in the config.

##### Arguments
- **duration** (int): Specified time, in seconds, to sleep the Satellite for.

```py title="sleep_helper.py"
def safe_sleep(self, duration: int = 15) -> None:
    self.watchdog.pet()

    time_remaining = min(duration, self.config.longest_allowable_sleep_time)

    self.logger.debug("Setting Safe Sleep Mode", duration=time_remaining)

    while time_remaining > 0:
        time_increment = time_remaining if time_remaining < 15 else 15

        time_alarm: TimeAlarm = alarmTime.TimeAlarm(
            monotonic_time=time.monotonic() + time_increment
        )
        alarm.light_sleep_until_alarms(time_alarm)
        time_remaining -= time_increment

        self.watchdog.pet()
```

### Short Hibernation

#### Function: `short_hibernate`
Puts the Satellite to sleep for 120 seconds.

##### Returns
- **True**: Always returns True after hibernation.

```py title="sleep_helper.py"
def short_hibernate(self) -> Literal[True]:
    self.watchdog.pet()
    self.logger.debug("Short Hibernation Coming UP")
    gc.collect()
    # all should be off from cubesat powermode

    self.cubesat.f_softboot.toggle(True)
    self.safe_sleep(120)

    return True
```

### Long Hibernation

#### Function: `long_hibernate`
Puts the Satellite to sleep for 600 seconds.

##### Returns
- **True**: Always returns True after hibernation.

```py title="sleep_helper.py"
def long_hibernate(self) -> Literal[True]:
    self.watchdog.pet()
    self.logger.debug("LONG Hibernation Coming UP")
    gc.collect()
    # all should be off from cubesat powermode

    self.cubesat.f_softboot.toggle(True)
    self.safe_sleep(600)

    return True
```
