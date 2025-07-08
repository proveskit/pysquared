"""Mock for the CircuitPython bytearray.

This module provides a mock implementation of the CircuitPython bytearray for
testing purposes. It allows for simulating the behavior of the bytearray without the
need for actual hardware.

Usage:
    mem = ByteArray(10)
    mem[0] = 1
    value = mem[0]
"""


class ByteArray:
    """A mock bytearray that simulates the CircuitPython non-volatile memory API."""

    def __init__(self, size: int = 1024) -> None:
        """Initializes the mock bytearray.

        Args:
            size: The size of the bytearray.
        """
        self.memory = bytearray(size)

    def __getitem__(self, index: slice | int) -> bytearray | int:
        """Gets an item from the bytearray.

        Args:
            index: The index of the item to get.

        Returns:
            The item at the given index.
        """
        if isinstance(index, slice):
            return bytearray(self.memory[index])
        return int(self.memory[index])

    def __setitem__(self, index: int, value: int) -> None:
        """Sets an item in the bytearray.

        Args:
            index: The index of the item to set.
            value: The value to set.
        """
        self.memory[index] = value
