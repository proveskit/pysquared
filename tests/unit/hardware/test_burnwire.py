"""Unit tests for the BurnwireManager class.

This module contains unit tests for the `BurnwireManager` class, which controls
the activation of burnwires. The tests cover initialization, successful burn
operations, error handling, and cleanup procedures.
"""

from unittest.mock import ANY, MagicMock, patch

import pytest
from digitalio import DigitalInOut

from pysquared.hardware.burnwire.manager.burnwire import BurnwireManager
from pysquared.logger import Logger


@pytest.fixture
def mock_logger():
    """Mocks the Logger class."""
    return MagicMock(spec=Logger)


@pytest.fixture
def mock_enable_burn():
    """Mocks the DigitalInOut pin for enabling the burnwire."""
    return MagicMock(spec=DigitalInOut)


@pytest.fixture
def mock_fire_burn():
    """Mocks the DigitalInOut pin for firing the burnwire."""
    return MagicMock(spec=DigitalInOut)


@pytest.fixture
def burnwire_manager(mock_logger, mock_enable_burn, mock_fire_burn):
    """Provides a BurnwireManager instance for testing."""
    return BurnwireManager(
        logger=mock_logger,
        enable_burn=mock_enable_burn,
        fire_burn=mock_fire_burn,
        enable_logic=True,
    )


def test_burnwire_initialization_default_logic(
    mock_logger, mock_enable_burn, mock_fire_burn
):
    """Tests burnwire initialization with default enable_logic=True.

    Args:
        mock_logger: Mocked Logger instance.
        mock_enable_burn: Mocked enable_burn pin.
        mock_fire_burn: Mocked fire_burn pin.
    """
    manager = BurnwireManager(mock_logger, mock_enable_burn, mock_fire_burn)
    assert manager._enable_logic is True
    assert manager.number_of_attempts == 0


def test_burnwire_initialization_inverted_logic(
    mock_logger, mock_enable_burn, mock_fire_burn
):
    """Tests burnwire initialization with enable_logic=False.

    Args:
        mock_logger: Mocked Logger instance.
        mock_enable_burn: Mocked enable_burn pin.
        mock_fire_burn: Mocked fire_burn pin.
    """
    manager = BurnwireManager(
        mock_logger, mock_enable_burn, mock_fire_burn, enable_logic=False
    )
    assert manager._enable_logic is False
    assert manager.number_of_attempts == 0


def test_successful_burn(burnwire_manager):
    """Tests a successful burnwire activation.

    Args:
        burnwire_manager: BurnwireManager instance for testing.
    """
    with patch("time.sleep") as mock_sleep:
        result = burnwire_manager.burn(timeout_duration=1.0)

        mock_sleep.assert_any_call(0.1)  # Verify stabilization delay
        mock_sleep.assert_any_call(1.0)  # Verify burn duration

        # Verify final safe state
        assert burnwire_manager._fire_burn.value == (not burnwire_manager._enable_logic)
        assert burnwire_manager._enable_burn.value == (
            not burnwire_manager._enable_logic
        )

        assert result is True
        assert burnwire_manager.number_of_attempts == 1


def test_burn_error_handling(burnwire_manager):
    """Tests error handling during burnwire activation.

    Args:
        burnwire_manager: BurnwireManager instance for testing.
    """
    # Mock the enable_burn pin to raise an exception when setting value
    type(burnwire_manager._enable_burn).value = property(
        fset=MagicMock(side_effect=RuntimeError("Hardware failure"))
    )

    result = burnwire_manager.burn()

    assert result is False

    # Verify critical log call about burn failure
    assert burnwire_manager._log.critical.call_count == 2
    calls = [call[0][0] for call in burnwire_manager._log.critical.call_args_list]
    assert any("Failed!" in msg for msg in calls)


