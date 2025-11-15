"""Test the VEML6031X00Manager class."""

from typing import Generator
from unittest.mock import MagicMock, PropertyMock, patch, call

import pytest
from pysquared.hardware.exception import HardwareInitializationError
from pysquared.hardware.light_sensor.manager.veml6031x00 import (
    VEML6031X00Manager,
    _VEML6031X00,
)
from pysquared.logger import Logger
from pysquared.sensor_reading.error import (
    SensorReadingUnknownError,
    SensorReadingValueError,
)
from pysquared.sensor_reading.light import Light
from pysquared.sensor_reading.lux import Lux


@pytest.fixture
def mock_i2c():
    """Fixture to mock the I2C bus."""
    return MagicMock()


@pytest.fixture
def mock_logger():
    """Fixture to mock the logger."""
    return MagicMock(Logger)


@pytest.fixture
def mock_veml6031x00(mock_i2c: MagicMock) -> Generator[MagicMock, None, None]:
    """Mocks the internal _VEML6031X00 driver class.
    Yields:
        MagicMock class for _VEML6031X00
    """
    with patch(
        "pysquared.hardware.light_sensor.manager.veml6031x00._VEML6031X00"
    ) as mock_class:
        mock_instance = MagicMock()
        mock_instance.light = 1000.0
        mock_instance.lux = 500.0
        mock_class.return_value = mock_instance
        yield mock_class


def test_create_light_sensor(mock_veml6031x00, mock_i2c, mock_logger):
    """Verify successful creation of the manager and driver init logging."""
    sensor = VEML6031X00Manager(mock_logger, mock_i2c)
    assert sensor._light_sensor is not None
    mock_logger.debug.assert_called_once_with("Initializing VEML6031X00 light sensor")


def test_create_light_sensor_failed(mock_veml6031x00, mock_i2c, mock_logger):
    """Ensure initialization failure raises HardwareInitializationError."""
    mock_veml6031x00.side_effect = Exception("Simulated VEML6031X00 failure")
    with pytest.raises(HardwareInitializationError):
        _ = VEML6031X00Manager(mock_logger, mock_i2c)
    mock_logger.debug.assert_called_with("Initializing VEML6031X00 light sensor")


def test_get_light_success(mock_veml6031x00, mock_i2c, mock_logger):
    """Read non-unit light value successfully and wrap in Light."""
    sensor = VEML6031X00Manager(mock_logger, mock_i2c)
    sensor._light_sensor = MagicMock()
    sensor._light_sensor.light = 1234.0

    light = sensor.get_light()
    assert isinstance(light, Light)
    assert light.value == pytest.approx(1234.0, rel=1e-6)


def test_get_light_failure(mock_veml6031x00, mock_i2c, mock_logger):
    """Propagate read exception as SensorReadingUnknownError for light."""
    sensor = VEML6031X00Manager(mock_logger, mock_i2c)
    mock_instance = MagicMock()
    sensor._light_sensor = mock_instance
    mock_prop = PropertyMock(side_effect=RuntimeError("Simulated retrieval error"))
    type(sensor._light_sensor).light = mock_prop

    with pytest.raises(SensorReadingUnknownError):
        sensor.get_light()


def test_get_lux_success(mock_veml6031x00, mock_i2c, mock_logger):
    """Read lux successfully and wrap in Lux."""
    sensor = VEML6031X00Manager(mock_logger, mock_i2c)
    sensor._light_sensor = MagicMock()
    sensor._light_sensor.lux = 321.0

    lux = sensor.get_lux()
    assert isinstance(lux, Lux)
    assert lux.value == pytest.approx(321.0, rel=1e-6)


def test_get_lux_failure(mock_veml6031x00, mock_i2c, mock_logger):
    """Propagate read exception as SensorReadingUnknownError for lux."""
    sensor = VEML6031X00Manager(mock_logger, mock_i2c)
    mock_instance = MagicMock()
    sensor._light_sensor = mock_instance
    mock_prop = PropertyMock(side_effect=RuntimeError("Simulated retrieval error"))
    type(sensor._light_sensor).lux = mock_prop

    with pytest.raises(SensorReadingUnknownError):
        sensor.get_lux()


