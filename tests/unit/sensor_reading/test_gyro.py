"""Unit tests for the Gyro sensor reading class."""

from unittest.mock import patch

from hypothesis import given
from hypothesis import strategies as st

from pysquared.sensor_reading.gyro import Gyro


@given(
    st.floats(allow_nan=False, allow_infinity=False),
    st.floats(allow_nan=False, allow_infinity=False),
    st.floats(allow_nan=False, allow_infinity=False),
)
def test_gyro_fuzzed_values(x, y, z):
    """Fuzz test Gyro sensor reading with arbitrary float values."""
    reading = Gyro(x, y, z)
    assert reading.x == x
    assert reading.y == y
    assert reading.z == z
    assert reading.value == (x, y, z)
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
def test_gyro_timestamp(ts):
    """Test that different Gyro readings have timestamps."""
    with patch("time.time", side_effect=[ts]):
        reading1 = Gyro(1.0, 2.0, 3.0)

        assert reading1.timestamp == ts
