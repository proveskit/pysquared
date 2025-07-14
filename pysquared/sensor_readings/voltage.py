"""Voltage sensor reading."""

from .base import Reading


class Voltage(Reading):
    """Voltage sensor reading."""

    value: float
    """Voltage in volts (V)"""

    def __init__(self, value: float) -> None:
        """Initialize the voltage sensor reading in volts (V).

        :param value: The voltage in volts (V)
        :type value: float
        """
        super().__init__()
        self.value = value
