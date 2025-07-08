"""This module provides decorators for hardware initialization and error handling.

This module includes decorators that add retry logic with exponential backoff to
functions, which is particularly useful for robust hardware initialization.

Usage:
    @with_retries(max_attempts=3, initial_delay=1.0)
    def initialize_my_hardware():
        # Hardware initialization code that might fail
        pass
"""

import time

from .exception import HardwareInitializationError


def with_retries(max_attempts: int = 3, initial_delay: float = 1.0):
    """Decorator that retries a function with exponential backoff.

    This decorator is designed to wrap functions that might fail due to transient
    issues, such as hardware initialization. It will retry the function up to a
    specified number of times, with an increasing delay between each attempt.

    Args:
        max_attempts: The maximum number of attempts to try the function.
        initial_delay: The initial delay in seconds between attempts.

    Returns:
        The result of the decorated function if successful.

    Raises:
        HardwareInitializationError: If all attempts fail, the last exception is raised.
    """

    def decorator(func):
        """The decorator function."""

        def wrapper(*args, **kwargs):
            """The wrapper function that implements the retry logic."""
            last_exception = Exception("with_retries decorator had unknown error")
            delay = initial_delay

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except HardwareInitializationError as e:
                    last_exception = e
                    if attempt < max_attempts - 1:  # Don't sleep on last attempt
                        time.sleep(delay)
                        delay *= 2  # Exponential backoff

            # If we get here, all attempts failed
            raise last_exception

        return wrapper

    return decorator
