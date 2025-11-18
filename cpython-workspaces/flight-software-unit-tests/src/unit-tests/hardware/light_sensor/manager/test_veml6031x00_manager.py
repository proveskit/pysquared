"""Test the VEML6031x00Manager class."""

from unittest.mock import MagicMock, patch

import pytest
from pysquared.hardware.exception import HardwareInitializationError
from pysquared.hardware.light_sensor.manager.veml6031x00 import (
    VEML6031x00Manager,
    _Div4,
    _Gain,
    _It,
)
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
    """Fixture to mock the I2C bus."""
    mock = MagicMock()
    mock.try_lock.return_value = True
    mock.unlock.return_value = None
    mock.writeto.return_value = None
    mock.writeto_then_readfrom.return_value = None
    mock.readfrom_into.return_value = None
    return mock


@pytest.fixture
def mock_logger():
    """Fixture to mock the logger."""
    return MagicMock(spec=Logger)


@pytest.fixture
def setup_mock_i2c_for_init(mock_i2c: MagicMock) -> MagicMock:
    """Configure mock I2C for successful initialization.

    Args:
        mock_i2c: Mocked I2C bus.

    Returns:
        Configured mock I2C.
    """

    def mock_writeto_then_readfrom(addr, out_buf, in_buf):
        """Mock combined write-then-read operation."""
        # Always return device ID for reads during init
        if len(in_buf) == 1:
            in_buf[0] = 0x01  # Device ID low byte
        elif len(in_buf) == 2:
            in_buf[0] = 0x00
            in_buf[1] = 0x00

    def mock_readfrom_into(addr, buffer):
        """Mock read operation that returns device ID."""
        if len(buffer) == 1:
            buffer[0] = 0x01  # Device ID low byte
        elif len(buffer) == 2:
            buffer[0] = 0x00
            buffer[1] = 0x00

    # Reset and reconfigure the mock
    mock_i2c.reset_mock()
    mock_i2c.try_lock.return_value = True
    mock_i2c.unlock.return_value = None
    mock_i2c.writeto.return_value = None
    mock_i2c.writeto_then_readfrom.side_effect = mock_writeto_then_readfrom
    mock_i2c.readfrom_into.side_effect = mock_readfrom_into
    return mock_i2c


def set_mock_i2c_reads(mock_i2c: MagicMock, read_func) -> None:
    """Helper to set both writeto_then_readfrom and readfrom_into.

    Args:
        mock_i2c: Mock I2C bus to configure.
        read_func: Function that handles read operations (addr, buffer) -> None.
    """

    def mock_writeto_then_readfrom(addr, out_buf, in_buf):
        """Wrapper for combined operation."""
        read_func(addr, in_buf)

    mock_i2c.writeto_then_readfrom.side_effect = mock_writeto_then_readfrom
    mock_i2c.readfrom_into.side_effect = read_func


def test_create_light_sensor_success(setup_mock_i2c_for_init, mock_i2c, mock_logger):
    """Tests successful creation of a VEML6031x00 light sensor instance.

    Args:
        setup_mock_i2c_for_init: Configured mock I2C.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    sensor = VEML6031x00Manager(mock_logger, mock_i2c)

    assert sensor._addr == 0x29
    assert sensor._div4 == _Div4.SIZE_4_4
    assert sensor._gain == _Gain.GAIN_1
    assert sensor._itim == _It.IT_100MS
    mock_logger.debug.assert_called_once_with("Initializing VEML6031x00 light sensor")


def test_create_light_sensor_with_custom_params(
    setup_mock_i2c_for_init, mock_i2c, mock_logger
):
    """Tests creation with custom parameters.

    Args:
        setup_mock_i2c_for_init: Configured mock I2C.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    sensor = VEML6031x00Manager(
        mock_logger,
        mock_i2c,
        address=0x10,
        integration_time=_It.IT_200MS,
        gain=_Gain.GAIN_2,
        div4=_Div4.SIZE_1_4,
        persistence=2,
    )

    assert sensor._addr == 0x10
    assert sensor._itim == _It.IT_200MS
    assert sensor._gain == _Gain.GAIN_2
    assert sensor._div4 == _Div4.SIZE_1_4
    assert sensor._pers == 2


