"""
Protocol defining the interface for a Real Time Clock (RTC).
"""


class RTCProto:
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
        ...
