from unittest.mock import MagicMock, patch

import pytest
from digitalio import DigitalInOut, Direction
from microcontroller import Pin

from pysquared.logger import Logger
from pysquared.watchdog import Watchdog


@pytest.fixture
def mock_pin() -> MagicMock:
    return MagicMock(spec=Pin)


@pytest.fixture
def mock_logger() -> MagicMock:
    return MagicMock(spec=Logger)


@patch("pysquared.watchdog.initialize_pin")
def test_watchdog_init(
    mock_initialize_pin: MagicMock, mock_logger: MagicMock, mock_pin: MagicMock
) -> None:
    """Test Watchdog initialization."""
    mock_digital_in_out = MagicMock(spec=DigitalInOut)
    mock_initialize_pin.return_value = mock_digital_in_out

    watchdog = Watchdog(mock_logger, mock_pin)

    mock_initialize_pin.assert_called_once_with(
        mock_logger,
        mock_pin,
        Direction.OUTPUT,
        False,
    )
    assert watchdog._digital_in_out is mock_digital_in_out


@patch("pysquared.watchdog.time.sleep")
@patch("pysquared.watchdog.initialize_pin")
def test_watchdog_pet(
    mock_initialize_pin: MagicMock,
    mock_sleep: MagicMock,
    mock_logger: MagicMock,
    mock_pin: MagicMock,
) -> None:
    """Test Watchdog pet method using side_effect on sleep."""
    mock_digital_in_out = MagicMock(spec=DigitalInOut)
    mock_initialize_pin.return_value = mock_digital_in_out

    # Inject a side effect to the sleep function
    # to capture the state of the mock pin when sleep is called
    value_during_sleep = None

    def check_value_and_sleep(_: float) -> None:
        nonlocal value_during_sleep
        value_during_sleep = mock_digital_in_out.value

    mock_sleep.side_effect = check_value_and_sleep

    watchdog = Watchdog(mock_logger, mock_pin)
    watchdog.pet()

    mock_sleep.assert_called_once_with(0.01)
    assert value_during_sleep, "Watchdog pin value should be True when sleep is called"
    assert (
        mock_digital_in_out.value is False
    ), "Watchdog pin value should be False after pet() finishes"
