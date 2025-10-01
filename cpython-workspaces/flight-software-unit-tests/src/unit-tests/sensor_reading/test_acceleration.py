"""Unit tests for the Acceleration sensor reading class."""

from unittest.mock import patch

from hypothesis import given
from hypothesis import strategies as st

from pysquared.sensor_reading.acceleration import Acceleration


@given(
    st.floats(allow_nan=False, allow_infinity=False),
    st.floats(allow_nan=False, allow_infinity=False),
    st.floats(allow_nan=False, allow_infinity=False),
)
def test_acceleration_fuzzed_values(x, y, z):
    """Fuzz test Acceleration sensor reading with arbitrary float values."""
    reading = Acceleration(x, y, z)
    assert reading.x == x
    assert reading.y == y
    assert reading.z == z
    assert reading.value == (x, y, z)
    assert reading.timestamp is not None
    assert isinstance(reading.timestamp, (int, float))

    result_dict = reading.to_dict()
    assert isinstance(result_dict, dict)
    assert "timestamp" in result_dict
    assert "value" in result_dict
    assert result_dict["timestamp"] == reading.timestamp
    assert result_dict["value"] == (x, y, z)


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_acceleration_timestamp(ts):
    """Test that different Acceleration readings have timestamps."""
    with patch("time.time", side_effect=[ts]):
        reading1 = Acceleration(1.0, 2.0, 3.0)

        assert reading1.timestamp == ts
