import time

import alarm
from alarm.time import TimeAlarm

from .config.config import Config
from .logger import Logger
from .watchdog import Watchdog


class SleepHelper:
    """
    Class responsible for sleeping the Satellite to conserve power
    """

    def __init__(self, logger: Logger, config: Config, watchdog: Watchdog) -> None:
        """
        Creates a SleepHelper object.

        :param cubesat: The Satellite object
        :param logger: The Logger object allowing for log output

        """
        self.logger: Logger = logger
        self.config: Config = config
        self.watchdog: Watchdog = watchdog

    def safe_sleep(self, duration) -> None:
        """
        Puts the Satellite to sleep for specified duration, in seconds.

        Allows for a maximum sleep duration of the longest_allowable_sleep_time field specified in config

        :param duration: Specified time, in seconds, to sleep the Satellite for
        """
        # Ensure the duration does not exceed the longest allowable sleep time
        if duration > self.config.longest_allowable_sleep_time:
            self.logger.warning(
                "Requested sleep duration exceeds longest allowable sleep time. "
                "Adjusting to longest allowable sleep time.",
                requested_duration=duration,
                longest_allowable_sleep_time=self.config.longest_allowable_sleep_time,
            )
            duration = self.config.longest_allowable_sleep_time

        self.logger.debug("Setting Safe Sleep Mode", duration=duration)

        end_sleep_time = time.monotonic() + duration

        # Pet the watchdog before sleeping
        self.watchdog.pet()

        # Sleep in increments to allow for watchdog to be pet
        while time.monotonic() < end_sleep_time:
            # TODO(nateinaction): Replace the hardcoded watchdog timeout with a config value
            watchdog_timeout = 15

            time_increment = min(end_sleep_time - time.monotonic(), watchdog_timeout)

            time_alarm: TimeAlarm = TimeAlarm(
                monotonic_time=time.monotonic() + time_increment
            )

            alarm.light_sleep_until_alarms(time_alarm)

            # Pet the watchdog on wake
            self.watchdog.pet()
