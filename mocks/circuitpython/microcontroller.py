"""Mock for the CircuitPython microcontroller module.

This module provides a mock implementation of the CircuitPython microcontroller module
for testing purposes. It allows for simulating the behavior of the microcontroller
module without the need for actual hardware.

Usage:
    temp = microcontroller.Processor.temperature
"""


class Pin:
    """A mock Pin."""

    pass


class Processor:
    """A mock Processor."""

    temperature = 35.0
