"""
This module defines hardware agnostic protocols for accessing devices with certain features.
This allows for flexibility in the design of the system, enabling the use of different hardware
implementations without changing the code that uses them.

CircuitPython does not support Protocols directly, but these classes can still be used to define
an interface for type checking and ensuring multi-device compatibility.

https://docs.python.org/3/library/typing.html#typing.Protocol
"""
