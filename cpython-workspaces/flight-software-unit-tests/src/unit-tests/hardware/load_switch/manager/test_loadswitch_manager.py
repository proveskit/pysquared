"""Unit tests for the LoadSwitchManager class.

This module contains unit tests for the `LoadSwitchManager` class, which controls
load switch operations for power management. The tests cover initialization,
successful operations, error handling, and state management.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

# Mock digitalio module before importing LoadSwitchManager
digitalio = MagicMock()
digitalio.DigitalInOut = MagicMock
sys.modules["digitalio"] = digitalio

from pysquared.hardware.load_switch.manager.loadswitch_manager import (  # noqa: E402
    LoadSwitchManager,
)


def test_loadswitch_initialization_enable_high():
    """Tests LoadSwitchManager initialization with enable_high=True."""
    mock_pin = MagicMock()
    manager = LoadSwitchManager(load_switch_pin=mock_pin, enable_high=True)

    # Test behavior through public interface - enable should set pin to True
    manager.enable_load()
    # Check that the pin value was set to True (called via property setter)
    assert mock_pin.value == True  # noqa: E712


def test_loadswitch_initialization_enable_low():
    """Tests LoadSwitchManager initialization with enable_high=False."""
    mock_pin = MagicMock()
    manager = LoadSwitchManager(load_switch_pin=mock_pin, enable_high=False)

    # Test behavior through public interface - enable should set pin to False
    manager.enable_load()
    # Check that the pin value was set to False (called via property setter)
    assert mock_pin.value == False  # noqa: E712


def test_loadswitch_initialization_default_enable_high():
    """Tests LoadSwitchManager initialization with default enable_high=True."""
    mock_pin = MagicMock()
    manager = LoadSwitchManager(load_switch_pin=mock_pin)

    # Test behavior through public interface - enable should set pin to True (default)
    manager.enable_load()
    # Check that the pin value was set to True (called via property setter)
    assert mock_pin.value == True  # noqa: E712


def test_enable_load_success_enable_high():
    """Tests successful load enable operation with enable_high=True."""
    mock_pin = MagicMock()
    manager = LoadSwitchManager(load_switch_pin=mock_pin, enable_high=True)

    manager.enable_load()

    # Verify the pin was set to True (enable_pin_value)
    assert mock_pin.value == True  # noqa: E712


def test_enable_load_success_enable_low():
    """Tests successful load enable operation with enable_high=False."""
    mock_pin = MagicMock()
    manager = LoadSwitchManager(load_switch_pin=mock_pin, enable_high=False)

    manager.enable_load()

    # Verify the pin was set to False (enable_pin_value)
    assert mock_pin.value == False  # noqa: E712


def test_enable_load_hardware_failure():
    """Tests enable_load error handling when hardware fails."""
    mock_pin = MagicMock()
    manager = LoadSwitchManager(load_switch_pin=mock_pin, enable_high=True)

    # Mock the pin to raise an exception when setting value
    type(mock_pin).value = property(
        fset=MagicMock(side_effect=RuntimeError("Hardware failure"))
    )

    with pytest.raises(
        RuntimeError, match="Failed to enable load switch: Hardware failure"
    ):
        manager.enable_load()


def test_disable_load_success_enable_high():
    """Tests successful load disable operation with enable_high=True."""
    mock_pin = MagicMock()
    manager = LoadSwitchManager(load_switch_pin=mock_pin, enable_high=True)

    manager.disable_load()

    # Verify the pin was set to False (disable_pin_value)
    assert mock_pin.value == False  # noqa: E712


def test_disable_load_success_enable_low():
    """Tests successful load disable operation with enable_high=False."""
    mock_pin = MagicMock()
    manager = LoadSwitchManager(load_switch_pin=mock_pin, enable_high=False)

    manager.disable_load()

    # Verify the pin was set to True (disable_pin_value)
    assert mock_pin.value == True  # noqa: E712


def test_disable_load_hardware_failure():
    """Tests disable_load error handling when hardware fails."""
    mock_pin = MagicMock()
    manager = LoadSwitchManager(load_switch_pin=mock_pin, enable_high=True)

    # Mock the pin to raise an exception when setting value
    type(mock_pin).value = property(
        fset=MagicMock(side_effect=RuntimeError("Hardware failure"))
    )

    with pytest.raises(
        RuntimeError, match="Failed to disable load switch: Hardware failure"
    ):
        manager.disable_load()


def test_is_enabled_true_enable_high():
    """Tests is_enabled property when load is enabled with enable_high=True."""
    mock_pin = MagicMock()
    manager = LoadSwitchManager(load_switch_pin=mock_pin, enable_high=True)

    # Mock pin value to return True (enabled state for enable_high=True)
    mock_pin.value = True

    assert manager.is_enabled is True


def test_is_enabled_false_enable_high():
    """Tests is_enabled property when load is disabled with enable_high=True."""
    mock_pin = MagicMock()
    manager = LoadSwitchManager(load_switch_pin=mock_pin, enable_high=True)

    # Mock pin value to return False (disabled state for enable_high=True)
    mock_pin.value = False

    assert manager.is_enabled is False


def test_is_enabled_true_enable_low():
    """Tests is_enabled property when load is enabled with enable_high=False."""
    mock_pin = MagicMock()
    manager = LoadSwitchManager(load_switch_pin=mock_pin, enable_high=False)

    # Mock pin value to return False (enabled state for enable_high=False)
    mock_pin.value = False

    assert manager.is_enabled is True


def test_is_enabled_false_enable_low():
    """Tests is_enabled property when load is disabled with enable_high=False."""
    mock_pin = MagicMock()
    manager = LoadSwitchManager(load_switch_pin=mock_pin, enable_high=False)

    # Mock pin value to return True (disabled state for enable_high=False)
    mock_pin.value = True

    assert manager.is_enabled is False


def test_is_enabled_hardware_failure():
    """Tests is_enabled error handling when hardware fails."""
    mock_pin = MagicMock()
    manager = LoadSwitchManager(load_switch_pin=mock_pin, enable_high=True)

    # Mock the pin to raise an exception when reading value
    type(mock_pin).value = property(
        fget=MagicMock(side_effect=RuntimeError("Hardware failure"))
    )

    with pytest.raises(
        RuntimeError, match="Failed to read load switch state: Hardware failure"
    ):
        _ = manager.is_enabled


@patch("pysquared.hardware.load_switch.manager.loadswitch_manager.time.sleep")
def test_reset_load_was_enabled(mock_sleep):
    """Tests reset_load when load was previously enabled."""
    mock_pin = MagicMock()
    manager = LoadSwitchManager(load_switch_pin=mock_pin, enable_high=True)

    # Set up initial state as enabled
    mock_pin.value = True

    with patch.object(manager, "disable_load") as mock_disable:
        with patch.object(manager, "enable_load") as mock_enable:
            manager.reset_load()

            # Verify disable was called
            mock_disable.assert_called_once()
            # Verify sleep for 0.1 seconds
            mock_sleep.assert_called_once_with(0.1)
            # Verify enable was called to restore state
            mock_enable.assert_called_once()


@patch("pysquared.hardware.load_switch.manager.loadswitch_manager.time.sleep")
def test_reset_load_was_disabled(mock_sleep):
    """Tests reset_load when load was previously disabled."""
    mock_pin = MagicMock()
    manager = LoadSwitchManager(load_switch_pin=mock_pin, enable_high=True)

    # Set up initial state as disabled
    mock_pin.value = False

    with patch.object(manager, "disable_load") as mock_disable:
        with patch.object(manager, "enable_load") as mock_enable:
            manager.reset_load()

            # Verify disable was called
            mock_disable.assert_called_once()
            # Verify sleep for 0.1 seconds
            mock_sleep.assert_called_once_with(0.1)
            # Verify enable was NOT called since it was previously disabled
            mock_enable.assert_not_called()


def test_reset_load_disable_failure():
    """Tests reset_load error handling when disable fails."""
    mock_pin = MagicMock()
    manager = LoadSwitchManager(load_switch_pin=mock_pin, enable_high=True)

    # Set up initial state as enabled
    mock_pin.value = True

    with patch.object(
        manager, "disable_load", side_effect=RuntimeError("Disable failed")
    ):
        with pytest.raises(
            RuntimeError, match="Failed to reset load switch: Disable failed"
        ):
            manager.reset_load()


def test_reset_load_enable_failure():
    """Tests reset_load error handling when re-enable fails."""
    mock_pin = MagicMock()
    manager = LoadSwitchManager(load_switch_pin=mock_pin, enable_high=True)

    # Set up initial state as enabled
    mock_pin.value = True

    with patch.object(manager, "disable_load"):
        with patch.object(
            manager, "enable_load", side_effect=RuntimeError("Enable failed")
        ):
            with pytest.raises(
                RuntimeError, match="Failed to reset load switch: Enable failed"
            ):
                manager.reset_load()


def test_reset_load_is_enabled_check_failure():
    """Tests reset_load error handling when is_enabled check fails."""
    mock_pin = MagicMock()
    manager = LoadSwitchManager(load_switch_pin=mock_pin, enable_high=True)

    # Mock the pin to raise an exception when reading value (which is used by is_enabled)
    type(mock_pin).value = property(
        fget=MagicMock(side_effect=RuntimeError("State check failed"))
    )

    with pytest.raises(
        RuntimeError,
        match="Failed to reset load switch: Failed to read load switch state: State check failed",
    ):
        manager.reset_load()