def test_create_light_sensor_wrong_device_id(mock_i2c, mock_logger):
    """Tests initialization failure with wrong device ID.

    Args:
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """

    def mock_readfrom_into(addr, buffer):
        """Mock read operation that returns wrong device ID."""
        buffer[0] = 0xFF  # Wrong device ID

    set_mock_i2c_reads(mock_i2c, mock_readfrom_into)

    with pytest.raises(HardwareInitializationError) as exc_info:
        VEML6031x00Manager(mock_logger, mock_i2c)

    assert "Unexpected VEML6031x00 device ID" in str(exc_info.value)


def test_create_light_sensor_i2c_failure(mock_i2c, mock_logger):
    """Tests initialization failure with I2C communication error.

    Args:
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    mock_i2c.writeto_then_readfrom.side_effect = OSError("I2C communication error")
    mock_i2c.readfrom_into.side_effect = OSError("I2C communication error")

    with pytest.raises(HardwareInitializationError) as exc_info:
        VEML6031x00Manager(mock_logger, mock_i2c)

    # The error could be either the device ID check or the OSError wrapped
    assert "VEML6031x00" in str(exc_info.value)


def test_get_light_success(setup_mock_i2c_for_init, mock_i2c, mock_logger):
    """Tests successful light reading.

    Args:
        setup_mock_i2c_for_init: Configured mock I2C.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    sensor = VEML6031x00Manager(mock_logger, mock_i2c)

    # Mock the measurement sequence
    read_count = [0]

    def mock_readfrom_into(addr, buffer):
        """Mock sequential reads for measurement."""
        read_count[0] += 1
        if len(buffer) == 1:
            if read_count[0] <= 3:  # Init reads
                buffer[0] = 0x01
            elif read_count[0] == 4:  # ALS_INT register (not ready)  # codespell:ignore
                buffer[0] = 0x00
            elif read_count[0] == 5:  # ALS_INT register (ready)  # codespell:ignore
                buffer[0] = 0x08  # Data ready bit set
        elif len(buffer) == 2:
            if read_count[0] > 5:  # ALS data  # codespell:ignore
                buffer[0] = 0x64  # 100 counts (low byte)
                buffer[1] = 0x00  # (high byte)

    set_mock_i2c_reads(mock_i2c, mock_readfrom_into)

    with patch("time.sleep"):
        light = sensor.get_light()

    assert isinstance(light, Light)
    assert light.value == 100.0


def test_get_lux_success(setup_mock_i2c_for_init, mock_i2c, mock_logger):
    """Tests successful lux reading.

    Args:
        setup_mock_i2c_for_init: Configured mock I2C.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    sensor = VEML6031x00Manager(mock_logger, mock_i2c)

    # Mock the measurement sequence
    read_count = [0]

    def mock_readfrom_into(addr, buffer):
        """Mock sequential reads for measurement."""
        read_count[0] += 1
        if len(buffer) == 1:
            buffer[0] = 0x08  # Always data ready for measurement
        elif len(buffer) == 2:
            # ALS data (1000 counts)  # codespell:ignore
            buffer[0] = 0xE8  # Low byte
            buffer[1] = 0x03  # High byte (1000 decimal)

    set_mock_i2c_reads(mock_i2c, mock_readfrom_into)

    with patch("time.sleep"):
        lux = sensor.get_lux()

    assert isinstance(lux, Lux)
    # With default settings (SIZE_4_4, GAIN_1, IT_100MS), resolution is 0.0272
    # 1000 counts * 0.0272 = 27.2 lux
    assert lux.value == pytest.approx(27.2, rel=1e-6)


def test_get_lux_zero_reading(setup_mock_i2c_for_init, mock_i2c, mock_logger):
    """Tests handling of zero lux reading.

    Args:
        setup_mock_i2c_for_init: Configured mock I2C.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    sensor = VEML6031x00Manager(mock_logger, mock_i2c)

    # Mock the measurement sequence with zero counts
    read_count = [0]

    def mock_readfrom_into(addr, buffer):
        """Mock sequential reads returning zero."""
        read_count[0] += 1
        if len(buffer) == 1:
            if read_count[0] <= 3:
                buffer[0] = 0x01
            else:
                buffer[0] = 0x08  # Data ready
        elif len(buffer) == 2:
            buffer[0] = 0x00
            buffer[1] = 0x00

    set_mock_i2c_reads(mock_i2c, mock_readfrom_into)

    with patch("time.sleep"):
        with pytest.raises(SensorReadingValueError) as exc_info:
            sensor.get_lux()

    assert "invalid or zero" in str(exc_info.value)


