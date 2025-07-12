"""This module provides the SleepHelper class for managing safe sleep and hibernation
modes for the PySquared satellite. It ensures the satellite sleeps for specified
durations while maintaining system safety and watchdog activity.

"""

import time

import alarm
from alarm.time import TimeAlarm

from .config.config import Config
from .logger import Logger
from .watchdog import Watchdog


class SleepHelper:
    """
    Class responsible for sleeping the Satellite to conserve power.

    Attributes:
        cubesat (Satellite): The Satellite object.
        logger (Logger): Logger instance for logging events and errors.
        watchdog (Watchdog): Watchdog instance for system safety.
        config (Config): Configuration object.
    """

    def __init__(self, logger: Logger, config: Config, watchdog: Watchdog) -> None:
        """
        Creates a SleepHelper object.

        Args:
            logger (Logger): Logger instance for logging events and errors.
            watchdog (Watchdog): Watchdog instance for system safety.
            config (Config): Configuration object.
        """
        self.logger: Logger = logger
        self.config: Config = config
        self.watchdog: Watchdog = watchdog

    def safe_sleep(self, duration) -> None:
        """
        Puts the Satellite to sleep for a specified duration, in seconds.

        Allows for a maximum sleep duration of the longest_allowable_sleep_time field specified in config

        Args:
            duration (int): Specified time, in seconds, to sleep the Satellite for.
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
