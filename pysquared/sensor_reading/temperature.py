"""Temperature sensor reading."""

from .base import Reading


class Temperature(Reading):
    """Temperature sensor reading in degrees celsius."""

    value: float
    """Temperature in degrees celsius."""

    def __init__(self, value: float) -> None:
        """Initialize the temperature sensor reading.

        Args:
            value: Temperature in degrees Celsius.
        """
        super().__init__()
        self.value = value
