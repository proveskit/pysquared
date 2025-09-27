"""Unit tests for the Magnetic sensor reading class."""

from unittest.mock import patch

from hypothesis import given
from hypothesis import strategies as st

from pysquared.sensor_reading.magnetic import Magnetic


@given(
    st.floats(allow_nan=False, allow_infinity=False),
    st.floats(allow_nan=False, allow_infinity=False),
    st.floats(allow_nan=False, allow_infinity=False),
)
def test_magnetic_fuzzed_values(x, y, z):
    """Fuzz test Magnetic sensor reading with arbitrary float values."""
    reading = Magnetic(x, y, z)
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
def test_magnetic_timestamp(ts):
    """Test that different Magnetic readings have timestamps."""
    with patch("time.time", side_effect=[ts]):
        reading1 = Magnetic(1.0, 2.0, 3.0)

        assert reading1.timestamp == ts
