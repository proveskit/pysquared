"""This module provides the SleepHelper class for managing safe sleep and hibernation
modes for the PySquared satellite. It ensures the satellite sleeps for specified
durations while maintaining system safety and watchdog activity.

"""

import time

from .config.config import Config
from .logger import Logger
from .watchdog import Watchdog


class SleepHelper:
    """
    Class responsible for sleeping the Satellite to conserve power.

    Attributes:
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

    def safe_sleep(self, duration, watchdog_timeout=15) -> None:
        """
        Puts the Satellite to sleep for a specified duration, in seconds while still petting the watchdog at least every 15 seconds.

        Allows for a maximum sleep duration of the longest_allowable_sleep_time field specified in config

        Args:
            duration (int): Specified time, in seconds, to sleep the Satellite for.
            watchdog_timeout (int): Time, in seconds, to wait before petting the watchdog. Default is 15 seconds.
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
            time_increment = min(end_sleep_time - time.monotonic(), watchdog_timeout)

            time.sleep(time_increment)

            # Pet the watchdog on wake
            self.watchdog.pet()
