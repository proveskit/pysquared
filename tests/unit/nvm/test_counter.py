from unittest.mock import MagicMock, patch

import pysquared.nvm.counter as counter
from mocks.circuitpython.byte_array import ByteArray


@patch("pysquared.nvm.counter.microcontroller")
def test_counter_bounds(mock_microcontroller: MagicMock):
    """
    Test that the counter class correctly handles values that are inside and outside the bounds of its bit length
    """
    datastore = ByteArray(size=1)
    mock_microcontroller.nvm = datastore

    index = 0
    count = counter.Counter(index)
    assert count.get() == 0

    count.increment()
    assert count.get() == 1

    datastore[index] = 255
    assert count.get() == 255

    count.increment()
    assert count.get() == 0


@patch("pysquared.nvm.counter.microcontroller")
def test_writing_to_multiple_counters_in_same_datastore(
    mock_microcontroller: MagicMock,
):
    datastore = ByteArray(size=2)
    mock_microcontroller.nvm = datastore

    count_1 = counter.Counter(0)
    count_2 = counter.Counter(1)

    count_2.increment()
    assert count_1.get() == 0
    assert count_2.get() == 1
