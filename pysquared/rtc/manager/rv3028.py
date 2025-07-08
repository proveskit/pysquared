"""This module provides a manager for the RV3028 Real-Time Clock (RTC).

This module defines the `RV3028Manager` class, which provides a high-level interface
for interacting with the RV3028 RTC. It handles the initialization of the sensor
and provides methods for setting the current time.

**Usage:**
```python
logger = Logger()
i2c = busio.I2C(board.SCL, board.SDA)
rtc_manager = RV3028Manager(logger, i2c)
rtc_manager.set_time(2024, 7, 8, 10, 30, 0, 1) # Set to July 8, 2024, 10:30:00 AM, Monday
```
"""

from busio import I2C
from rv3028.rv3028 import RV3028

from ...hardware.exception import HardwareInitializationError
from ...logger import Logger
from ...protos.rtc import RTCProto


class RV3028Manager(RTCProto):
    """Manages the RV3028 RTC."""

    def __init__(
        self,
        logger: Logger,
        i2c: I2C,
    ) -> None:
        """Initializes the RV3028Manager.

        Args:
            logger: The logger to use.
            i2c: The I2C bus connected to the chip.

        Raises:
            HardwareInitializationError: If the RTC fails to initialize.
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
        """Sets the time on the real-time clock.

        Args:
            year: The year value (0-9999).
            month: The month value (1-12).
            date: The date value (1-31).
            hour: The hour value (0-23).
            minute: The minute value (0-59).
            second: The second value (0-59).
            weekday: The nth day of the week (0-6), where 0 represents Sunday and 6 represents Saturday.

        Raises:
            Exception: If there is an error setting the values.
        """
        try:
            self._rtc.set_date(year, month, date, weekday)
            self._rtc.set_time(hour, minute, second)
        except Exception as e:
            self._log.error("Error setting RTC time", e)
