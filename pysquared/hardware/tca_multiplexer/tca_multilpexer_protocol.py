"""
This module defines a protocol for creating TCA Multiplexer instances.
This is useful for defining an interface that can be implemented by different classes
for different types of TCA Multiplexers. This allows for flexibility in the design of the system,
enabling the use of different TCA Multiplexer implementations without changing the code that uses them.

CircuitPython does not support Protocols directly, but this class can still be used to define an interface

https://docs.python.org/3/library/typing.html#typing.Protocol
"""

# type-hinting only
try:
    from busio import I2C
except ImportError:
    pass


class TCAMultiplexerProto:
    """Protocol for the TCA Multiplexer."""

    def get_i2c_device(self, channel: int) -> I2C | None:
        """ """
        ...

    def scan_channel(self, channel: int, valid_addresses: list[int]) -> list[int]:
        """ """
        ...
