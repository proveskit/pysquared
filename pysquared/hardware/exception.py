"""This module provides a custom exception for hardware initialization errors.

This exception is raised when a hardware component fails to initialize after a
certain number of retries.

**Usage:**
```python
raise HardwareInitializationError("Failed to initialize the IMU.")
```
"""


class HardwareInitializationError(Exception):
    """Exception raised for errors in hardware initialization."""

    pass
