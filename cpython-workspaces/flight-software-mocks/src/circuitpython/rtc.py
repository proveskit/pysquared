"""Mock for the CircuitPython RTC module.

This module provides a mock implementation of the CircuitPython RTC module for
testing purposes. It allows for simulating the behavior of the RTC module without
the need for actual hardware.
"""

from time import struct_time


class RTC:
    """A mock RTC that can be used as a singleton."""

    _instance = None
    datetime: struct_time | None = None

    def __new__(cls):
        """Creates a new RTC instance if one does not already exist."""
        if cls._instance is None:
            cls._instance = super(RTC, cls).__new__(cls)
            cls._instance.datetime = None
        return cls._instance

    @classmethod
    def destroy(cls):
        """Destroys the RTC instance."""
        cls._instance = None
