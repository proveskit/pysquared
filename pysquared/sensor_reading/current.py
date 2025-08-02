"""Current sensor reading."""

from .base import Reading


class Current(Reading):
    """Current sensor reading in milliamps (mA)."""

    _value: float
    """Current in milliamps (mA)."""

    def __init__(self, value: float) -> None:
        """Initialize the current sensor reading.

        Args:
            value: The current in milliamps (mA)
        """
        super().__init__()
        self._value = value

    @property
    def value(self) -> float:
        """Get the current value in milliamps (mA).

        Returns:
            The current in milliamps (mA).
        """
        return self._value
