"""Unit tests for the Counter16 class."""

from unittest.mock import MagicMock, patch

import pysquared.nvm.counter as counter
import pytest
from mocks.circuitpython.byte_array import ByteArray


@patch("pysquared.nvm.counter.microcontroller")
def test_counter16_init(mock_microcontroller: MagicMock):
    """Tests Counter16 initialization.

    Args:
        mock_microcontroller: Mocked microcontroller module.
    """
    datastore = ByteArray(size=512)
    mock_microcontroller.nvm = datastore

    index = 0
    count = counter.Counter16(index)
    assert count.get() == 0


@patch("pysquared.nvm.counter.microcontroller")
def test_counter16_independent_counters(mock_microcontroller: MagicMock):
    """Tests that two counters maintain independent values.

    Args:
        mock_microcontroller: Mocked microcontroller module.
    """
    datastore = ByteArray(size=512)
    mock_microcontroller.nvm = datastore

    count_1 = counter.Counter16(0)
    count_2 = counter.Counter16(2)  # Start at index 2 (skipping 0 and 1)

    count_2.increment()
    assert count_1.get() == 0
    assert count_2.get() == 1


@patch("pysquared.nvm.counter.microcontroller")
def test_counter16_no_nvm(mock_microcontroller: MagicMock):
    """Tests Counter16 initialization failure when NVM is not available.

    Args:
        mock_microcontroller: Mocked microcontroller module.
    """
    mock_microcontroller.nvm = None
    with pytest.raises(ValueError):
        counter.Counter16(0)


@patch("pysquared.nvm.counter.microcontroller")
def test_counter16_set_get(mock_microcontroller: MagicMock):
    """Tests Counter16 set and get methods.

    Args:
        mock_microcontroller: Mocked microcontroller module.
    """
    datastore = ByteArray(size=512)
    mock_microcontroller.nvm = datastore

    count = counter.Counter16(0)
    count.set(1234)
    assert count.get() == 1234


@patch("pysquared.nvm.counter.microcontroller")
def test_counter16_increment(mock_microcontroller: MagicMock):
    """Tests Counter16 increment.

    Args:
        mock_microcontroller: Mocked microcontroller module.
    """
    datastore = ByteArray(size=512)
    mock_microcontroller.nvm = datastore

    count = counter.Counter16(0)
    count.set(0)
    count.increment()
    assert count.get() == 1


@patch("pysquared.nvm.counter.microcontroller")
def test_counter16_rollover(mock_microcontroller: MagicMock):
    """Tests Counter16 16-bit rollover.

    Args:
        mock_microcontroller: Mocked microcontroller module.
    """
    datastore = ByteArray(size=512)
    mock_microcontroller.nvm = datastore

    count = counter.Counter16(0)
    count.set(0xFFFF)  # Max 16-bit value
    count.increment()
    assert count.get() == 0  # Should roll over to 0


@patch("pysquared.nvm.counter.microcontroller")
def test_counter16_large_value(mock_microcontroller: MagicMock):
    """Tests Counter16 with large values.

    Args:
        mock_microcontroller: Mocked microcontroller module.
    """
    datastore = ByteArray(size=512)
    mock_microcontroller.nvm = datastore

    count = counter.Counter16(0)
    count.set(65535)  # Max 16-bit value
    assert count.get() == 65535


@patch("pysquared.nvm.counter.microcontroller")
def test_counter16_multiple_increments(mock_microcontroller: MagicMock):
    """Tests Counter16 multiple increments.

    Args:
        mock_microcontroller: Mocked microcontroller module.
    """
    datastore = ByteArray(size=512)
    mock_microcontroller.nvm = datastore

    count = counter.Counter16(0)
    count.set(0)
    for i in range(100):
        count.increment()
    assert count.get() == 100


@patch("pysquared.nvm.counter.microcontroller")
def test_counter16_get_name(mock_microcontroller: MagicMock):
    """Tests Counter16 get_name method.

    Args:
        mock_microcontroller: Mocked microcontroller module.
    """
    datastore = ByteArray(size=512)
    mock_microcontroller.nvm = datastore

    count = counter.Counter16(5)
    assert count.get_name() == "Counter16_index_5"
