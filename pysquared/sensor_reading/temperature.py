"""Temperature sensor reading."""

from .base import Reading


class Temperature(Reading):
    """Temperature sensor reading in degrees celsius."""

    _value: float
    """Temperature in degrees celsius."""

    def __init__(self, value: float) -> None:
        """Initialize the temperature sensor reading.

        Args:
            value: Temperature in degrees Celsius.
        """
        super().__init__()
        self._value = value

    @property
    def value(self) -> float:
        """Get the temperature value in degrees celsius.

        Returns:
            The temperature in degrees Celsius.
        """
        return self._value
