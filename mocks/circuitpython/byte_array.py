from typing import Union

from circuitpython_typing import ReadableBuffer


class ByteArray:
    """
    ByteArray is a class that mocks the implementaion of the CircuitPython non-volatile memory API.
    """

    def __init__(self, size: int = 1024) -> None:
        self.memory = bytearray(size)

    def __getitem__(self, index: Union[slice, int]) -> Union[bytearray, int]:
        if isinstance(index, slice):
            return bytearray(self.memory[index])
        return int(self.memory[index])

    def __setitem__(
        self, index: Union[slice, int], value: Union[ReadableBuffer, int]
    ) -> None:
        self.memory[index] = value