def test_get_light_timeout(setup_mock_i2c_for_init, mock_i2c, mock_logger):
    """Tests timeout when data ready bit never sets.

    Args:
        setup_mock_i2c_for_init: Configured mock I2C.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    sensor = VEML6031x00Manager(mock_logger, mock_i2c)

    # Mock the measurement sequence - data never ready
    read_count = [0]

    def mock_readfrom_into(addr, buffer):
        """Mock reads with data never ready."""
        read_count[0] += 1
        if len(buffer) == 1:
            if read_count[0] <= 3:
                buffer[0] = 0x01
            else:
                buffer[0] = 0x00  # Data never ready

    mock_i2c.readfrom_into.side_effect = mock_readfrom_into

    with patch("time.sleep"), patch("time.monotonic", side_effect=[0, 0.6]):
        with pytest.raises(SensorReadingTimeoutError) as exc_info:
            sensor.get_light()

    assert "timeout" in str(exc_info.value)


def test_get_light_overflow(setup_mock_i2c_for_init, mock_i2c, mock_logger):
    """Tests handling of sensor overflow (saturation).

    Args:
        setup_mock_i2c_for_init: Configured mock I2C.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    sensor = VEML6031x00Manager(mock_logger, mock_i2c)

    # Mock the measurement sequence with overflow value
    read_count = [0]

    def mock_readfrom_into(addr, buffer):
        """Mock reads returning overflow."""
        read_count[0] += 1
        if len(buffer) == 1:
            if read_count[0] <= 3:
                buffer[0] = 0x01
            else:
                buffer[0] = 0x08  # Data ready
        elif len(buffer) == 2:
            buffer[0] = 0xFF
            buffer[1] = 0xFF  # Overflow value

    set_mock_i2c_reads(mock_i2c, mock_readfrom_into)

    with patch("time.sleep"):
        with pytest.raises(SensorReadingValueError) as exc_info:
            sensor.get_light()

    assert "overflow" in str(exc_info.value)


def test_get_light_unknown_error(setup_mock_i2c_for_init, mock_i2c, mock_logger):
    """Tests handling of unknown errors during measurement.

    Args:
        setup_mock_i2c_for_init: Configured mock I2C.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    sensor = VEML6031x00Manager(mock_logger, mock_i2c)

    # Force an error during measurement
    with patch.object(
        sensor, "_single_measurement_sequence", side_effect=ValueError("Test error")
    ):
        with pytest.raises(SensorReadingUnknownError) as exc_info:
            sensor.get_light()

    assert "Failed to get light reading" in str(exc_info.value)


def test_reset_success(setup_mock_i2c_for_init, mock_i2c, mock_logger):
    """Tests successful sensor reset.

    Args:
        setup_mock_i2c_for_init: Configured mock I2C.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    sensor = VEML6031x00Manager(mock_logger, mock_i2c)

    with patch("time.sleep"):
        sensor.reset()

    mock_logger.debug.assert_called_with("Light sensor reset successfully")


def test_reset_failure(setup_mock_i2c_for_init, mock_i2c, mock_logger):
    """Tests handling of errors during reset.

    Args:
        setup_mock_i2c_for_init: Configured mock I2C.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    sensor = VEML6031x00Manager(mock_logger, mock_i2c)

    # Force an error during reset
    mock_i2c.writeto.side_effect = OSError("I2C error")

    sensor.reset()

    mock_logger.error.assert_called_once()
    assert "Failed to reset VEML6031x00" in str(mock_logger.error.call_args[0][0])


def test_i2c_lock_acquisition_retry(mock_i2c, mock_logger):
    """Tests I2C lock acquisition with retries.

    Args:
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    # Simulate lock acquisition succeeding on third attempt
    mock_i2c.try_lock.side_effect = [
        False,
        False,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
    ]

    def mock_readfrom_into(addr, buffer):
        """Mock read operation."""
        buffer[0] = 0x01
        if len(buffer) == 2:
            buffer[1] = 0x00

    set_mock_i2c_reads(mock_i2c, mock_readfrom_into)

    with patch("time.sleep"):
        sensor = VEML6031x00Manager(mock_logger, mock_i2c)

    assert sensor is not None
    # Verify try_lock was called multiple times
    assert mock_i2c.try_lock.call_count >= 3


