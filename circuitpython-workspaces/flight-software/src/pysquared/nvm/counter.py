"""This module provides the Counter class for managing 8-bit counters stored in
non-volatile memory (NVM) on CircuitPython devices.
"""

import microcontroller


class Counter:
    """
    Counter class for managing 8-bit counters stored in non-volatile memory.

    Attributes:
        _index (int): The index of the counter in the NVM datastore.
        _datastore (microcontroller.nvm.ByteArray): The NVM datastore.
    """

    def __init__(
        self,
        index: int,
    ) -> None:
        """
        Initializes a Counter instance.

        Args:
            index (int): The index of the counter in the datastore.

        Raises:
            ValueError: If NVM is not available.
        """
        self._index = index

        if microcontroller.nvm is None:
            raise ValueError("nvm is not available")

        self._datastore = microcontroller.nvm

    def get(self) -> int:
        """
        Returns the value of the counter.

        Returns:
            int: The current value of the counter.
        """
        return self._datastore[self._index]

    def increment(self) -> None:
        """
        Increases the counter by one, with 8-bit rollover.
        """
        value: int = (self.get() + 1) & 0xFF  # 8-bit counter with rollover
        self._datastore[self._index] = value

    def get_name(self) -> str:
        """
        get_name returns the name of the counter
        """
        return f"{self.__class__.__name__}_index_{self._index}"


class Counter16:
    """
    Counter class for managing 16-bit counters stored in non-volatile memory.

    Uses two consecutive bytes in NVM to store a 16-bit counter value.
    This provides a larger range (0-65535) before wraparound occurs.

    Attributes:
        _index (int): The starting index of the counter in the NVM datastore.
        _datastore (microcontroller.nvm.ByteArray): The NVM datastore.
    """

    def __init__(
        self,
        index: int,
    ) -> None:
        """
        Initializes a Counter16 instance.

        Args:
            index (int): The starting index of the counter in the datastore.
                        Uses two consecutive bytes (index and index+1).

        Raises:
            ValueError: If NVM is not available.
        """
        self._index = index

        if microcontroller.nvm is None:
            raise ValueError("nvm is not available")

        self._datastore = microcontroller.nvm

    def get(self) -> int:
        """
        Returns the value of the counter.

        Returns:
            int: The current value of the counter (0-65535).
        """
        # Read two bytes: high byte at _index, low byte at _index+1
        high_byte = self._datastore[self._index]
        low_byte = self._datastore[self._index + 1]
        return (high_byte << 8) | low_byte

    def set(self, value: int) -> None:
        """
        Sets the counter to a specific value.

        Args:
            value: The value to set (0-65535).
        """
        value = value & 0xFFFF  # Ensure 16-bit value
        high_byte = (value >> 8) & 0xFF
        low_byte = value & 0xFF
        self._datastore[self._index] = high_byte
        self._datastore[self._index + 1] = low_byte

    def increment(self) -> None:
        """
        Increases the counter by one, with 16-bit rollover.
        """
        value: int = (self.get() + 1) & 0xFFFF  # 16-bit counter with rollover
        self.set(value)

    def get_name(self) -> str:
        """
        get_name returns the name of the counter
        """
        return f"{self.__class__.__name__}_index_{self._index}"
