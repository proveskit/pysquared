"""Mock for the RV3028 real-time clock.

This module provides a mock implementation of the RV3028 real-time clock for testing
purposes. It allows for simulating the behavior of the RV3028 without the need for
actual hardware.

Usage:
    i2c = I2C()
    rv3028 = RV3028(i2c)
    rv3028.set_time(12, 30, 0)
    rv3028.set_date(2024, 1, 1, 1)
"""

from busio import I2C


class RV3028:
    """A mock RV3028 real-time clock."""

    def __init__(self, i2c_bus: I2C) -> None:
        """Initializes the mock RV3028.

        Args:
            i2c_bus: The I2C bus to use.
        """
        ...

    def configure_backup_switchover(self, mode: str, interrupt: bool) -> None:
        """Configures the backup switchover.

        Args:
            mode: The switchover mode.
            interrupt: Whether to enable the interrupt.
        """
        ...

    def set_time(self, hour: int, minute: int, second: int) -> None:
        """Sets the time.

        Args:
            hour: The hour to set.
            minute: The minute to set.
            second: The second to set.
        """
        ...

    def set_date(self, year: int, month: int, date: int, weekday: int) -> None:
        """Sets the date.

        Args:
            year: The year to set.
            month: The month to set.
            date: The date to set.
            weekday: The weekday to set.
        """
        ...