def test_get_lux_zero_reading(mock_veml6031x00, mock_i2c, mock_logger):
    """Zero lux is invalid and should raise SensorReadingValueError."""
    sensor = VEML6031X00Manager(mock_logger, mock_i2c)
    sensor._light_sensor = MagicMock()
    sensor._light_sensor.lux = 0.0

    with pytest.raises(SensorReadingValueError):
        sensor.get_lux()


def test_get_lux_none_reading(mock_veml6031x00, mock_i2c, mock_logger):
    """None lux is invalid and should raise SensorReadingValueError."""
    sensor = VEML6031X00Manager(mock_logger, mock_i2c)
    sensor._light_sensor = MagicMock()
    sensor._light_sensor.lux = None

    with pytest.raises(SensorReadingValueError):
        sensor.get_lux()


def test_get_lux_saturation_raw(mock_veml6031x00, mock_i2c, mock_logger):
    """Raw ambient-light of 0xFFFF indicates saturation - currently not detected."""
    # Note: The current implementation does not check for saturation (0xFFFF).
    # This test verifies that high values are still returned as valid lux readings.
    sensor = VEML6031X00Manager(mock_logger, mock_i2c)
    sensor._light_sensor = MagicMock()
    # Simulate a very high lux value (but not checking for 0xFFFF saturation)
    sensor._light_sensor.lux = 65535.0

    lux = sensor.get_lux()
    assert isinstance(lux, Lux)
    assert lux.value == pytest.approx(65535.0, rel=1e-6)


def test_reset_success(mock_veml6031x00, mock_i2c, mock_logger):
    """Reset toggles shutdown bit and logs success."""
    with patch("time.sleep"):
        sensor = VEML6031X00Manager(mock_logger, mock_i2c)
        # The driver is already mocked via the fixture
        # Reset will set light_shutdown to True then False

        sensor.reset()
        # Verify the logger was called
        mock_logger.debug.assert_called_with("VEML6031X00 light sensor reset successfully")


def test_reset_failure(mock_veml6031x00, mock_i2c, mock_logger):
    """Reset failure is logged at error level."""
    sensor = VEML6031X00Manager(mock_logger, mock_i2c)
    # Make setting light_shutdown raise an error
    type(sensor._light_sensor).light_shutdown = PropertyMock(
        side_effect=RuntimeError("Simulated reset error")
    )

    sensor.reset()
    # Verify error was logged (call_args_list since multiple calls may happen)
    assert mock_logger.error.call_count >= 1


def test_create_light_sensor_with_custom_integration_time(
    mock_veml6031x00, mock_i2c, mock_logger
):
    """Tests successful creation with custom integration time.

    Args:
        mock_veml6031x00: Mocked _VEML6031X00 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    sensor = VEML6031X00Manager(mock_logger, mock_i2c, integration_time=5)

    assert sensor._light_sensor is not None
    assert sensor._light_sensor.light_integration_time == 5
    mock_logger.debug.assert_called_once_with("Initializing VEML6031X00 light sensor")


def test_get_auto_lux_success(mock_veml6031x00, mock_i2c, mock_logger):
    """Tests successful retrieval of the auto lux reading.

    Args:
        mock_veml6031x00: Mocked _VEML6031X00 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    sensor = VEML6031X00Manager(mock_logger, mock_i2c)
    sensor._light_sensor = MagicMock()
    sensor._light_sensor.autolux = 275.5

    autolux = sensor.get_auto_lux()
    assert isinstance(autolux, Lux)
    assert autolux.value == pytest.approx(275.5, rel=1e-6)


