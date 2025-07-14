"""Current sensor reading."""

from .base import Reading


class Current(Reading):
    """Current sensor reading in milliamps (mA)."""

    value: float
    """Current in milliamps (mA)."""

    def __init__(self, value: float) -> None:
        """Initialize the current sensor reading.

        :param value: The current milliamps (mA)
        :type value: float
        """
        super().__init__()
        self.value = value
