"""Unit tests for the base Reading class."""

from unittest.mock import patch

import pytest
from hypothesis import given
from hypothesis import strategies as st

from pysquared.sensor_reading.base import Reading


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_reading_timestamp(ts):
    """Test that Reading timestamps work with different values."""
    with patch("time.time", side_effect=[ts]):
        reading1 = Reading()

        assert reading1.timestamp == ts


def test_reading_value_not_implemented():
    """Test that Reading.value raises NotImplementedError when not overridden."""
    reading = Reading()

    with pytest.raises(
        NotImplementedError, match="Subclasses must implement this method."
    ):
        _ = reading.value
