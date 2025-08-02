"""Voltage sensor reading."""

from .base import Reading


class Voltage(Reading):
    """Voltage sensor reading."""

    _value: float
    """Voltage in volts (V)"""

    def __init__(self, value: float) -> None:
        """Initialize the voltage sensor reading in volts (V).

        Args:
            value: The voltage in volts (V)
        """
        super().__init__()
        self._value = value

    @property
    def value(self) -> float:
        """Get the voltage value in volts (V).

        Returns:
            The voltage in volts (V).
        """
        return self._value
