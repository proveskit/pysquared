from unittest.mock import MagicMock, patch

import pytest
from digitalio import DigitalInOut

from pysquared.hardware.burnwire.manager.burnwire import BurnwireManager
from pysquared.logger import Logger


@pytest.fixture
def mock_logger():
    return MagicMock(spec=Logger)


@pytest.fixture
def mock_enable_burn():
    return MagicMock(spec=DigitalInOut)


@pytest.fixture
def mock_fire_burn():
    return MagicMock(spec=DigitalInOut)


@pytest.fixture
def burnwire_manager(mock_logger, mock_enable_burn, mock_fire_burn):
    return BurnwireManager(
        logger=mock_logger,
        enable_burn=mock_enable_burn,
        fire_burn=mock_fire_burn,
        enable_logic=True,
    )


def test_burnwire_initialization_default_logic(
    mock_logger, mock_enable_burn, mock_fire_burn
):
    """Test burnwire initialization with default enable_logic=True."""
    manager = BurnwireManager(mock_logger, mock_enable_burn, mock_fire_burn)
    assert manager._enable_logic is True
    assert manager.number_of_attempts == 0


def test_burnwire_initialization_inverted_logic(
    mock_logger, mock_enable_burn, mock_fire_burn
):
    """Test burnwire initialization with enable_logic=False."""
    manager = BurnwireManager(
        mock_logger, mock_enable_burn, mock_fire_burn, enable_logic=False
    )
    assert manager._enable_logic is False
    assert manager.number_of_attempts == 0


def test_successful_burn(burnwire_manager):
    """Test a successful burnwire activation."""
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
    """Test error handling during burnwire activation."""
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
    """Test that cleanup occurs even when an error happens during burn."""
    with patch("time.sleep") as mock_sleep:
        mock_sleep.side_effect = RuntimeError("Unexpected error")

        result = burnwire_manager.burn()

        assert result is False
        # Verify pins are set to safe state even after error
        assert burnwire_manager._fire_burn.value == (not burnwire_manager._enable_logic)
        assert burnwire_manager._enable_burn.value == (
            not burnwire_manager._enable_logic
        )
        burnwire_manager._log.info.assert_any_call("Burnwire Safed")


def test_attempt_burn_exception_handling(burnwire_manager):
    """Test that _attempt_burn properly handles and propagates exceptions."""
    # Mock the enable_burn pin to raise an exception when setting value
    type(burnwire_manager._enable_burn).value = property(
        fset=MagicMock(side_effect=RuntimeError("Hardware failure"))
    )

    with pytest.raises(RuntimeError) as exc_info:
        burnwire_manager._attempt_burn()

    assert "Failed to set fire_burn pin" in str(exc_info.value)
