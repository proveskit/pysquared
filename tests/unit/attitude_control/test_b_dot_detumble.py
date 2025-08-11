"""Unit tests for the b_dot_detumble module.

This module contains property-based unit tests using Hypothesis for the
`b_dot_detumble` module, which provides functions for spacecraft detumbling
using the B-dot algorithm.
"""

import math
from unittest.mock import patch

import pytest
from hypothesis import assume, example, given
from hypothesis import strategies as st

from pysquared.attitude_control.b_dot_detumble import BDotDetumble
from pysquared.sensor_reading.magnetic import Magnetic

# Strategy for generating finite float values
finite_floats = st.floats(
    min_value=-1e3, max_value=1e3, allow_nan=False, allow_infinity=False
)

# Strategy for generating positive finite float values
positive_floats = st.floats(
    min_value=1e-6, max_value=1e3, allow_nan=False, allow_infinity=False
)

# Strategy for generating magnetic field tuples
magnetic_field_tuples = st.tuples(finite_floats, finite_floats, finite_floats)

# Strategy for generating timestamps with reasonable differences
timestamps = st.floats(
    min_value=0, max_value=1e6, allow_nan=False, allow_infinity=False
)


def magnetic_with_timestamp(x: float, y: float, z: float, timestamp: float) -> Magnetic:
    """Create a Magnetic object with a specific timestamp."""
    with patch("time.time", return_value=timestamp):
        return Magnetic(x, y, z)