def test_get_auto_lux_failure(mock_veml6031x00, mock_i2c, mock_logger):
    """Tests handling of exceptions when retrieving the auto lux reading.

    Args:
        mock_veml6031x00: Mocked _VEML6031X00 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    sensor = VEML6031X00Manager(mock_logger, mock_i2c)
    mock_instance = MagicMock()
    sensor._light_sensor = mock_instance
    mock_prop = PropertyMock(side_effect=RuntimeError("Simulated autolux error"))
    type(sensor._light_sensor).autolux = mock_prop

    with pytest.raises(SensorReadingUnknownError):
        sensor.get_auto_lux()


def test_get_auto_lux_zero_reading(mock_veml6031x00, mock_i2c, mock_logger):
    """Tests handling of zero auto lux reading (should raise SensorReadingValueError).

    Args:
        mock_veml6031x00: Mocked _VEML6031X00 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    sensor = VEML6031X00Manager(mock_logger, mock_i2c)
    sensor._light_sensor = MagicMock()
    sensor._light_sensor.autolux = 0.0

    with pytest.raises(SensorReadingValueError):
        sensor.get_auto_lux()


def test_get_auto_lux_none_reading(mock_veml6031x00, mock_i2c, mock_logger):
    """Tests handling of None auto lux reading (should raise SensorReadingValueError).

    Args:
        mock_veml6031x00: Mocked _VEML6031X00 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    sensor = VEML6031X00Manager(mock_logger, mock_i2c)
    sensor._light_sensor = MagicMock()
    sensor._light_sensor.autolux = None

    with pytest.raises(SensorReadingValueError):
        sensor.get_auto_lux()


def test_get_light_with_various_values(mock_veml6031x00, mock_i2c, mock_logger):
    """Tests get_light with various valid light values.

    Args:
        mock_veml6031x00: Mocked _VEML6031X00 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    sensor = VEML6031X00Manager(mock_logger, mock_i2c)
    sensor._light_sensor = MagicMock()

    test_values = [0.0, 100.5, 1000.0, 50000.0, 65535.0]
    for value in test_values:
        sensor._light_sensor.light = value
        light = sensor.get_light()
        assert isinstance(light, Light)
        assert light.value == pytest.approx(value, rel=1e-6)


def test_get_lux_with_various_valid_values(mock_veml6031x00, mock_i2c, mock_logger):
    """Tests get_lux with various valid lux values (non-zero, non-None).

    Args:
        mock_veml6031x00: Mocked _VEML6031X00 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    sensor = VEML6031X00Manager(mock_logger, mock_i2c)
    sensor._light_sensor = MagicMock()

    # Only test positive, non-zero values since zero and None are invalid
    test_values = [0.001, 1.5, 100.0, 500.5, 10000.0]
    for value in test_values:
        sensor._light_sensor.lux = value
        lux = sensor.get_lux()
        assert isinstance(lux, Lux)
        assert lux.value == pytest.approx(value, rel=1e-6)


def test_is_invalid_lux_method(mock_veml6031x00, mock_i2c, mock_logger):
    """Tests the _is_invalid_lux static method directly.

    Args:
        mock_veml6031x00: Mocked _VEML6031X00 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    # Test invalid values
    assert VEML6031X00Manager._is_invalid_lux(None) is True
    assert VEML6031X00Manager._is_invalid_lux(0) is True
    assert VEML6031X00Manager._is_invalid_lux(0.0) is True

    # Test valid values
    assert VEML6031X00Manager._is_invalid_lux(0.001) is False
    assert VEML6031X00Manager._is_invalid_lux(1.0) is False
    assert VEML6031X00Manager._is_invalid_lux(100.5) is False
    assert VEML6031X00Manager._is_invalid_lux(65535.0) is False


# ============================================================================
# Tests for the internal _VEML6031X00 driver class
# ============================================================================


def test_veml6031x00_driver_init_success():
    """Test successful initialization of the _VEML6031X00 driver."""
    mock_i2c = MagicMock()

    with patch("pysquared.hardware.light_sensor.manager.veml6031x00.i2cdevice"):
        driver = _VEML6031X00(mock_i2c)

        # Verify initialization set the correct defaults
        assert driver.light_gain == _VEML6031X00.ALS_GAIN_1_2
        assert driver.light_shutdown is False


