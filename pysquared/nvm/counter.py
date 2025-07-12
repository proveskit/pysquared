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
