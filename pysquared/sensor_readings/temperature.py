"""Temperature sensor reading."""

from .base import Reading


class Temperature(Reading):
    """Temperature sensor reading in degrees celsius."""

    value: float
    """Temperature in degrees celsius."""

    def __init__(self, value: float) -> None:
        """Initialize the temperature sensor reading.

        :param value: The temperature in degrees celsius.
        :type value: float
        """
        super().__init__()
        self.value = value