def test_veml6031x00_driver_init_retry_logic():
    """Test that the driver retries initialization on OSError."""
    mock_i2c = MagicMock()

    with patch("pysquared.hardware.light_sensor.manager.veml6031x00.i2cdevice"):
        with patch.object(_VEML6031X00, "light_gain", new_callable=PropertyMock) as mock_gain:
            with patch.object(_VEML6031X00, "light_shutdown", new_callable=PropertyMock) as mock_shutdown:
                # First two attempts raise OSError, third succeeds
                mock_gain.side_effect = [OSError(), OSError(), None]
                mock_shutdown.side_effect = [None, None, None]

                driver = _VEML6031X00(mock_i2c)

                # Should have tried 3 times
                assert mock_gain.call_count == 3


def test_veml6031x00_driver_init_failure_after_retries():
    """Test that the driver raises RuntimeError after all retries fail."""
    mock_i2c = MagicMock()

    with patch("pysquared.hardware.light_sensor.manager.veml6031x00.i2cdevice"):
        with patch.object(_VEML6031X00, "light_gain", new_callable=PropertyMock) as mock_gain:
            # All attempts raise OSError
            mock_gain.side_effect = OSError()

            with pytest.raises(RuntimeError, match="Unable to enable VEML6031X00 device"):
                _VEML6031X00(mock_i2c)


def test_veml6031x00_integration_time_value():
    """Test the integration_time_value() method."""
    mock_i2c = MagicMock()

    with patch("pysquared.hardware.light_sensor.manager.veml6031x00.i2cdevice"):
        driver = _VEML6031X00(mock_i2c)

        # Test different integration time settings
        driver.light_integration_time = _VEML6031X00.ALS_3_125MS
        assert driver.integration_time_value() == 3.125

        driver.light_integration_time = _VEML6031X00.ALS_100MS
        assert driver.integration_time_value() == 100

        driver.light_integration_time = _VEML6031X00.ALS_400MS
        assert driver.integration_time_value() == 400


def test_veml6031x00_gain_value():
    """Test the gain_value() method."""
    mock_i2c = MagicMock()

    with patch("pysquared.hardware.light_sensor.manager.veml6031x00.i2cdevice"):
        driver = _VEML6031X00(mock_i2c)

        # Test different gain settings
        driver.light_gain = _VEML6031X00.ALS_GAIN_1
        assert driver.gain_value() == 1

        driver.light_gain = _VEML6031X00.ALS_GAIN_2
        assert driver.gain_value() == 2

        driver.light_gain = _VEML6031X00.ALS_GAIN_2_3
        assert driver.gain_value() == pytest.approx(0.66, rel=1e-6)

        driver.light_gain = _VEML6031X00.ALS_GAIN_1_2
        assert driver.gain_value() == 0.5


def test_veml6031x00_resolution_at_max_settings():
    """Test resolution() returns base value at maximum sensitivity settings."""
    mock_i2c = MagicMock()

    with patch("pysquared.hardware.light_sensor.manager.veml6031x00.i2cdevice"):
        driver = _VEML6031X00(mock_i2c)

        # Set to maximum sensitivity (gain=2, integration=400ms)
        driver.light_gain = _VEML6031X00.ALS_GAIN_2
        driver.light_integration_time = _VEML6031X00.ALS_400MS

        assert driver.resolution() == pytest.approx(0.0034, rel=1e-6)


def test_veml6031x00_resolution_with_different_settings():
    """Test resolution() calculates correctly for non-max settings."""
    mock_i2c = MagicMock()

    with patch("pysquared.hardware.light_sensor.manager.veml6031x00.i2cdevice"):
        driver = _VEML6031X00(mock_i2c)

        # Set to lower sensitivity (gain=1, integration=100ms)
        driver.light_gain = _VEML6031X00.ALS_GAIN_1
        driver.light_integration_time = _VEML6031X00.ALS_100MS

        # Resolution should be: 0.0034 * (400/100) * (2/1) = 0.0034 * 4 * 2 = 0.0272
        expected = 0.0034 * (400 / 100) * (2 / 1)
        assert driver.resolution() == pytest.approx(expected, rel=1e-6)


