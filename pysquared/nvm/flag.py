"""This module provides the Flag class for managing boolean flags stored in
non-volatile memory (NVM) on CircuitPython devices.
"""

import microcontroller


class Flag:
    """
    Flag class for managing boolean flags stored in non-volatile memory.

    Attributes:
        _index (int): The index of the flag (byte) in the NVM datastore.
        _bit (int): The bit index within the byte.
        _datastore (microcontroller.nvm.ByteArray): The NVM datastore.
        _bit_mask (int): Bitmask for the flag's bit position.
    """

    def __init__(
        self,
        index: int,
        bit_index: int,
    ) -> None:
        """
        Initializes a Flag instance.

        Args:
            index (int): The index of the flag (byte) in the datastore.
            bit_index (int): The index of the bit within the byte.

        Raises:
            ValueError: If NVM is not available.
        """
        self._index = index
        self._bit = bit_index

        if microcontroller.nvm is None:
            raise ValueError("nvm is not available")

        self._datastore = microcontroller.nvm  # Array of bytes (Non-volatile Memory)
        self._bit_mask = 1 << bit_index  # Creating bitmask with bit position
        # Ex. bit = 3 -> 3 % 8 = 3 -> 1 << 3 = 00001000

    def get(self) -> bool:
        """
        Returns the value of the flag.

        Returns:
            bool: The current value of the flag.
        """
        return bool(self._datastore[self._index] & self._bit_mask)

    def toggle(self, value: bool) -> None:
        """
        Sets or clears the flag value.

        Args:
            value (bool): If True, sets the flag; if False, clears the flag.
        """
        if value:
            # If true, perform OR on specific byte and bitmask to set bit to 1
            self._datastore[self._index] |= self._bit_mask
        else:
            # If false, perform AND on specific byte and inverted bitmask to set bit to 0
            self._datastore[self._index] &= ~self._bit_mask

    def get_name(self) -> str:
        """
        get_name returns the name of the flag
        """
        return f"{self.__class__.__name__}_index_{self._index}_bit_{self._bit}"
