import time

from ...protos.rtc import RTCProto

try:
    import mocks.circuitpython.rtc as rtc
except ImportError:
    import rtc


class MicrocontrollerManager(RTCProto):
    """
    Class for interfacing with the Microcontroller's Real Time Clock (RTC) via CircuitPython.

    rtc.RTC is a singleton and does not need to be stored as a class variable.
    """

    def __init__(self) -> None:
        """
        Initialize the RTC

        Required on every boot to ensure the RTC is ready for use
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
        day_of_week: int,
    ) -> None:
        """
        Updates the Microcontroller's Real Time Clock (RTC) to the date and time passed

        :param year: The year value (0-9999)
        :param month: The month value (1-12)
        :param date: The date value (1-31)
        :param hour: The hour value (0-23)
        :param minute: The minute value (0-59)
        :param second: The second value (0-59)
        :param day_of_week: The nth day of the week (0-6), where 0 represents Sunday and 6 represents Saturday
        """
        microcontroller_rtc = rtc.RTC()
        microcontroller_rtc.datetime = time.struct_time(
            (year, month, date, hour, minute, second, day_of_week, -1, -1)
        )
