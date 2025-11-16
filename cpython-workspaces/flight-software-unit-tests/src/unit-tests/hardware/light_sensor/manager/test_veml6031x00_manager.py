"""Tests for the VEML6031x00Manager class."""

from unittest.mock import MagicMock, patch

import pytest
from pysquared.hardware.exception import HardwareInitializationError
from pysquared.hardware.light_sensor.manager.veml6031x00 import VEML6031x00Manager
from pysquared.logger import Logger
from pysquared.sensor_reading.error import (
    SensorReadingTimeoutError,
    SensorReadingUnknownError,
    SensorReadingValueError,
)
from pysquared.sensor_reading.light import Light
from pysquared.sensor_reading.lux import Lux


@pytest.fixture
def mock_i2c():
    """Mocked I2C bus object."""
    return MagicMock()


@pytest.fixture
def mock_logger():
    """Mocked Logger instance."""
    return MagicMock(Logger)


def make_manager_with_reads(
    mock_logger: MagicMock,
    mock_i2c: MagicMock,
    id_l: int = 0x01,
    id_h: int = 0x00,
):
    """Construct manager while patching ID reads and avoiding real I2C IO."""

    with patch(
        "pysquared.hardware.light_sensor.manager.veml6031x00.VEML6031x00Manager._read8",
        side_effect=[id_l, id_h],
    ) as _:
        with patch(
            "pysquared.hardware.light_sensor.manager.veml6031x00.VEML6031x00Manager._write_thresh_low"
        ) as __:
            with patch(
                "pysquared.hardware.light_sensor.manager.veml6031x00.VEML6031x00Manager._write_thresh_high"
            ) as ___:
                with patch(
                    "pysquared.hardware.light_sensor.manager.veml6031x00.VEML6031x00Manager._write_conf"
                ) as ____:
                    return VEML6031x00Manager(mock_logger, mock_i2c)


def test_init_success(mock_i2c, mock_logger):
    """Manager initializes successfully when device ID matches expected value."""
    mgr = make_manager_with_reads(mock_logger, mock_i2c)
    assert isinstance(mgr, VEML6031x00Manager)
    mock_logger.debug.assert_any_call("Initializing VEML6031x00 light sensor")


def test_init_wrong_id_raises(mock_i2c, mock_logger):
    """Initialization raises when the device ID is unexpected."""
    with pytest.raises(HardwareInitializationError):
        _ = make_manager_with_reads(mock_logger, mock_i2c, id_l=0xFF)


def test_get_lux_success(mock_i2c, mock_logger):
    """Single measurement succeeds and returns correct lux value."""
    # Prepare manager
    mgr = make_manager_with_reads(mock_logger, mock_i2c)

    # Data ready sequence: first read clears, then not ready, then ready
    dr_sequence = [0x00, 0x00, 0x08]

    def _mock_read8(reg: int) -> int:
        """Mock read8 returning the next data-ready value."""
        return dr_sequence.pop(0)

    # Ambient light counts = 100, IR counts arbitrary
    def _mock_read16(reg: int) -> int:
        """Mock read16 returning deterministic ambient/IR counts."""
        if reg == 0x10:
            return 100
        if reg == 0x12:
            return 42
        return 0

    with patch.object(mgr, "_read8", side_effect=_mock_read8):
        with patch.object(mgr, "_read16", side_effect=_mock_read16):
            with patch("time.sleep"):
                lux = mgr.get_lux()

    # Default configuration uses div4=4/4, gain=1x, it=100ms => 0.0272 lux/count
    assert isinstance(lux, Lux)
    assert lux.value == pytest.approx(100 * 0.0272, rel=1e-6)


def test_get_light_success(mock_i2c, mock_logger):
    """Returns Light reading containing sensor counts."""
    mgr = make_manager_with_reads(mock_logger, mock_i2c)

    dr_sequence = [0x00, 0x08]

    with patch.object(mgr, "_read8", side_effect=dr_sequence):
        with patch.object(mgr, "_read16", side_effect=[50, 5]):
            with patch("time.sleep"):
                light = mgr.get_light()

    assert isinstance(light, Light)
    assert light.value == pytest.approx(50.0, rel=1e-6)


def test_overflow_raises_value_error(mock_i2c, mock_logger):
    """Overflow sentinel value triggers SensorReadingValueError."""
    mgr = make_manager_with_reads(mock_logger, mock_i2c)

    dr_sequence = [0x00, 0x08]

    with patch.object(mgr, "_read8", side_effect=dr_sequence):
        # Ambient light overflow 0xFFFF
        with patch.object(mgr, "_read16", side_effect=[0xFFFF, 0]):
            with patch("time.sleep"):
                with pytest.raises(SensorReadingValueError):
                    _ = mgr.get_lux()


def test_data_ready_timeout_raises(mock_i2c, mock_logger):
    """Polling without data-ready bit set triggers timeout error."""
    mgr = make_manager_with_reads(mock_logger, mock_i2c)

    # Never sets data ready bit
    def _mock_read8(_: int) -> int:
        """Mock read8 that never sets the data-ready bit."""
        return 0x00

    with patch.object(mgr, "_read8", side_effect=_mock_read8):
        with patch("time.sleep"):
            with patch("time.monotonic", side_effect=[0.0] + [0.6] * 10):
                with pytest.raises(SensorReadingTimeoutError):
                    _ = mgr.get_lux()


def test_unknown_error_wrapped(mock_i2c, mock_logger):
    """Unexpected exceptions during reads are wrapped as unknown errors."""
    mgr = make_manager_with_reads(mock_logger, mock_i2c)

    # Cause unexpected exception during reads
    with patch.object(mgr, "_read8", side_effect=RuntimeError("boom")):
        with pytest.raises(SensorReadingUnknownError):
            _ = mgr.get_light()
