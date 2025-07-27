"""
Error Counter Middleware for Logger

This module provides a middleware for the Logger records the number of errors logged to a non-volatile memory (NVM) counter.

Usage:
```python
from .nvm.counter import Counter
from .logger.default_logger import DefaultLogger
from .logger.middleware.error_counter.error_counter import add_logger_middleware_error_counter
count = Counter(0)
logger = DefaultLogger()
logger = add_logger_middleware_error_counter(count)(logger)
logger.critical("Test critical error", err=Exception("Test exception"))
```
"""

try:
    from typing import Callable
except ImportError:
    pass

from ....nvm.counter import Counter
from ...logger_proto import LoggerProto


def add_logger_middleware_error_counter(
    counter: Counter,
) -> Callable[[LoggerProto], LoggerProto]:
    """Adds error counting middleware to a logger.

    Args:
        counter (Counter): Counter for error occurrences.
    Returns:
        Callable[[LoggerProto], LoggerProto]: A function that takes a logger and returns a new logger with error counting middleware.
    """
    return lambda next_logger: ErrorCountLogger(counter, next_logger)


class ErrorCountLogger(LoggerProto):
    """
    Logger that counts the number of errors logged.
    """

    def __init__(self, counter: Counter, next_logger: LoggerProto) -> None:
        """
        Initializes the ErrorCountLogger instance.

        Args:
            error_counter (Counter): Counter for error occurrences.
        """
        self._counter: Counter = counter
        self._next_logger: LoggerProto = next_logger

    def debug(self, message: str, **kwargs: object) -> None:
        """
        Log a message with severity level DEBUG.

        Args:
            message (str): The log message.
            **kwargs: Additional key/value pairs to include in the log.
        """
        self._next_logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs: object) -> None:
        """
        Log a message with severity level INFO.

        Args:
            message (str): The log message.
            **kwargs: Additional key/value pairs to include in the log.
        """
        self._next_logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs: object) -> None:
        """
        Log a message with severity level WARNING.

        Args:
            message (str): The log message.
            **kwargs: Additional key/value pairs to include in the log.
        """
        self._next_logger.warning(message, **kwargs)

    def error(self, message: str, err: Exception, **kwargs: object) -> None:
        """
        Log a message with severity level ERROR.

        Args:
            message (str): The log message.
            err (Exception): The exception to log.
            **kwargs: Additional key/value pairs to include in the log.
        """
        self._counter.increment()
        self._next_logger.error(message, err, **kwargs)

    def critical(self, message: str, err: Exception, **kwargs: object) -> None:
        """
        Log a message with severity level CRITICAL.

        Args:
            message (str): The log message.
            err (Exception): The exception to log.
            **kwargs: Additional key/value pairs to include in the log.
        """
        self._counter.increment()
        self._next_logger.critical(message, err, **kwargs)

    def get_error_count(self) -> int:
        """
        Returns the current error count.

        Returns:
            int: The number of errors logged.
        """
        return self._counter.get()