def test_cleanup_on_error(burnwire_manager):
    """Tests that cleanup occurs even when an error happens during burn.

    Args:
        burnwire_manager: BurnwireManager instance for testing.
    """
    with patch("time.sleep") as mock_sleep:
        mock_sleep.side_effect = RuntimeError("Unexpected error")

        result = burnwire_manager.burn()

        assert result is False
        # Verify pins are set to safe state even after error
        assert burnwire_manager._fire_burn.value == (not burnwire_manager._enable_logic)
        assert burnwire_manager._enable_burn.value == (
            not burnwire_manager._enable_logic
        )
        burnwire_manager._log.debug.assert_any_call("Burnwire Safed")


def test_attempt_burn_exception_handling(burnwire_manager):
    """Tests that _attempt_burn properly handles and propagates exceptions.

    Args:
        burnwire_manager: BurnwireManager instance for testing.
    """
    # Mock the enable_burn pin to raise an exception when setting value
    type(burnwire_manager._enable_burn).value = property(
        fset=MagicMock(side_effect=RuntimeError("Hardware failure"))
    )

    with pytest.raises(RuntimeError) as exc_info:
        burnwire_manager._attempt_burn()

    assert "Failed to set fire_burn pin" in str(exc_info.value)


def test_burn_keyboard_interrupt(burnwire_manager):
    """Tests that a KeyboardInterrupt during burn is handled and logged, including in _attempt_burn.

    Args:
        burnwire_manager: BurnwireManager instance for testing.
    """
    # Patch _attempt_burn to raise KeyboardInterrupt
    with patch.object(burnwire_manager, "_attempt_burn", side_effect=KeyboardInterrupt):
        result = burnwire_manager.burn(timeout_duration=1.0)
        assert result is False
        # Check that the log contains the interruption message from burn()
        found = any(
            "Burn Attempt Interupted after" in str(call[0][0])
            for call in burnwire_manager._log.debug.call_args_list
        )
        assert found

    # Patch _enable to raise KeyboardInterrupt as if from inside _attempt_burn
    with patch.object(burnwire_manager, "_enable", side_effect=KeyboardInterrupt):
        with patch.object(burnwire_manager._log, "warning") as mock_warning:
            with pytest.raises(KeyboardInterrupt):
                burnwire_manager._attempt_burn()
            # Should log the warning from _attempt_burn
            mock_warning.assert_called_once()
            assert "Interrupted" in mock_warning.call_args[0][0]


def test_enable_fire_burn_pin_error(burnwire_manager):
    """Tests that a RuntimeError is raised if setting fire_burn pin fails in _enable.

    Args:
        burnwire_manager: BurnwireManager instance for testing.
    """
    # Allow enable_burn to succeed
    burnwire_manager._enable_burn.value = burnwire_manager._enable_logic
    # Make fire_burn raise an exception when set
    type(burnwire_manager._fire_burn).value = property(
        fset=MagicMock(side_effect=Exception("fire_burn failure"))
    )
    with pytest.raises(RuntimeError) as exc_info:
        burnwire_manager._enable()
    assert str(exc_info.value) == "Failed to set fire_burn pin"


def test_disable_cleanup_critical_log(burnwire_manager):
    """Tests that a critical log is made if _disable fails during cleanup and no prior error occurred.

    Args:
        burnwire_manager: BurnwireManager instance for testing.
    """
    # Patch _enable to succeed
    with patch.object(burnwire_manager, "_enable", return_value=None):
        # Patch time.sleep to avoid delay
        with patch("time.sleep"):
            # Patch _disable to raise an Exception
            with patch.object(
                burnwire_manager, "_disable", side_effect=Exception("disable failed")
            ):
                # Patch _log.critical to track calls
                with patch.object(burnwire_manager._log, "critical") as mock_critical:
                    # Patch _fire_burn and _enable_burn to allow value assignment
                    burnwire_manager._fire_burn.value = False
                    burnwire_manager._enable_burn.value = False
                    # The error variable should be None, so critical should be called
                    burnwire_manager._attempt_burn()
                    mock_critical.assert_called_with(
                        "Failed to safe burnwire pins!", ANY
                    )