def test_veml6031x00_lux_property():
    """Test the lux property calculation."""
    mock_i2c = MagicMock()

    with patch("pysquared.hardware.light_sensor.manager.veml6031x00.i2cdevice"):
        driver = _VEML6031X00(mock_i2c)

        # Set gain and integration time
        driver.light_gain = _VEML6031X00.ALS_GAIN_2
        driver.light_integration_time = _VEML6031X00.ALS_400MS

        # Mock the light reading (read-only property)
        with patch.object(_VEML6031X00, "light", new_callable=PropertyMock) as mock_light:
            mock_light.return_value = 1000

            # Lux should be resolution * light = 0.0034 * 1000 = 3.4
            assert driver.lux == pytest.approx(3.4, rel=1e-6)


def test_veml6031x00_autolux_finds_optimal_settings():
    """Test autolux property finds optimal gain/integration settings."""
    mock_i2c = MagicMock()

    with patch("pysquared.hardware.light_sensor.manager.veml6031x00.i2cdevice"):
        with patch("time.sleep"):  # Mock sleep to speed up test
            driver = _VEML6031X00(mock_i2c)

            # Set initial settings
            original_gain = _VEML6031X00.ALS_GAIN_1_2
            original_integration = _VEML6031X00.ALS_100MS
            driver.light_gain = original_gain
            driver.light_integration_time = original_integration

            # Create a counter to track which config we're on
            call_count = [0]

            def mock_light_reading():
                """Return different values based on call count."""
                call_count[0] += 1
                # First config (ALS_GAIN_2, ALS_400MS): too high (saturated)
                if call_count[0] == 1:
                    return 70000
                # Second config (ALS_GAIN_1, ALS_400MS): in valid range
                return 5000

            def mock_lux_reading():
                """Return lux based on current settings."""
                # Calculate based on the test values
                if call_count[0] == 1:
                    return 238.0  # High lux for saturated reading
                return 17.0  # Valid lux for good reading

            # Patch both light and lux properties
            with patch.object(
                type(driver), "light", new_callable=PropertyMock
            ) as mock_light:
                with patch.object(
                    type(driver), "lux", new_callable=PropertyMock
                ) as mock_lux:
                    mock_light.side_effect = mock_light_reading
                    mock_lux.side_effect = mock_lux_reading

                    result = driver.autolux

                    # Should return the lux from the valid configuration
                    assert result == pytest.approx(17.0, rel=1e-6)

                    # Original settings should be restored
                    assert driver.light_gain == original_gain
                    assert driver.light_integration_time == original_integration


def test_veml6031x00_autolux_no_valid_range_found():
    """Test autolux when no readings are in the optimal range."""
    mock_i2c = MagicMock()

    with patch("pysquared.hardware.light_sensor.manager.veml6031x00.i2cdevice"):
        with patch("time.sleep"):  # Mock sleep to speed up test
            driver = _VEML6031X00(mock_i2c)

            # Set initial settings
            original_gain = _VEML6031X00.ALS_GAIN_1
            original_integration = _VEML6031X00.ALS_200MS
            driver.light_gain = original_gain
            driver.light_integration_time = original_integration

            # Mock all readings to be out of range (too low)
            with patch.object(
                type(driver), "light", new_callable=PropertyMock
            ) as mock_light:
                with patch.object(
                    type(driver), "lux", new_callable=PropertyMock
                ) as mock_lux:
                    # All readings are too low (< 100)
                    mock_light.return_value = 50
                    mock_lux.return_value = 0.17

                    result = driver.autolux

                    # Should return the last configuration's lux
                    assert result == pytest.approx(0.17, rel=1e-6)

                    # Original settings should be restored
                    assert driver.light_gain == original_gain
                    assert driver.light_integration_time == original_integration