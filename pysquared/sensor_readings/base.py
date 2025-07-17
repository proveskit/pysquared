"""A sensor reading."""

import time


class Reading:
    """A sensor reading."""

    def __init__(self) -> None:
        """Initialize the sensor reading with a timestamp."""
        self.timestamp = time.time()
