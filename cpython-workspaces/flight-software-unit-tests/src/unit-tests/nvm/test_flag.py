"""Unit tests for the Flag class in the NVM module.

This module contains unit tests for the `Flag` class, which provides a persistent
boolean flag stored in non-volatile memory (NVM). The tests cover flag
initialization, getting and setting flag values, and handling of NVM availability.
"""

from unittest.mock import MagicMock, patch

import pytest
from mocks.circuitpython.byte_array import ByteArray
from pysquared.nvm.flag import Flag


@pytest.fixture
def setup_datastore():
    """Sets up a mock datastore for NVM components."""
    return ByteArray(size=17)


@patch("pysquared.nvm.flag.microcontroller")
def test_init(mock_microcontroller: MagicMock, setup_datastore: ByteArray):
    """Tests Flag initialization.

    Args:
        mock_microcontroller: Mocked microcontroller module.
        setup_datastore: Fixture providing the mock datastore.
    """
    mock_microcontroller.nvm = (
        setup_datastore  # Mock the nvm module to use the ByteArray
    )
    flag = Flag(16, 0)  # Example flag for softboot
    assert flag._index == 16  # Check if _index (index of byte array) is set to 16
    assert flag._bit == 0  # Check if _bit (bit position) is set to first index of byte
    assert flag._bit_mask == 0b00000001  # Check if _bit_mask is set correctly


@patch("pysquared.nvm.flag.microcontroller")
def test_get(mock_microcontroller: MagicMock, setup_datastore: ByteArray):
    """Tests getting the flag value.

    Args:
        mock_microcontroller: Mocked microcontroller module.
        setup_datastore: Fixture providing the mock datastore.
    """
    mock_microcontroller.nvm = (
        setup_datastore  # Mock the nvm module to use the ByteArray
    )
    flag = Flag(16, 1)  # Example flag for solar
    assert setup_datastore[16] == 0b00000000
    assert not flag.get()  # Bit should be 0 by default

    setup_datastore[16] = 0b00000010  # Manually set bit to test
    assert flag.get()  # Should return true since bit position 1 = 1


@patch("pysquared.nvm.flag.microcontroller")
def test_toggle(mock_microcontroller: MagicMock, setup_datastore: ByteArray):
    """Tests toggling the flag value.

    Args:
        mock_microcontroller: Mocked microcontroller module.
        setup_datastore: Fixture providing the mock datastore.
    """
    mock_microcontroller.nvm = (
        setup_datastore  # Mock the nvm module to use the ByteArray
    )
    flag = Flag(16, 2)  # Example flag for burnarm
    assert setup_datastore[16] == 0b00000000
    flag.toggle(False)  # Set flag to off (bit to 0)
    assert setup_datastore[16] == 0b00000000
    assert not flag.get()  # Bit should remain 0 due to 0 by default

    flag.toggle(True)  # Set flag to on (bit to 1)
    assert setup_datastore[16] == 0b00000100  # Check if bit position 2 = 1
    assert flag.get()  # Bit should be flipped to 1

    flag.toggle(True)  # Set flag to on (bit to 1)
    assert setup_datastore[16] == 0b00000100  # Check if bit position 2 = 1
    assert flag.get()  # Bit should remain 1 due to already being set to on

    flag.toggle(False)  # Set flag back to off (bit to 0)
    assert setup_datastore[16] == 0b00000000  # Check if bit position 2 = 0
    assert not flag.get()  # Bit should be 0


@patch("pysquared.nvm.flag.microcontroller")
def test_edge_cases(mock_microcontroller: MagicMock, setup_datastore: ByteArray):
    """Tests edge cases for flag manipulation.

    Args:
        mock_microcontroller: Mocked microcontroller module.
        setup_datastore: Fixture providing the mock datastore.
    """
    mock_microcontroller.nvm = (
        setup_datastore  # Mock the nvm module to use the ByteArray
    )
    first_bit = Flag(0, 0)
    first_bit.toggle(True)
    assert setup_datastore[0] == 0b00000001
    assert first_bit.get()

    last_bit = Flag(0, 7)
    last_bit.toggle(True)
    assert setup_datastore[0] == 0b10000001
    assert last_bit.get()


@patch("pysquared.nvm.flag.microcontroller")
def test_counter_raises_error_when_nvm_is_none(mock_microcontroller: MagicMock):
    """Tests that the Flag raises a ValueError when NVM is not available.

    Args:
        mock_microcontroller: Mocked microcontroller module.
    """
    mock_microcontroller.nvm = None

    with pytest.raises(ValueError, match="nvm is not available"):
        Flag(0, 7)


@patch("pysquared.nvm.flag.microcontroller")
def test_get_name(mock_microcontroller: MagicMock):
    """Tests the get_name method of the Flag class.

    Args:
        mock_microcontroller: Mocked microcontroller module.
    """
    mock_microcontroller.nvm = (
        setup_datastore  # Mock the nvm module to use the ByteArray
    )

    flag = Flag(0, 7)
    assert flag.get_name() == "Flag_index_0_bit_7"
