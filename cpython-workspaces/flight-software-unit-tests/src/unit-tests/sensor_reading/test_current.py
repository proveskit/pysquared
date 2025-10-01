"""Unit tests for the Current sensor reading class."""

from unittest.mock import patch

from hypothesis import given
from hypothesis import strategies as st

from pysquared.sensor_reading.current import Current


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_current_fuzzed_values(value):
    """Fuzz test Current sensor reading with arbitrary float values."""
    reading = Current(value)
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
def test_current_timestamp(ts):
    """Test that different Current readings have timestamps."""
    with patch("time.time", side_effect=[ts]):
        reading1 = Current(150.5)

        assert reading1.timestamp == ts
