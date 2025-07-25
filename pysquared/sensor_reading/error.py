"""This file contains custom error classes for handling sensor reading errors."""


class SensorReadingError(Exception):
    """Base class for all sensor reading errors."""

    pass


class SensorReadingTimeoutError(SensorReadingError):
    """Raised when a sensor reading operation times out."""

    def __init__(self, message: str = "Sensor reading operation timed out.") -> None:
        """Initialize the timeout error with a custom message."""
        super().__init__(message)


class SensorReadingValueError(SensorReadingError):
    """Raised when a sensor reading returns an invalid value."""

    def __init__(
        self, message: str = "Sensor reading returned an invalid value."
    ) -> None:
        """Initialize the value error with a custom message."""
        super().__init__(message)


class SensorReadingUnknownError(SensorReadingError):
    """Raised when an unknown error occurs during sensor reading."""

    def __init__(
        self, message: str = "An unknown error occurred during sensor reading."
    ) -> None:
        """Initialize the unknown error with a custom message."""
        super().__init__(message)