class TestBDotDetumble:
    """Test class for BDotDetumble functionality."""

    @given(
        st.floats(min_value=0.1, max_value=100, allow_nan=False, allow_infinity=False)
    )
    def test_initialization(self, gain: float):
        """Test that BDotDetumble initializes correctly with various gain values."""
        detumble = BDotDetumble(gain=gain)
        assert detumble._gain == gain

    def test_default_initialization(self):
        """Test that BDotDetumble initializes with default gain of 1.0."""
        detumble = BDotDetumble()
        assert detumble._gain == 1.0

    @given(magnetic_field_tuples)
    @example((0, 0, 0))  # Test zero vector
    @example((1, 0, 0))  # Test unit vectors
    @example((0, 1, 0))
    @example((0, 0, 1))
    def test_magnitude_properties(self, mag_field: tuple[float, float, float]):
        """Test mathematical properties of the magnitude function."""
        x, y, z = mag_field
        magnetic = magnetic_with_timestamp(x, y, z, 0.0)

        magnitude = BDotDetumble._magnitude(magnetic)

        # Magnitude should always be non-negative
        assert magnitude >= 0

        # Test that magnitude matches expected mathematical formula
        expected_magnitude = math.sqrt(x**2 + y**2 + z**2)
        assert pytest.approx(expected_magnitude, 1e-10) == magnitude

        # Magnitude should be zero if and only if all components are effectively zero
        if abs(x) < 1e-12 and abs(y) < 1e-12 and abs(z) < 1e-12:
            assert pytest.approx(0, 1e-12) == magnitude
        else:
            # If any component is non-zero, magnitude should be positive
            if max(abs(x), abs(y), abs(z)) > 1e-12:
                assert magnitude > 0

    @given(
        magnetic_field_tuples,
        magnetic_field_tuples,
        st.floats(min_value=0.1, max_value=1000, allow_nan=False, allow_infinity=False),
    )
    def test_dB_dt_basic_properties(
        self,
        prev_field: tuple[float, float, float],
        curr_field: tuple[float, float, float],
        dt: float,
    ):
        """Test basic mathematical properties of dB_dt calculation."""
        prev_x, prev_y, prev_z = prev_field
        curr_x, curr_y, curr_z = curr_field

        prev_magnetic = magnetic_with_timestamp(prev_x, prev_y, prev_z, 0.0)
        curr_magnetic = magnetic_with_timestamp(curr_x, curr_y, curr_z, dt)

        dB_dt = BDotDetumble._dB_dt(curr_magnetic, prev_magnetic)

        # Should return a tuple of three floats
        assert isinstance(dB_dt, tuple)
        assert len(dB_dt) == 3
        assert all(isinstance(x, float) for x in dB_dt)

        # Verify the calculation matches expected formula
        expected_dx_dt = (curr_x - prev_x) / dt
        expected_dy_dt = (curr_y - prev_y) / dt
        expected_dz_dt = (curr_z - prev_z) / dt

        assert pytest.approx(expected_dx_dt, 1e-10) == dB_dt[0]
        assert pytest.approx(expected_dy_dt, 1e-10) == dB_dt[1]
        assert pytest.approx(expected_dz_dt, 1e-10) == dB_dt[2]

    @given(magnetic_field_tuples, positive_floats)
    def test_dB_dt_zero_change(self, mag_field: tuple[float, float, float], dt: float):
        """Test that dB_dt is zero when magnetic field doesn't change."""
        x, y, z = mag_field

        prev_magnetic = magnetic_with_timestamp(x, y, z, 0.0)
        curr_magnetic = magnetic_with_timestamp(x, y, z, dt)

        dB_dt = BDotDetumble._dB_dt(curr_magnetic, prev_magnetic)

        # All components should be zero
        assert pytest.approx(0, 1e-10) == dB_dt[0]
        assert pytest.approx(0, 1e-10) == dB_dt[1]
        assert pytest.approx(0, 1e-10) == dB_dt[2]

    @given(
        magnetic_field_tuples,
        st.floats(min_value=-1000, max_value=0, allow_nan=False, allow_infinity=False),
    )
    @example((0, 0, 0), 0)  # Test zero dt
    @example((0, 0, 0), -1.0)  # Test negative dt
    def test_dB_dt_zero_division(
        self, mag_field: tuple[float, float, float], dt: float
    ):
        """Test behavior when time difference is zero or negative."""
        x, y, z = mag_field

        prev_magnetic = magnetic_with_timestamp(x, y, z, 0.0)
        curr_magnetic = magnetic_with_timestamp(x, y, z, dt)

        # This should raise a ValueError due to zero time difference
        with pytest.raises(ValueError):
            BDotDetumble._dB_dt(curr_magnetic, prev_magnetic)

    @given(
        magnetic_field_tuples, magnetic_field_tuples, positive_floats, positive_floats
    )
    def test_dipole_moment_properties(
        self,
        prev_field: tuple[float, float, float],
        curr_field: tuple[float, float, float],
        dt: float,
        gain: float,
    ):
        """Test properties of dipole moment calculation."""
        prev_x, prev_y, prev_z = prev_field
        curr_x, curr_y, curr_z = curr_field

        # Skip test if current magnetic field magnitude is too small
        curr_magnitude = math.sqrt(curr_x**2 + curr_y**2 + curr_z**2)
        assume(curr_magnitude > 1e-6)

        detumble = BDotDetumble(gain)

        prev_magnetic = magnetic_with_timestamp(prev_x, prev_y, prev_z, 0.0)
        curr_magnetic = magnetic_with_timestamp(curr_x, curr_y, curr_z, dt)

        dipole = detumble.dipole_moment(curr_magnetic, prev_magnetic)

        # Should return a tuple of three floats
        assert isinstance(dipole, tuple)
        assert len(dipole) == 3
        assert all(isinstance(x, float) for x in dipole)

    @given(magnetic_field_tuples, positive_floats, positive_floats)
    def test_dipole_moment_zero_change(
        self, mag_field: tuple[float, float, float], dt: float, gain: float
    ):
        """Test that dipole moment is zero when magnetic field doesn't change."""
        x, y, z = mag_field

        # Skip test if magnetic field magnitude is too small
        magnitude = math.sqrt(x**2 + y**2 + z**2)
        assume(magnitude > 1e-6)

        detumble = BDotDetumble(gain=gain)

        prev_magnetic = magnetic_with_timestamp(x, y, z, 0.0)
        curr_magnetic = magnetic_with_timestamp(x, y, z, dt)

        dipole = detumble.dipole_moment(curr_magnetic, prev_magnetic)

        # All components should be approximately zero
        assert abs(dipole[0]) < 1e-6
        assert abs(dipole[1]) < 1e-6
        assert abs(dipole[2]) < 1e-6

    def test_dipole_moment_zero_magnitude(self):
        """Test behavior when current magnetic field magnitude is zero."""
        detumble = BDotDetumble(gain=1.0)

        # Create zero magnetic field
        prev_magnetic = magnetic_with_timestamp(0, 0, 0, 0.0)
        curr_magnetic = magnetic_with_timestamp(0, 0, 0, 1.0)

        # This should raise a ValueError due to zero magnitude
        with pytest.raises(ValueError):
            detumble.dipole_moment(curr_magnetic, prev_magnetic)

    @given(
        magnetic_field_tuples,
        st.floats(min_value=-1000, max_value=0, allow_nan=False, allow_infinity=False),
    )
    @example((1, 0, 0), 0.0)  # Test zero timestamp
    @example((1, 0, 0), -1.0)  # Test negative timestamp
    def test_dipole_moment_zero_or_negative_timestamp(
        self, mag_field: tuple[float, float, float], dt: float
    ):
        """Test behavior when current magnetic field timestamp is zero or negative."""
        x, y, z = mag_field

        # Skip test if current magnetic field magnitude is too small
        curr_magnitude = math.sqrt(x**2 + y**2 + z**2)
        assume(curr_magnitude > 1e-6)

        detumble = BDotDetumble()

        prev_magnetic = magnetic_with_timestamp(x, y, z, 0.0)
        curr_magnetic = magnetic_with_timestamp(x, y, z, dt)

        # This should raise a ValueError due to zero or negative timestamp
        with pytest.raises(ValueError):
            detumble.dipole_moment(curr_magnetic, prev_magnetic)

    @pytest.mark.parametrize(
        "gain, current_mag_field, previous_mag_field, dipole_moment",
        [
            (
                1.0,
                magnetic_with_timestamp(1, 0, 0, 1.0),
                magnetic_with_timestamp(0, 1, 0, 0.0),
                (-1.0, 1.0, 0.0),
            ),
            (
                2.0,
                magnetic_with_timestamp(1, 0, 0, 1.0),
                magnetic_with_timestamp(0, 1, 0, 0.0),
                (-2.0, 2.0, 0.0),
            ),  # Test scaling gain
            (
                1.0,
                magnetic_with_timestamp(3, 0, 0, 1.0),
                magnetic_with_timestamp(0, 3, 0, 0.0),
                (-1.0, 1.0, 0.0),
            ),  # Test scaling magnitude
            (
                1.7,
                magnetic_with_timestamp(-9.5, 8.2, 3.3, 37.0),
                magnetic_with_timestamp(-3, -8.4, 6.1, 0.0),
                (0.0230152290, -0.058777354, 0.009914252),
            ),
        ],
    )
    def test_dipole_moment_formula_verification(
        self, gain, current_mag_field, previous_mag_field, dipole_moment
    ):
        """Test that dipole moment calculation matches the expected formula: m = -k * (dB/dt) / |B|."""
        detumble = BDotDetumble(gain)

        # Calculate the dipole moment
        calculated_dipole = detumble.dipole_moment(
            current_mag_field, previous_mag_field
        )

        # Verify the calculated dipole moment matches the expected values
        assert pytest.approx(calculated_dipole[0], 1e-6) == dipole_moment[0]
        assert pytest.approx(calculated_dipole[1], 1e-6) == dipole_moment[1]
        assert pytest.approx(calculated_dipole[2], 1e-6) == dipole_moment[2]
