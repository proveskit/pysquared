"""Unit tests for the Light sensor reading class."""

from unittest.mock import patch

from hypothesis import given
from hypothesis import strategies as st

from pysquared.sensor_reading.light import Light


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_light_fuzzed_values(value):
    """Fuzz test Light sensor reading with arbitrary float values."""
    reading = Light(value)
    assert reading.value == value
    assert reading.timestamp is not None
    assert isinstance(reading.timestamp, (int, float))

    result_dict = reading.to_dict()
    assert isinstance(result_dict, dict)
    assert "timestamp" in result_dict
    assert "value" in result_dict
    assert result_dict["timestamp"] == reading.timestamp
    assert result_dict["value"] == value


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_light_timestamp(ts):
    """Test that different Light readings have timestamps."""
    with patch("time.time", side_effect=[ts]):
        reading1 = Light(500.0)

        assert reading1.timestamp == ts
