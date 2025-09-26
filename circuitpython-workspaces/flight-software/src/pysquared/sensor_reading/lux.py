"""Lux sensor reading."""

from .base import Reading


class Lux(Reading):
    """Lux sensor reading in SI lux."""

    _value: float
    """Light level in SI lux."""

    def __init__(self, value: float) -> None:
        """Initialize the lux sensor reading.

        Args:
            value: The light level in SI lux
        """
        super().__init__()
        self._value = value

    @property
    def value(self) -> float:
        """Get the light level in SI lux.

        Returns:
            The light level in SI lux.
        """
        return self._value
