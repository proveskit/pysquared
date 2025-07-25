"""Unit tests for the Temperature sensor reading class."""

import pytest

from pysquared.sensor_reading.temperature import Temperature


def test_temperature_initialization():
    """Test that Temperature sensor reading initializes correctly."""
    value = 25.5
    reading = Temperature(value)

    assert reading.value == value
    assert reading.timestamp is not None
    assert isinstance(reading.timestamp, (int, float))


def test_temperature_with_zero_value():
    """Test Temperature sensor reading with zero value."""
    reading = Temperature(0.0)

    assert reading.value == 0.0


def test_temperature_with_positive_value():
    """Test Temperature sensor reading with high temperature value."""
    high_temp = 85.0
    reading = Temperature(high_temp)

    assert reading.value == high_temp


def test_temperature_with_negative_value():
    """Test Temperature sensor reading with very low temperature."""
    very_cold = -273.15  # Absolute zero
    reading = Temperature(very_cold)

    assert reading.value == very_cold


def test_temperature_timestamp_uniqueness():
    """Test that different Temperature readings have different timestamps."""
    import time

    reading1 = Temperature(20.0)
    time.sleep(0.01)  # Small delay to ensure different timestamps
    reading2 = Temperature(25.0)

    assert reading1.timestamp != reading2.timestamp
    assert reading2.timestamp > reading1.timestamp


def test_temperature_precision():
    """Test Temperature sensor reading with high precision values."""
    precise_temp = 23.456789
    reading = Temperature(precise_temp)

    assert reading.value == pytest.approx(precise_temp, rel=1e-9)
