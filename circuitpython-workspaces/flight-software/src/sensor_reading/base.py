"""A sensor reading."""

import time

from ..protos.reading import ReadingProto

try:
    from typing import Tuple
except ImportError:
    pass


class Reading(ReadingProto):
    """A sensor reading."""

    def __init__(self) -> None:
        """Initialize the sensor reading with a timestamp."""
        self._timestamp = time.time()

    @property
    def timestamp(self):
        """Get the timestamp of the reading."""
        return self._timestamp

    @property
    def value(self) -> Tuple[float, float, float] | float:
        """Get the value of the reading.

        This method should be overridden by subclasses to return the specific sensor reading value.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def to_dict(self) -> dict:
        """Convert reading to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp,
            "value": self.value,
        }
