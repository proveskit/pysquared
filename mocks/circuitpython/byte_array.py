from circuitpython_typing import ReadableBuffer


class ByteArray:
    """
    ByteArray is a class that mocks the implementaion of the CircuitPython non-volatile memory API.
    https://docs.circuitpython.org/en/latest/shared-bindings/nvm/index.html
    """

    def __init__(self, size: int = 1024) -> None:
        self.memory = bytearray(size)

    def __getitem__(self, index: slice | int) -> bytearray | int:
        if isinstance(index, slice):
            return bytearray(self.memory[index])
        return int(self.memory[index])

    # def __setitem__(self, index: slice | int, value: int | bytearray | list | tuple) -> None:
    #     if isinstance(index, slice):
    #         if not isinstance(value, (bytearray, list, tuple)) or not all(isinstance(v, int) for v in value):
    #             raise TypeError("Value must be a bytearray, list, or tuple of integers for slice assignment.")
    #         self.memory[index] = bytes(value) if isinstance(value, (bytearray, list, tuple)) else value
    #     else:
    #         self.memory[index] = value if isinstance(value, int) else value[0]

    def __setitem__(self, index: slice | int, value: int | ReadableBuffer) -> None:
        if isinstance(index, slice):
            if not isinstance(value, ReadableBuffer):
                raise TypeError(
                    "Value must be a ReadableBuffer for slice index assignment."
                )

            if isinstance(value, ("rgbmatrix.RGBMatrix", "ulab.numpy.ndarray")):
                raise TypeError(
                    "Value must be a ReadableBuffer for slice index assignment."
                )

            self.memory[index] = value.__rsub__
            # self.memory[index] = bytes(value) if isinstance(value, (array.array, bytearray, memoryview)) else value

        if isinstance(index, int):
            if not isinstance(value, int):
                raise TypeError("Value must be an int for int index assignment.")

            self.memory[index] = value

        raise TypeError("Index must be an int or slice.")


def __setitem__(self, index: slice | int, value: int | ReadableBuffer) -> None:
    if isinstance(index, slice):
        if not isinstance(value, ReadableBuffer):
            raise TypeError(
                "Value must be a ReadableBuffer for slice index assignment."
            )

        self.memory[index] = bytes(value)

    if isinstance(index, int):
        if not isinstance(value, int):
            raise TypeError("Value must be an int for int index assignment.")

        self.memory[index] = value

    raise TypeError("Index must be an int or slice.")
