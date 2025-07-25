"""Unit tests for the Light sensor reading class."""

from pysquared.sensor_reading.light import Light


def test_light_initialization():
    """Test that Light sensor reading initializes correctly."""
    value = 500.0
    reading = Light(value)

    assert reading.value == value
    assert reading.timestamp is not None
    assert isinstance(reading.timestamp, (int, float))


def test_light_with_zero_value():
    """Test Light sensor reading with zero value."""
    reading = Light(0.0)

    assert reading.value == 0.0


def test_light_with_negative_value():
    """Test Light sensor reading with negative value."""
    reading = Light(-10.5)

    assert reading.value == -10.5


def test_light_with_large_value():
    """Test Light sensor reading with large value."""
    large_value = 999999.9
    reading = Light(large_value)

    assert reading.value == large_value


def test_light_timestamp_uniqueness():
    """Test that different Light readings have different timestamps."""
    import time

    reading1 = Light(100.0)
    time.sleep(0.01)  # Small delay to ensure different timestamps
    reading2 = Light(200.0)

    assert reading1.timestamp != reading2.timestamp
    assert reading2.timestamp > reading1.timestamp
