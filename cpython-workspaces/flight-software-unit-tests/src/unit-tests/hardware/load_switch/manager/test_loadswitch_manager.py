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


@pytest.fixture
def mock_pin():
    """Provides a mock DigitalInOut pin for testing."""
    return MagicMock()


@pytest.fixture
def manager_enable_high(mock_pin):
    """Provides a LoadSwitchManager with enable_high=True."""
    return LoadSwitchManager(load_switch_pin=mock_pin, enable_high=True)


@pytest.fixture
def manager_enable_low(mock_pin):
    """Provides a LoadSwitchManager with enable_high=False."""
    return LoadSwitchManager(load_switch_pin=mock_pin, enable_high=False)


def test_loadswitch_initialization_enable_high(manager_enable_high, mock_pin):
    """Tests LoadSwitchManager initialization with enable_high=True."""
    # Test behavior through public interface - enable should set pin to True
    manager_enable_high.enable_load()
    assert mock_pin.value is True


def test_loadswitch_initialization_enable_low(manager_enable_low, mock_pin):
    """Tests LoadSwitchManager initialization with enable_high=False."""
    # Test behavior through public interface - enable should set pin to False
    manager_enable_low.enable_load()
    assert mock_pin.value is False


def test_loadswitch_initialization_default_enable_high(mock_pin):
    """Tests LoadSwitchManager initialization with default enable_high=True."""
    manager = LoadSwitchManager(load_switch_pin=mock_pin)
    # Test behavior through public interface - enable should set pin to True (default)
    manager.enable_load()
    assert mock_pin.value is True


@pytest.mark.parametrize(
    "manager_fixture,expected_value",
    [("manager_enable_high", True), ("manager_enable_low", False)],
)
def test_enable_load_success(manager_fixture, expected_value, request, mock_pin):
    """Tests successful load enable operation for both enable logic types."""
    manager = request.getfixturevalue(manager_fixture)
    manager.enable_load()
    assert mock_pin.value is expected_value


def test_enable_load_hardware_failure(manager_enable_high, mock_pin):
    """Tests enable_load error handling when hardware fails."""
    # Mock the pin to raise an exception when setting value
    type(mock_pin).value = property(
        fset=MagicMock(side_effect=RuntimeError("Hardware failure"))
    )

    with pytest.raises(
        RuntimeError, match="Failed to enable load switch: Hardware failure"
    ):
        manager_enable_high.enable_load()


@pytest.mark.parametrize(
    "manager_fixture,expected_value",
    [("manager_enable_high", False), ("manager_enable_low", True)],
)
def test_disable_load_success(manager_fixture, expected_value, request, mock_pin):
    """Tests successful load disable operation for both enable logic types."""
    manager = request.getfixturevalue(manager_fixture)
    manager.disable_load()
    assert mock_pin.value is expected_value


def test_disable_load_hardware_failure(manager_enable_high, mock_pin):
    """Tests disable_load error handling when hardware fails."""
    # Mock the pin to raise an exception when setting value
    type(mock_pin).value = property(
        fset=MagicMock(side_effect=RuntimeError("Hardware failure"))
    )

    with pytest.raises(
        RuntimeError, match="Failed to disable load switch: Hardware failure"
    ):
        manager_enable_high.disable_load()


@pytest.mark.parametrize(
    "manager_fixture,pin_value,expected_enabled",
    [
        ("manager_enable_high", True, True),
        ("manager_enable_high", False, False),
        ("manager_enable_low", False, True),
        ("manager_enable_low", True, False),
    ],
)
def test_is_enabled(manager_fixture, pin_value, expected_enabled, request, mock_pin):
    """Tests is_enabled property for all combinations of enable logic and pin states."""
    manager = request.getfixturevalue(manager_fixture)
    mock_pin.value = pin_value
    assert manager.is_enabled is expected_enabled


def test_is_enabled_hardware_failure(manager_enable_high, mock_pin):
    """Tests is_enabled error handling when hardware fails."""
    # Mock the pin to raise an exception when reading value
    type(mock_pin).value = property(
        fget=MagicMock(side_effect=RuntimeError("Hardware failure"))
    )

    with pytest.raises(
        RuntimeError, match="Failed to read load switch state: Hardware failure"
    ):
        _ = manager_enable_high.is_enabled


@pytest.mark.parametrize(
    "was_enabled,enable_should_be_called",
    [(True, True), (False, False)],
)
@patch("pysquared.hardware.load_switch.manager.loadswitch_manager.time.sleep")
def test_reset_load_state_preservation(
    mock_sleep, was_enabled, enable_should_be_called, manager_enable_high, mock_pin
):
    """Tests reset_load preserves previous state correctly."""
    # Set up initial state
    mock_pin.value = was_enabled

    with patch.object(manager_enable_high, "disable_load") as mock_disable:
        with patch.object(manager_enable_high, "enable_load") as mock_enable:
            manager_enable_high.reset_load()

            # Verify disable was called
            mock_disable.assert_called_once()
            # Verify sleep for 0.1 seconds
            mock_sleep.assert_called_once_with(0.1)
            # Verify enable behavior based on previous state
            if enable_should_be_called:
                mock_enable.assert_called_once()
            else:
                mock_enable.assert_not_called()


@pytest.mark.parametrize(
    "failure_method,error_message,expected_match",
    [
        (
            "disable_load",
            "Disable failed",
            "Failed to reset load switch: Disable failed",
        ),
        ("enable_load", "Enable failed", "Failed to reset load switch: Enable failed"),
    ],
)
def test_reset_load_operation_failures(
    failure_method, error_message, expected_match, manager_enable_high, mock_pin
):
    """Tests reset_load error handling for disable and enable failures."""
    # Set up initial state as enabled
    mock_pin.value = True

    patches = {}
    if failure_method == "disable_load":
        patches["disable_load"] = patch.object(
            manager_enable_high, "disable_load", side_effect=RuntimeError(error_message)
        )
    else:
        patches["disable_load"] = patch.object(manager_enable_high, "disable_load")
        patches["enable_load"] = patch.object(
            manager_enable_high, "enable_load", side_effect=RuntimeError(error_message)
        )

    with patches["disable_load"]:
        if "enable_load" in patches:
            with patches["enable_load"]:
                with pytest.raises(RuntimeError, match=expected_match):
                    manager_enable_high.reset_load()
        else:
            with pytest.raises(RuntimeError, match=expected_match):
                manager_enable_high.reset_load()


def test_reset_load_is_enabled_check_failure(manager_enable_high, mock_pin):
    """Tests reset_load error handling when is_enabled check fails."""
    # Mock the pin to raise an exception when reading value (which is used by is_enabled)
    type(mock_pin).value = property(
        fget=MagicMock(side_effect=RuntimeError("State check failed"))
    )

    with pytest.raises(
        RuntimeError,
        match="Failed to reset load switch: Failed to read load switch state: State check failed",
    ):
        manager_enable_high.reset_load()
