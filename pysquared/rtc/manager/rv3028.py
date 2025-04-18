from busio import I2C
from rv3028.rv3028 import RV3028

from ...hardware.decorators import with_retries
from ...hardware.exception import HardwareInitializationError
from ...logger import Logger
from ...protos.rtc import RTCProto


class RV3028Manager(RTCProto):
    """Manager class for creating RV3028 RTC instances.
    The purpose of the manager class is to hide the complexity of RTC initialization from the caller.
    Specifically we should try to keep adafruit_lis2mdl to only this manager class.
    """

    @with_retries(max_attempts=3, initial_delay=1)
    def __init__(
        self,
        logger: Logger,
        i2c: I2C,
    ) -> None:
        """Initialize the manager class.

        :param Logger logger: Logger instance for logging messages.
        :param busio.I2C i2c: The I2C bus connected to the chip.

        :raises HardwareInitializationError: If the RTC fails to initialize.
        """
        self._log: Logger = logger

        try:
            self._log.debug("Initializing RTC")

            self._rtc: RV3028 = RV3028(i2c)
            self._rtc.configure_backup_switchover(mode="level", interrupt=True)
        except Exception as e:
            raise HardwareInitializationError("Failed to initialize RTC") from e

    def set_time(
        self,
        year: int,
        month: int,
        date: int,
        hour: int,
        minute: int,
        second: int,
        weekday: int,
    ) -> None:
        """Set the time on the real time clock.

        :param year: The year value (0-9999)
        :param month: The month value (1-12)
        :param date: The date value (1-31)
        :param hour: The hour value (0-23)
        :param minute: The minute value (0-59)
        :param second: The second value (0-59)
        :param weekday: The nth day of the week (0-6), where 0 represents Sunday and 6 represents Saturday

        :raises Exception: If there is an error setting the values.
        """
        try:
            self._rtc.set_date(year, month, date, weekday)
            self._rtc.set_time(hour, minute, second)
        except Exception as e:
            self._log.error("Error setting RTC time", e)

    def get_time(self):
        try:
            self._rtc.get_time()

        except Exception as e:
            self._log.error("Error getting RTC time", e)

    def get_date(self):
        try:
            self._rtc.get_date()

        except Exception as e:
            self._log.error("Error getting RTC date", e)

    def set_alarm(
        self, minute: int = None, hour: int = None, weekday: int = None
    ) -> None:
        try:
            self._rtc.set_alarm(minute, hour, weekday)

        except Exception as e:
            self._log.error("Error setting alarm", e)

    def check_alarm(self, clear: bool = True) -> bool:
        try:
            self._rtc.check_alarm(clear)

        except Exception as e:
            self._log.error("Error checking alarm", e)

    def get_alarm(self) -> tuple:
        try:
            self._rtc.get_alarm()

        except Exception as e:
            self._log.error("Error getting alarm", e)
