"""Unit tests for the Lux sensor reading class."""

from pysquared.sensor_reading.lux import Lux


def test_lux_initialization():
    """Test that Lux sensor reading initializes correctly."""
    value = 250.5
    reading = Lux(value)

    assert reading.value == value
    assert reading.timestamp is not None
    assert isinstance(reading.timestamp, (int, float))


def test_lux_with_zero_value():
    """Test Lux sensor reading with zero value."""
    reading = Lux(0.0)

    assert reading.value == 0.0


def test_lux_with_negative_value():
    """Test Lux sensor reading with negative value (edge case)."""
    reading = Lux(-5.0)

    assert reading.value == -5.0


def test_lux_with_typical_indoor_value():
    """Test Lux sensor reading with typical indoor lighting value."""
    indoor_lux = 300.0  # Typical indoor lighting
    reading = Lux(indoor_lux)

    assert reading.value == indoor_lux


def test_lux_with_typical_outdoor_value():
    """Test Lux sensor reading with typical outdoor lighting value."""
    outdoor_lux = 10000.0  # Typical daylight
    reading = Lux(outdoor_lux)

    assert reading.value == outdoor_lux


def test_lux_with_very_high_value():
    """Test Lux sensor reading with very high value (direct sunlight)."""
    sunlight_lux = 100000.0  # Direct sunlight
    reading = Lux(sunlight_lux)

    assert reading.value == sunlight_lux


def test_lux_timestamp_uniqueness():
    """Test that different Lux readings have different timestamps."""
    import time

    reading1 = Lux(100.0)
    time.sleep(0.01)  # Small delay to ensure different timestamps
    reading2 = Lux(200.0)

    assert reading1.timestamp != reading2.timestamp
    assert reading2.timestamp > reading1.timestamp
