"""This protocol specifies the interface that any Real-Time Clock (RTC) implementation
must adhere to, ensuring consistent behavior across different RTC hardware.
"""


class RTCProto:
    """Protocol defining the interface for a Real Time Clock (RTC)."""

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
        ...
