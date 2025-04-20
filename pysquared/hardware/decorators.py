import time

from .exception import HardwareInitializationError


def with_retries(max_attempts: int = 3, initial_delay: float = 1.0):
    """Decorator that retries hardware initialization with exponential backoff.

    :param int max_attempts: Maximum number of attempts to try initialization (default is 3)
    :param int initial_delay: Initial delay in seconds between attempts (default is 1.0)

    :raises HardwareInitializationError: If all attempts fail, the last exception is raised

    :returns: The result of the decorated function if successful
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
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