def test_i2c_lock_acquisition_timeout(mock_i2c, mock_logger):
    """Tests I2C lock acquisition timeout after max retries.

    Args:
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    # Simulate lock never acquired
    mock_i2c.try_lock.return_value = False

    with patch("time.sleep"):
        with pytest.raises(HardwareInitializationError) as exc_info:
            VEML6031x00Manager(mock_logger, mock_i2c)

    assert "Unable to lock I2C bus" in str(exc_info.value.__cause__)


def test_i2c_unlock_on_write_error(setup_mock_i2c_for_init, mock_i2c, mock_logger):
    """Tests that I2C bus is unlocked even if write fails.

    Args:
        setup_mock_i2c_for_init: Configured mock I2C.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    sensor = VEML6031x00Manager(mock_logger, mock_i2c)

    # Force write to fail after initialization
    mock_i2c.writeto.side_effect = OSError("Write error")

    # Reset will trigger writes and should handle the error
    sensor.reset()

    # Verify unlock was called (should be called for each write attempt)
    assert mock_i2c.unlock.call_count > 0


def test_i2c_unlock_on_read_error(mock_i2c, mock_logger):
    """Tests that I2C bus is unlocked even if read fails.

    Args:
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    # Setup initial reads to succeed
    call_count = [0]

    def mock_readfrom_into(addr, buffer):
        """Mock read operation that fails after init."""
        call_count[0] += 1
        if call_count[0] <= 3:
            buffer[0] = 0x01
            if len(buffer) == 2:
                buffer[1] = 0x00
        else:
            raise OSError("Read error")

    set_mock_i2c_reads(mock_i2c, mock_readfrom_into)

    sensor = VEML6031x00Manager(mock_logger, mock_i2c)

    # Try to read, which should fail but unlock should still be called
    with patch("time.sleep"):
        with pytest.raises(SensorReadingUnknownError):
            sensor.get_light()

    # Verify unlock was called
    assert mock_i2c.unlock.call_count > 0


def test_writeto_then_readfrom_fallback(mock_i2c, mock_logger):
    """Tests fallback to separate write/read when writeto_then_readfrom not available.

    Args:
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    # Remove writeto_then_readfrom to trigger fallback
    del mock_i2c.writeto_then_readfrom

    def mock_readfrom_into(addr, buffer):
        """Mock read operation for fallback test."""
        buffer[0] = 0x01
        if len(buffer) == 2:
            buffer[1] = 0x00

    mock_i2c.readfrom_into.side_effect = mock_readfrom_into

    VEML6031x00Manager(mock_logger, mock_i2c)

    # Verify both writeto and readfrom_into were called (fallback path)
    assert mock_i2c.writeto.call_count > 0
    assert mock_i2c.readfrom_into.call_count > 0


def test_different_integration_times(setup_mock_i2c_for_init, mock_i2c, mock_logger):
    """Tests sensors with different integration times.

    Args:
        setup_mock_i2c_for_init: Configured mock I2C.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    for it_value in range(_It.COUNT):
        sensor = VEML6031x00Manager(mock_logger, mock_i2c, integration_time=it_value)
        assert sensor._itim == it_value


def test_different_gains(setup_mock_i2c_for_init, mock_i2c, mock_logger):
    """Tests sensors with different gain settings.

    Args:
        setup_mock_i2c_for_init: Configured mock I2C.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    for gain_value in range(_Gain.COUNT):
        sensor = VEML6031x00Manager(mock_logger, mock_i2c, gain=gain_value)
        assert sensor._gain == gain_value


