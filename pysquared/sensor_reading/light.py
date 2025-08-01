"""Light sensor reading."""

from .base import Reading


class Light(Reading):
    """Light sensor reading (non-unit-specific light levels)."""

    value: float
    """Light level (non-unit-specific)."""

    def __init__(self, value: float) -> None:
        """Initialize the light sensor reading.

        Args:
            value: The light level (non-unit-specific)
        """
        super().__init__()
        self.value = value
