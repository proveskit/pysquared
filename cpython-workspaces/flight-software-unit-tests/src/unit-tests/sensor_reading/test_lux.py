"""Unit tests for the Lux sensor reading class."""

from unittest.mock import patch

from hypothesis import given
from hypothesis import strategies as st

from pysquared.sensor_reading.lux import Lux


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_lux_fuzzed_values(value):
    """Fuzz test Lux sensor reading with arbitrary float values."""
    reading = Lux(value)
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
def test_lux_timestamp(ts):
    """Test that different Lux readings have timestamps."""
    with patch("time.time", side_effect=[ts]):
        reading1 = Lux(250.5)

        assert reading1.timestamp == ts