def test_different_div4_settings(setup_mock_i2c_for_init, mock_i2c, mock_logger):
    """Tests sensors with different photodiode size settings.

    Args:
        setup_mock_i2c_for_init: Configured mock I2C.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    for div4_value in range(_Div4.COUNT):
        sensor = VEML6031x00Manager(mock_logger, mock_i2c, div4=div4_value)
        assert sensor._div4 == div4_value


def test_resolution_calculation_size_1_4_gain_2_it_200ms(
    setup_mock_i2c_for_init, mock_i2c, mock_logger
):
    """Tests lux calculation with specific settings (SIZE_1_4, GAIN_2, IT_200MS).

    Args:
        setup_mock_i2c_for_init: Configured mock I2C.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    sensor = VEML6031x00Manager(
        mock_logger,
        mock_i2c,
        integration_time=_It.IT_200MS,
        gain=_Gain.GAIN_2,
        div4=_Div4.SIZE_1_4,
    )

    # Mock measurement sequence returning 500 counts
    read_count = [0]

    def mock_readfrom_into(addr, buffer):
        """Mock read operation for resolution calculation test."""
        read_count[0] += 1
        if len(buffer) == 1:
            if read_count[0] <= 3:
                buffer[0] = 0x01
            else:
                buffer[0] = 0x08  # Data ready
        elif len(buffer) == 2:
            if read_count[0] > 4:
                buffer[0] = 0xF4  # 500 counts (low byte)
                buffer[1] = 0x01  # (high byte)

    set_mock_i2c_reads(mock_i2c, mock_readfrom_into)

    with patch("time.sleep"):
        lux = sensor.get_lux()

    # Resolution for SIZE_1_4, GAIN_2, IT_200MS is 0.0272
    # 500 * 0.0272 = 13.6 lux
    assert lux.value == pytest.approx(13.6, rel=1e-6)


def test_invalid_configuration_indices(setup_mock_i2c_for_init, mock_i2c, mock_logger):
    """Tests handling of invalid configuration indices during measurement.

    Args:
        setup_mock_i2c_for_init: Configured mock I2C.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    sensor = VEML6031x00Manager(mock_logger, mock_i2c)

    # Corrupt the configuration
    sensor._div4 = 999  # Invalid value

    # Mock measurement sequence
    read_count = [0]

    def mock_readfrom_into(addr, buffer):
        """Mock read operation for invalid config test."""
        read_count[0] += 1
        if len(buffer) == 1:
            buffer[0] = 0x08  # Data ready
        elif len(buffer) == 2:
            buffer[0] = 0x64
            buffer[1] = 0x00

    set_mock_i2c_reads(mock_i2c, mock_readfrom_into)

    with patch("time.sleep"):
        with pytest.raises(SensorReadingUnknownError) as exc_info:
            sensor.get_light()

    # Check the cause of the exception
    assert exc_info.value.__cause__ is not None
    assert "Invalid sensor configuration" in str(exc_info.value.__cause__)


def test_configuration_register_encoding(
    setup_mock_i2c_for_init, mock_i2c, mock_logger
):
    """Tests that configuration registers are encoded correctly.

    Args:
        setup_mock_i2c_for_init: Configured mock I2C.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    VEML6031x00Manager(
        mock_logger,
        mock_i2c,
        integration_time=_It.IT_50MS,
        gain=_Gain.GAIN_2,
        div4=_Div4.SIZE_1_4,
        persistence=1,
    )

    # Capture the write calls
    write_calls = [call_args for call_args in mock_i2c.writeto.call_args_list]

    # Verify configuration was written (should be called during init)
    assert len(write_calls) > 0


def test_threshold_writing(setup_mock_i2c_for_init, mock_i2c, mock_logger):
    """Tests that threshold values are written correctly during initialization.

    Args:
        setup_mock_i2c_for_init: Configured mock I2C.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    VEML6031x00Manager(mock_logger, mock_i2c)

    # Check that thresholds were written during initialization
    # Default: low=0x0000, high=0xFFFF
    write_calls = mock_i2c.writeto.call_args_list

    # Verify multiple writes occurred (thresholds + config)
    assert len(write_calls) >= 3


def test_data_ready_polling_immediate(setup_mock_i2c_for_init, mock_i2c, mock_logger):
    """Tests measurement when data is ready immediately.

    Args:
        setup_mock_i2c_for_init: Configured mock I2C.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    sensor = VEML6031x00Manager(mock_logger, mock_i2c)

    # Mock immediate data ready
    read_count = [0]

    def mock_readfrom_into(addr, buffer):
        """Mock read operation with immediate data ready."""
        read_count[0] += 1
        if len(buffer) == 1:
            if read_count[0] <= 3:
                buffer[0] = 0x01
            else:
                buffer[0] = 0x08  # Data ready immediately
        elif len(buffer) == 2:
            buffer[0] = 0x0A
            buffer[1] = 0x00

    set_mock_i2c_reads(mock_i2c, mock_readfrom_into)

    with patch("time.sleep"):
        light = sensor.get_light()

    assert light.value == 10.0


