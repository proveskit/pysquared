from unittest.mock import MagicMock

import pytest

from mocks.circuitpython.byte_array import ByteArray

# from pysquared.hardware.load_switchs.factory import ShiftRegister74HC595Factory
from pysquared.hardware.load_switchs.manager import LoadSwitchManager
from pysquared.logger import Logger
from pysquared.nvm.counter import Counter


@pytest.fixture
def mock_logger():
    return Logger(Counter(0, ByteArray(size=8)))


@pytest.fixture
def mock_shift_register_factory():
    return MagicMock()


@pytest.fixture
def mock_enable_pins():
    return [MagicMock(value=True) for _ in range(8)]


@pytest.fixture
def load_switch_manager(mock_logger, mock_shift_register_factory, mock_enable_pins):
    mock_shift_register_factory.create.return_value = mock_enable_pins
    mock_latch = MagicMock()  # Mock the latch argument
    return LoadSwitchManager(mock_logger, mock_shift_register_factory, mock_latch)


def test_turn_on(load_switch_manager, mock_enable_pins):
    load_switch_manager.turn_on(2)
    assert mock_enable_pins[2].value is False


def test_turn_on_invalid_switch(load_switch_manager):
    with pytest.raises(ValueError, match="Load switch 5 not found."):
        load_switch_manager.turn_on(10)


def test_turn_off(load_switch_manager, mock_enable_pins):
    load_switch_manager.turn_off(1)
    assert mock_enable_pins[1].value is True


def test_turn_off_invalid_switch(load_switch_manager):
    with pytest.raises(ValueError, match="Load switch 5 not found."):
        load_switch_manager.turn_off(55)


def test_turn_on_all(load_switch_manager, mock_enable_pins, mock_logger):
    load_switch_manager.turn_on_all()
    for pin in mock_enable_pins:
        assert pin.value is False
    mock_logger.info.assert_called_once_with("All load switches turned on.")


def test_turn_off_all(load_switch_manager, mock_enable_pins, mock_logger):
    load_switch_manager.turn_off_all()
    for pin in mock_enable_pins:
        assert pin.value is True
    mock_logger.info.assert_called_once_with("All load switches turned off.")


def test_assign_names_to_pins(load_switch_manager, mock_enable_pins, mock_logger):
    pin_names = {"switch_a": 0, "switch_b": 1}
    load_switch_manager.assign_names_to_pins(pin_names)
    assert load_switch_manager._pin_name_map["switch_a"] == mock_enable_pins[0]
    assert load_switch_manager._pin_name_map["switch_b"] == mock_enable_pins[1]
    mock_logger.debug.assert_called_once_with(
        "Assigned names to load switch pins",
        pin_names=load_switch_manager._pin_name_map,
    )


def test_assign_names_to_pins_invalid_index(load_switch_manager):
    pin_names = {"switch_a": 15}
    with pytest.raises(ValueError, match="Invalid pin index 5 for name 'switch_a'."):
        load_switch_manager.assign_names_to_pins(pin_names)


def test_turn_on_by_name(load_switch_manager, mock_enable_pins):
    pin_names = {"switch_a": 0}
    load_switch_manager.assign_names_to_pins(pin_names)
    load_switch_manager.turn_on_by_name("switch_a")
    assert mock_enable_pins[0].value is False


def test_turn_on_by_name_invalid_name(load_switch_manager):
    with pytest.raises(ValueError, match="Load switch with name 'invalid' not found."):
        load_switch_manager.turn_on_by_name("invalid")


def test_turn_off_by_name(load_switch_manager, mock_enable_pins):
    pin_names = {"switch_a": 0}
    load_switch_manager.assign_names_to_pins(pin_names)
    load_switch_manager.turn_off_by_name("switch_a")
    assert mock_enable_pins[0].value is True


def test_turn_off_by_name_invalid_name(load_switch_manager):
    with pytest.raises(ValueError, match="Load switch with name 'invalid' not found."):
        load_switch_manager.turn_off_by_name("invalid")
