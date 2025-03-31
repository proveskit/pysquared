import gc
import time

import alarm
import digitalio

from lib.pysquared.logger import Logger
from lib.pysquared.pysquared import Satellite

try:
    from typing import Literal

    import circuitpython_typing
except Exception:
    pass


class SleepHelper:
    """
    Class responsible for sleeping the Satellite to conserve power
    """

    def __init__(self, cubesat: Satellite, logger: Logger):
        """
        Creates a SleepHelper object.

        :param cubesat: The Satellite object
        :param logger: The Logger object allowing for log output

        """
        self.cubesat: Satellite = cubesat
        self.logger: Logger = logger

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
            time_alarm: circuitpython_typing.Alarm = alarm.time.TimeAlarm(
                monotonic_time=time.monotonic() + 15
            )

            alarm.light_sleep_until_alarms(time_alarm)
            duration -= 15
            iterations += 1

    def short_hibernate(self) -> Literal[True]:
        """Puts the Satellite to sleep for 120 seconds"""

        self.logger.debug("Short Hibernation Coming UP")
        gc.collect()
        # all should be off from cubesat powermode

        # checking the type of self.cubesat.enable_rf, as it can be a DigitalInOut object or a bool.
        if isinstance(self.cubesat.enable_rf, digitalio.DigitalInOut):
            self.cubesat.enable_rf.value = False
        else:
            self.cubesat.enable_rf = False

        self.cubesat.f_softboot.toggle(True)

        self.safe_sleep(120)

        # checking the type of self.cubesat.enable_rf, as it can be a DigitalInOut object or a bool.
        if isinstance(self.cubesat.enable_rf, digitalio.DigitalInOut):
            self.cubesat.enable_rf.value = True
        else:
            self.cubesat.enable_rf = True

        return True

    def long_hibernate(self) -> Literal[True]:
        """Puts the Satellite to sleep for 180 seconds"""

        self.logger.debug("LONG Hibernation Coming UP")
        gc.collect()
        # all should be off from cubesat powermode

        # checking the type of self.cubesat.enable_rf, as it can be a DigitalInOut object or a bool.
        if isinstance(self.cubesat.enable_rf, digitalio.DigitalInOut):
            self.cubesat.enable_rf.value = False
        else:
            self.cubesat.enable_rf = False

        self.cubesat.f_softboot.toggle(True)

        self.safe_sleep(600)

        # checking the type of self.cubesat.enable_rf, as it can be a DigitalInOut object or a bool.
        if isinstance(self.cubesat.enable_rf, digitalio.DigitalInOut):
            self.cubesat.enable_rf.value = True
        else:
            self.cubesat.enable_rf = True

        return True