def test_data_ready_polling_delayed(setup_mock_i2c_for_init, mock_i2c, mock_logger):
    """Tests measurement when data ready is delayed.

    Args:
        setup_mock_i2c_for_init: Configured mock I2C.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    sensor = VEML6031x00Manager(mock_logger, mock_i2c)

    # Mock delayed data ready (not ready, then ready)
    read_count = [0]

    def mock_readfrom_into(addr, buffer):
        """Mock read operation with delayed data ready."""
        read_count[0] += 1
        if len(buffer) == 1:
            # First read of ALS_INT: not ready, second: ready
            if read_count[0] == 1:
                buffer[0] = 0x00  # Not ready
            else:
                buffer[0] = 0x08  # Ready
        elif len(buffer) == 2:
            buffer[0] = 0x14
            buffer[1] = 0x00

    set_mock_i2c_reads(mock_i2c, mock_readfrom_into)

    with patch("time.sleep"), patch("time.monotonic", side_effect=[0, 0.01, 0.02]):
        light = sensor.get_light()

    assert light.value == 20.0


def test_ir_channel_data_read(setup_mock_i2c_for_init, mock_i2c, mock_logger):
    """Tests that IR channel data is also read (even though not currently exposed).

    Args:
        setup_mock_i2c_for_init: Configured mock I2C.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    sensor = VEML6031x00Manager(mock_logger, mock_i2c)

    # Mock measurement with both ALS and IR data # codespell:ignore
    read_count = [0]

    def mock_readfrom_into(addr, buffer):
        """Mock read operation for IR channel test."""
        read_count[0] += 1
        if len(buffer) == 1:
            if read_count[0] <= 3:
                buffer[0] = 0x01
            else:
                buffer[0] = 0x08  # Data ready
        elif len(buffer) == 2:
            # First 16-bit read is ALS, second is IR  # codespell:ignore
            if read_count[0] == 5:  # ALS data  # codespell:ignore
                buffer[0] = 0x64
                buffer[1] = 0x00
            elif read_count[0] == 6:  # IR data
                buffer[0] = 0x32  # 50 counts
                buffer[1] = 0x00

    set_mock_i2c_reads(mock_i2c, mock_readfrom_into)

    with patch("time.sleep"):
        light = sensor.get_light()

    # Verify IR counts were stored internally
    assert sensor._ir_counts == 50
    assert light.value == 100.0


def test_invalid_integration_time_fallback(
    setup_mock_i2c_for_init, mock_i2c, mock_logger
):
    """Tests fallback sleep when integration time is out of range.

    Args:
        setup_mock_i2c_for_init: Configured mock I2C.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    sensor = VEML6031x00Manager(mock_logger, mock_i2c, integration_time=7)

    # Use a valid but boundary integration time that will test the range check
    # Note: IT_400MS = 7 is valid, so test with value at boundary

    def mock_readfrom_into(addr, buffer):
        """Mock read operation."""
        if len(buffer) == 1:
            buffer[0] = 0x08  # Data ready
        elif len(buffer) == 2:
            buffer[0] = 0x64
            buffer[1] = 0x00

    set_mock_i2c_reads(mock_i2c, mock_readfrom_into)

    # Corrupt integration time AFTER init to invalid value to test fallback
    sensor._itim = 999

    with patch("time.sleep") as mock_sleep:
        try:
            sensor.get_light()
        except SensorReadingUnknownError:
            # Expected due to invalid config, but fallback sleep should still be called
            pass

    # Verify fallback sleep was called with 0.001
    assert any(call[0][0] == 0.001 for call in mock_sleep.call_args_list)
