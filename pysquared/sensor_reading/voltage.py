"""Voltage sensor reading."""

from .base import Reading


class Voltage(Reading):
    """Voltage sensor reading."""

    value: float
    """Voltage in volts (V)"""

    def __init__(self, value: float) -> None:
        """Initialize the voltage sensor reading in volts (V).

        Args:
            value: The voltage in volts (V)
        """
        super().__init__()
        self.value = value
