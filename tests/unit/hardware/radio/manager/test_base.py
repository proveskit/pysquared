import pytest

from pysquared.hardware.radio.manager.base import BaseRadioManager
from pysquared.hardware.radio.modulation import LoRa


def test_initialize_radio_not_implemented():
    """Test that the _initialize_radio method raises NotImplementedError."""
    # Create a mock instance of the BaseRadioManager
    mock_manager = BaseRadioManager.__new__(BaseRadioManager)

    # Check that calling _initialize_radio raises NotImplementedError
    with pytest.raises(NotImplementedError):
        mock_manager._initialize_radio(LoRa)


def test_receive_not_implemented():
    """Test that the _initialize_radio method raises NotImplementedError."""
    # Create a mock instance of the BaseRadioManager
    mock_manager = BaseRadioManager.__new__(BaseRadioManager)

    # Check that calling _initialize_radio raises NotImplementedError
    with pytest.raises(NotImplementedError):
        mock_manager.receive()


def test_send_internal_not_implemented():
    """Test that the _initialize_radio method raises NotImplementedError."""
    # Create a mock instance of the BaseRadioManager
    mock_manager = BaseRadioManager.__new__(BaseRadioManager)

    # Check that calling _initialize_radio raises NotImplementedError
    with pytest.raises(NotImplementedError):
        mock_manager._send_internal(b"blah")


def test_get_modulation_not_implemented():
    """Test that the _initialize_radio method raises NotImplementedError."""
    # Create a mock instance of the BaseRadioManager
    mock_manager = BaseRadioManager.__new__(BaseRadioManager)

    # Check that calling _initialize_radio raises NotImplementedError
    with pytest.raises(NotImplementedError):
        mock_manager.get_modulation()
