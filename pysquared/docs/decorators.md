# Hardware Decorators

### decorators Module
This module provides decorators for hardware initialization and error handling, including retry logic with exponential backoff for robust hardware setup.

#### Imports
```py title="decorators.py"
import time

from .exception import HardwareInitializationError
```

### Retry Decorator

#### Function: `with_retries`
A decorator that retries hardware initialization functions with exponential backoff. Useful for robust hardware setup where initialization may intermittently fail.

##### Arguments
- **max_attempts** (int): Maximum number of attempts to try initialization (default 3).
- **initial_delay** (float): Initial delay in seconds between attempts (default 1.0).

##### Raises
- **HardwareInitializationError**: If all attempts fail, the last exception is raised.

##### Returns
- **function**: The result of the decorated function if successful.

```py title="decorators.py"
def with_retries(max_attempts: int = 3, initial_delay: float = 1.0):

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
```