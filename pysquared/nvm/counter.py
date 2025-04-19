import microcontroller


class Counter:
    """
    Counter class for managing 8-bit counters stored in non-volatile memory
    """

    def __init__(
        self,
        index: int,
    ) -> None:
        """Initialize a Counter instance.

        :param index int: The index of the counter in the datastore.
        :param datastore ByteArray: The non-volatile memory datastore where the counter is stored.
            Expected to be of type `microcontroller.nvm.ByteArray`.
        """
        self._index = index

        if microcontroller.nvm is None:
            raise ValueError("nvm is not available")

        self._datastore = microcontroller.nvm

    def get(self) -> int:
        """
        get returns the value of the counter
        """
        return self._datastore[self._index]

    def increment(self) -> None:
        """
        increment increases the counter by one
        """
        value: int = (self.get() + 1) & 0xFF  # 8-bit counter with rollover
        self._datastore[self._index] = value
