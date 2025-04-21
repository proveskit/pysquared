import microcontroller


class Flag:
    """
    Flag class for managing boolean flags stored in non-volatile memory
    """

    def __init__(
        self,
        index: int,
        bit_index: int,
    ) -> None:
        """Initialize a Flag instance.

        :param index int: The index of the flag (byte) in the datastore (array of bytes).
        :param bit_index int: The index of the bit within the byte.
        """
        self._index = index
        self._bit = bit_index

        if microcontroller.nvm is None:
            raise ValueError("nvm is not available")

        self._datastore = microcontroller.nvm  # Array of bytes (Non-volatile Memory)
        self._bit_mask = 1 << bit_index  # Creating bitmask with bit position
        # Ex. bit = 3 -> 3 % 8 = 3 -> 1 << 3 = 00001000

    def get(self) -> bool:
        """Get flag value"""
        return bool(self._datastore[self._index] & self._bit_mask)

    def toggle(self, value: bool) -> None:
        """Toggle flag value"""
        if value:
            # If true, perform OR on specific byte and bitmask to set bit to 1
            self._datastore[self._index] |= self._bit_mask
        else:
            # If false, perform AND on specific byte and inverted bitmask to set bit to 0
            self._datastore[self._index] &= ~self._bit_mask

    def get_name(self) -> str:
        """
        get_name returns the name of the counter
        """
        return f"{self.__class__.__name__}_idx_{self._index}_bit_{self._bit}"
