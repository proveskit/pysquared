"""Protocol to define the logger interface."""


class LoggerProto:
    """Protocol defining the interface for a logger."""

    def debug(self, message: str, **kwargs) -> None:
        """Logs a message with DEBUG level."""
        ...

    def info(self, message: str, **kwargs) -> None:
        """Logs a message with INFO level."""
        ...

    def warning(self, message: str, **kwargs) -> None:
        """Logs a message with WARNING level."""
        ...

    def error(self, message: str, err: Exception, **kwargs) -> None:
        """Logs a message with ERROR level, including an exception."""
        ...

    def critical(self, message: str, err: Exception, **kwargs: object) -> None:
        """Logs a message with CRITICAL level, including an exception."""
        ...
