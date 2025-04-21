import gc
import time

import alarm
from alarm import time as alarmTime
from alarm.time import TimeAlarm

from .logger import Logger
from .watchdog import Watchdog

try:
    from typing import Literal
except Exception:
    pass


class SleepHelper:
    """
    Class responsible for sleeping the Satellite to conserve power
    """

    def __init__(self, logger: Logger, watchdog: Watchdog) -> None:
        """
        Creates a SleepHelper object.

        :param cubesat: The Satellite object
        :param logger: The Logger object allowing for log output

        """
        self.logger: Logger = logger
        self.watchdog: Watchdog = watchdog

    def safe_sleep(self, duration: int = 15) -> None:
        """
        Puts the Satellite to sleep for specified duration, in seconds.

        Current implementation results in an actual sleep duration that is a multiple of 15.
        Current implementation only allows for a maximum sleep duration of 180 seconds.

        :param duration: Specified time, in seconds, to sleep the Satellite for
        """

        self.logger.info("Setting Safe Sleep Mode")

        iterations: int = 0

        while duration >= 15 and iterations < 12:
            time_alarm: TimeAlarm = alarmTime.TimeAlarm(
                monotonic_time=time.monotonic() + 15
            )

            alarm.light_sleep_until_alarms(time_alarm)
            duration -= 15
            iterations += 1

            self.watchdog.pet()

    def short_hibernate(self) -> Literal[True]:
        """Puts the Satellite to sleep for 120 seconds"""

        self.logger.debug("Short Hibernation Coming UP")
        gc.collect()
        # all should be off from cubesat powermode

        self.watchdog.pet()
        self.safe_sleep(120)

        return True

    def long_hibernate(self) -> Literal[True]:
        """Puts the Satellite to sleep for 180 seconds"""

        self.logger.debug("LONG Hibernation Coming UP")
        gc.collect()
        # all should be off from cubesat powermode

        self.watchdog.pet()
        self.safe_sleep(600)

        return True
