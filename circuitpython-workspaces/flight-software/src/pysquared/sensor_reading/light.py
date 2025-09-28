"""Light sensor reading."""

from .base import Reading


class Light(Reading):
    """Light sensor reading (non-unit-specific light levels)."""

    _value: float
    """Light level (non-unit-specific)."""

    def __init__(self, value: float) -> None:
        """Initialize the light sensor reading.

        Args:
            value: The light level (non-unit-specific)
        """
        super().__init__()
        self._value = value

    @property
    def value(self) -> float:
        """Get the light level (non-unit-specific).

        Returns:
            The light level (non-unit-specific).
        """
        return self._value
