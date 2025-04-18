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


class SleepHelper:
    """
    Class responsible for sleeping the Satellite to conserve power
    """

    def __init__(
        self, cubesat: Satellite, logger: Logger, watchdog: Watchdog, config: Config
    ) -> None:
        """
        Creates a SleepHelper object.

        :param cubesat: The Satellite object
        :param logger: The Logger object allowing for log output

        """
        self.cubesat: Satellite = cubesat
        self.logger: Logger = logger
        self.watchdog: Watchdog = watchdog
        self.config = config

    def safe_sleep(self, duration: int = 15) -> None:
        """
        Puts the Satellite to sleep for specified duration, in seconds.

        Allows for a maximum sleep duration of the longest_allowable_sleep_time field specified in config

        :param duration: Specified time, in seconds, to sleep the Satellite for
        """

        self.watchdog.pet()

        time_remaining = min(duration, self.config.longest_allowable_sleep_time)

        self.logger.info("Setting Safe Sleep Mode")

        while time_remaining > 0:
            time_increment = time_remaining if time_remaining < 15 else 15

            time_alarm: circuitpython_typing.Alarm = alarm.time.TimeAlarm(
                monotonic_time=time.monotonic() + time_increment
            )
            alarm.light_sleep_until_alarms(time_alarm)
            time_remaining -= time_increment

            self.watchdog.pet()

    def short_hibernate(self) -> Literal[True]:
        """Puts the Satellite to sleep for 120 seconds"""

        self.watchdog.pet()
        self.logger.debug("Short Hibernation Coming UP")
        gc.collect()
        # all should be off from cubesat powermode

        self.cubesat.f_softboot.toggle(True)
        self.safe_sleep(120)

        return True

    def long_hibernate(self) -> Literal[True]:
        """Puts the Satellite to sleep for 180 seconds"""

        self.watchdog.pet()
        self.logger.debug("LONG Hibernation Coming UP")
        gc.collect()
        # all should be off from cubesat powermode

        self.cubesat.f_softboot.toggle(True)
        self.safe_sleep(600)

        return True
