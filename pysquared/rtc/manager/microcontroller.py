"""This module provides a manager for the Microcontroller's Real-Time Clock (RTC).

This module defines the `MicrocontrollerManager` class, which provides an interface
for interacting with the microcontroller's built-in RTC. It allows for setting
the current time.

**Usage:**
```python
rtc_manager = MicrocontrollerManager()
rtc_manager.set_time(2024, 7, 8, 10, 30, 0, 1) # Set to July 8, 2024, 10:30:00 AM, Monday
```
"""

import time

from ...protos.rtc import RTCProto

try:
    import mocks.circuitpython.rtc as rtc
except ImportError:
    import rtc


class MicrocontrollerManager(RTCProto):
    """Manages the Microcontroller's Real Time Clock (RTC)."""

    def __init__(self) -> None:
        """Initializes the RTC.

        This method is required on every boot to ensure the RTC is ready for use.
        """
        microcontroller_rtc = rtc.RTC()
        microcontroller_rtc.datetime = time.localtime()

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
        """Updates the Microcontroller's Real Time Clock (RTC).

        Args:
            year: The year value (0-9999).
            month: The month value (1-12).
            date: The date value (1-31).
            hour: The hour value (0-23).
            minute: The minute value (0-59).
            second: The second value (0-59).
            weekday: The nth day of the week (0-6), where 0 represents Sunday and 6 represents Saturday.
        """
        microcontroller_rtc = rtc.RTC()
        microcontroller_rtc.datetime = time.struct_time(
            (year, month, date, hour, minute, second, weekday, -1, -1)
        )
