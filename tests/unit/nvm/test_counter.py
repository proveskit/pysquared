"""Unit tests for the Counter class in the NVM module.

This module contains unit tests for the `Counter` class, which provides a
persistent counter stored in non-volatile memory (NVM). The tests cover
counter initialization, incrementing, and handling of NVM availability.
"""

from unittest.mock import MagicMock, patch

import pytest

import pysquared.nvm.counter as counter
from mocks.circuitpython.byte_array import ByteArray


@patch("pysquared.nvm.counter.microcontroller")
def test_counter_bounds(mock_microcontroller: MagicMock):
    """Tests that the counter class correctly handles values that are inside and outside the bounds of its bit length.

    Args:
        mock_microcontroller: Mocked microcontroller module.
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
    """Tests writing to multiple counters that share the same datastore.

    Args:
        mock_microcontroller: Mocked microcontroller module.
    """
    datastore = ByteArray(size=2)
    mock_microcontroller.nvm = datastore

    count_1 = counter.Counter(0)
    count_2 = counter.Counter(1)

    count_2.increment()
    assert count_1.get() == 0
    assert count_2.get() == 1


@patch("pysquared.nvm.counter.microcontroller")
def test_counter_raises_error_when_nvm_is_none(mock_microcontroller: MagicMock):
    """Tests that the Counter raises a ValueError when NVM is not available.

    Args:
        mock_microcontroller: Mocked microcontroller module.
    """
    mock_microcontroller.nvm = None

    with pytest.raises(ValueError, match="nvm is not available"):
        counter.Counter(0)


@patch("pysquared.nvm.counter.microcontroller")
def test_get_name(mock_microcontroller: MagicMock):
    """Tests the get_name method of the Counter class.

    Args:
        mock_microcontroller: Mocked microcontroller module.
    """
    datastore = ByteArray(size=2)
    mock_microcontroller.nvm = datastore

    count = counter.Counter(0)
    assert count.get_name() == "Counter_index_0"
