"""Lux sensor reading."""

from .base import Reading


class Lux(Reading):
    """Lux sensor reading in SI lux."""

    value: float
    """Light level in SI lux."""

    def __init__(self, value: float) -> None:
        """Initialize the lux sensor reading.

        :param value: The light level in SI lux
        :type value: float
        """
        super().__init__()
        self.value = value
