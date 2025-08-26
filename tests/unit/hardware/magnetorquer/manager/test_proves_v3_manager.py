"""Unit tests for the ProvesV3Manager class.

This module contains unit tests for the `ProvesV3Manager` class, which is responsible for
controlling magnetorquers on the Proves V3 hardware. The tests cover initialization,
dipole moment calculations, current limiting, and the magnetorquer protocol interface.
"""

import math
from unittest.mock import patch

import pytest

from pysquared.hardware.magnetorquer.manager.proves_v3_manager import ProvesV3Manager
from pysquared.protos.magnetorquer import MagnetorquerProto


class TestProvesV3Manager:
    """Test suite for the ProvesV3Manager class."""

    @pytest.fixture
    def manager(self) -> ProvesV3Manager:
        """Create a ProvesV3Manager instance for testing."""
        return ProvesV3Manager()

    def test_initialization(self, manager: ProvesV3Manager) -> None:
        """Test that the manager initializes correctly."""
        assert isinstance(manager, ProvesV3Manager)
        assert isinstance(manager, MagnetorquerProto)

    def test_class_constants(self) -> None:
        """Test that all class constants are set correctly."""
        # Coil voltage
        assert ProvesV3Manager._coil_voltage == 3.3

        # X and Y axis constants
        assert ProvesV3Manager._coil_num_turns_x_y == 2 * 24
        assert ProvesV3Manager._coil_length_x_y == 0.053
        assert ProvesV3Manager._coil_width_x_y == 0.045
        assert ProvesV3Manager._coil_area_x_y == 0.053 * 0.045
        assert ProvesV3Manager._coil_resistance_x_y == 57.2
        assert ProvesV3Manager._coil_max_current_x_y == 3.3 / 57.2

        # Z axis constants
        assert ProvesV3Manager._coil_num_turns_z == 3 * 51
        assert ProvesV3Manager._coil_diameter_z == 0.05755
        expected_area_z = math.pi * (0.05755 / 2) ** 2
        assert abs(ProvesV3Manager._coil_area_z - expected_area_z) < 1e-10
        assert ProvesV3Manager._coil_resistance_z == 248.8
        assert ProvesV3Manager._coil_max_current_z == 3.3 / 248.8

    def test_current_from_dipole_moment_zero(self, manager: ProvesV3Manager) -> None:
        """Test current calculation with zero dipole moment."""
        dipole_moment = (0.0, 0.0, 0.0)
        current = manager._current_from_dipole_moment(dipole_moment)

        assert current == (0.0, 0.0, 0.0)

    def test_current_from_dipole_moment_positive(
        self, manager: ProvesV3Manager
    ) -> None:
        """Test current calculation with positive dipole moments."""
        dipole_moment = (1.0, 2.0, 3.0)
        current = manager._current_from_dipole_moment(dipole_moment)

        # Calculate expected values
        expected_x = 1.0 / (
            ProvesV3Manager._coil_num_turns_x_y * ProvesV3Manager._coil_area_x_y
        )
        expected_y = 2.0 / (
            ProvesV3Manager._coil_num_turns_x_y * ProvesV3Manager._coil_area_x_y
        )
        expected_z = 3.0 / (
            ProvesV3Manager._coil_num_turns_z * ProvesV3Manager._coil_area_z
        )

        assert abs(current[0] - expected_x) < 1e-10
        assert abs(current[1] - expected_y) < 1e-10
        assert abs(current[2] - expected_z) < 1e-10

    def test_current_from_dipole_moment_negative(
        self, manager: ProvesV3Manager
    ) -> None:
        """Test current calculation with negative dipole moments."""
        dipole_moment = (-1.0, -2.0, -3.0)
        current = manager._current_from_dipole_moment(dipole_moment)

        # Calculate expected values
        expected_x = -1.0 / (
            ProvesV3Manager._coil_num_turns_x_y * ProvesV3Manager._coil_area_x_y
        )
        expected_y = -2.0 / (
            ProvesV3Manager._coil_num_turns_x_y * ProvesV3Manager._coil_area_x_y
        )
        expected_z = -3.0 / (
            ProvesV3Manager._coil_num_turns_z * ProvesV3Manager._coil_area_z
        )

        assert abs(current[0] - expected_x) < 1e-10
        assert abs(current[1] - expected_y) < 1e-10
        assert abs(current[2] - expected_z) < 1e-10

    def test_current_from_dipole_moment_mixed(self, manager: ProvesV3Manager) -> None:
        """Test current calculation with mixed positive and negative dipole moments."""
        dipole_moment = (1.5, -2.5, 0.8)
        current = manager._current_from_dipole_moment(dipole_moment)

        # Calculate expected values
        expected_x = 1.5 / (
            ProvesV3Manager._coil_num_turns_x_y * ProvesV3Manager._coil_area_x_y
        )
        expected_y = -2.5 / (
            ProvesV3Manager._coil_num_turns_x_y * ProvesV3Manager._coil_area_x_y
        )
        expected_z = 0.8 / (
            ProvesV3Manager._coil_num_turns_z * ProvesV3Manager._coil_area_z
        )

        assert abs(current[0] - expected_x) < 1e-10
        assert abs(current[1] - expected_y) < 1e-10
        assert abs(current[2] - expected_z) < 1e-10

    def test_limit_current_within_limits(self, manager: ProvesV3Manager) -> None:
        """Test current limiting when currents are within limits."""
        # Use small currents that are well within the limits
        current = (0.01, -0.02, 0.005)
        limited = manager._limit_current(current)

        # Should return the same values since they're within limits
        assert limited == current

    def test_limit_current_exceeds_x_axis_positive(
        self, manager: ProvesV3Manager
    ) -> None:
        """Test current limiting when x-axis current exceeds positive limit."""
        max_current_x_y = ProvesV3Manager._coil_max_current_x_y
        current = (max_current_x_y + 0.1, 0.01, 0.005)
        limited = manager._limit_current(current)

        assert limited[0] == max_current_x_y  # Limited to max
        assert limited[1] == 0.01  # Unchanged
        assert limited[2] == 0.005  # Unchanged

    def test_limit_current_exceeds_x_axis_negative(
        self, manager: ProvesV3Manager
    ) -> None:
        """Test current limiting when x-axis current exceeds negative limit."""
        max_current_x_y = ProvesV3Manager._coil_max_current_x_y
        current = (-(max_current_x_y + 0.1), 0.01, 0.005)
        limited = manager._limit_current(current)

        assert limited[0] == -max_current_x_y  # Limited to -max
        assert limited[1] == 0.01  # Unchanged
        assert limited[2] == 0.005  # Unchanged

    def test_limit_current_exceeds_y_axis_positive(
        self, manager: ProvesV3Manager
    ) -> None:
        """Test current limiting when y-axis current exceeds positive limit."""
        max_current_x_y = ProvesV3Manager._coil_max_current_x_y
        current = (0.01, max_current_x_y + 0.1, 0.005)
        limited = manager._limit_current(current)

        assert limited[0] == 0.01  # Unchanged
        assert limited[1] == max_current_x_y  # Limited to max
        assert limited[2] == 0.005  # Unchanged

    def test_limit_current_exceeds_y_axis_negative(
        self, manager: ProvesV3Manager
    ) -> None:
        """Test current limiting when y-axis current exceeds negative limit."""
        max_current_x_y = ProvesV3Manager._coil_max_current_x_y
        current = (0.01, -(max_current_x_y + 0.1), 0.005)
        limited = manager._limit_current(current)

        assert limited[0] == 0.01  # Unchanged
        assert limited[1] == -max_current_x_y  # Limited to -max
        assert limited[2] == 0.005  # Unchanged

    def test_limit_current_exceeds_z_axis_positive(
        self, manager: ProvesV3Manager
    ) -> None:
        """Test current limiting when z-axis current exceeds positive limit."""
        max_current_z = ProvesV3Manager._coil_max_current_z
        current = (0.01, 0.02, max_current_z + 0.1)
        limited = manager._limit_current(current)

        assert limited[0] == 0.01  # Unchanged
        assert limited[1] == 0.02  # Unchanged
        assert limited[2] == max_current_z  # Limited to max

    def test_limit_current_exceeds_z_axis_negative(
        self, manager: ProvesV3Manager
    ) -> None:
        """Test current limiting when z-axis current exceeds negative limit."""
        max_current_z = ProvesV3Manager._coil_max_current_z
        current = (0.01, 0.02, -(max_current_z + 0.1))
        limited = manager._limit_current(current)

        assert limited[0] == 0.01  # Unchanged
        assert limited[1] == 0.02  # Unchanged
        assert limited[2] == -max_current_z  # Limited to -max

    def test_limit_current_all_axes_exceed(self, manager: ProvesV3Manager) -> None:
        """Test current limiting when all axes exceed their limits."""
        max_current_x_y = ProvesV3Manager._coil_max_current_x_y
        max_current_z = ProvesV3Manager._coil_max_current_z

        current = (max_current_x_y + 0.1, -(max_current_x_y + 0.2), max_current_z + 0.3)
        limited = manager._limit_current(current)

        assert limited[0] == max_current_x_y
        assert limited[1] == -max_current_x_y
        assert limited[2] == max_current_z

    def test_limit_current_zero_currents(self, manager: ProvesV3Manager) -> None:
        """Test current limiting with zero currents."""
        current = (0.0, 0.0, 0.0)
        limited = manager._limit_current(current)

        assert limited == (0.0, 0.0, 0.0)

    def test_limit_current_exactly_at_limits(self, manager: ProvesV3Manager) -> None:
        """Test current limiting when currents are exactly at the limits."""
        max_current_x_y = ProvesV3Manager._coil_max_current_x_y
        max_current_z = ProvesV3Manager._coil_max_current_z

        current = (max_current_x_y, -max_current_x_y, max_current_z)
        limited = manager._limit_current(current)

        # Should return the same values since they're exactly at the limits
        assert limited == current

    def test_set_dipole_moment_calls_helper_methods(
        self, manager: ProvesV3Manager
    ) -> None:
        """Test that set_dipole_moment calls the correct helper methods."""
        dipole_moment = (1.0, 2.0, 3.0)

        with (
            patch.object(manager, "_current_from_dipole_moment") as mock_current_calc,
            patch.object(manager, "_limit_current") as mock_limit,
        ):
            # Set up return values
            calculated_current = (0.1, 0.2, 0.05)
            limited_current = (0.08, 0.15, 0.04)
            mock_current_calc.return_value = calculated_current
            mock_limit.return_value = limited_current

            manager.set_dipole_moment(dipole_moment)

            # Verify methods were called with correct arguments
            mock_current_calc.assert_called_once_with(dipole_moment)
            mock_limit.assert_called_once_with(calculated_current)

    def test_set_dipole_moment_integration(self, manager: ProvesV3Manager) -> None:
        """Test set_dipole_moment with actual calculations (integration test)."""
        # This test verifies the complete flow without mocking
        dipole_moment = (0.001, -0.002, 0.0005)

        # This should not raise any exceptions
        manager.set_dipole_moment(dipole_moment)

    def test_set_dipole_moment_large_values(self, manager: ProvesV3Manager) -> None:
        """Test set_dipole_moment with large dipole moment values."""
        # Large values that would exceed current limits
        dipole_moment = (100.0, -150.0, 50.0)

        # This should not raise any exceptions (current limiting should handle it)
        manager.set_dipole_moment(dipole_moment)

    def test_magnetorquer_configuration_comments(self) -> None:
        """Test that the magnetorquer configuration is documented correctly in comments."""
        # This test verifies the physical configuration described in the code comments

        # X and Y axis: 2 layers of 24 turns each
        assert ProvesV3Manager._coil_num_turns_x_y == 48

        # Z axis: 3 layers of 51 turns each
        assert ProvesV3Manager._coil_num_turns_z == 153

    def test_mathematical_relationships(self) -> None:
        """Test that mathematical relationships between constants are correct."""
        # Test that area calculations are correct
        expected_area_x_y = (
            ProvesV3Manager._coil_length_x_y * ProvesV3Manager._coil_width_x_y
        )
        assert ProvesV3Manager._coil_area_x_y == expected_area_x_y

        expected_area_z = math.pi * (ProvesV3Manager._coil_diameter_z / 2) ** 2
        assert abs(ProvesV3Manager._coil_area_z - expected_area_z) < 1e-10

        # Test that max current calculations are correct
        expected_max_current_x_y = (
            ProvesV3Manager._coil_voltage / ProvesV3Manager._coil_resistance_x_y
        )
        assert (
            abs(ProvesV3Manager._coil_max_current_x_y - expected_max_current_x_y)
            < 1e-10
        )

        expected_max_current_z = (
            ProvesV3Manager._coil_voltage / ProvesV3Manager._coil_resistance_z
        )
        assert abs(ProvesV3Manager._coil_max_current_z - expected_max_current_z) < 1e-10

    def test_edge_case_very_small_dipole_moments(
        self, manager: ProvesV3Manager
    ) -> None:
        """Test with very small dipole moment values."""
        dipole_moment = (1e-10, -1e-10, 1e-10)
        current = manager._current_from_dipole_moment(dipole_moment)
        limited = manager._limit_current(current)

        # Should handle very small values without issues
        assert all(abs(c) < 1e-5 for c in current)
        assert limited == current  # Should not be limited

    def test_edge_case_very_large_dipole_moments(
        self, manager: ProvesV3Manager
    ) -> None:
        """Test with very large dipole moment values."""
        dipole_moment = (1e6, -1e6, 1e6)
        current = manager._current_from_dipole_moment(dipole_moment)
        limited = manager._limit_current(current)

        # Current should be very large
        assert all(abs(c) > 1e3 for c in current)

        # But limited current should be within bounds
        max_x_y = ProvesV3Manager._coil_max_current_x_y
        max_z = ProvesV3Manager._coil_max_current_z

        assert abs(limited[0]) <= max_x_y
        assert abs(limited[1]) <= max_x_y
        assert abs(limited[2]) <= max_z

    @pytest.mark.parametrize(
        "dipole_x,dipole_y,dipole_z",
        [
            (1.0, 0.0, 0.0),  # X-axis only
            (0.0, 1.0, 0.0),  # Y-axis only
            (0.0, 0.0, 1.0),  # Z-axis only
            (1.0, 1.0, 1.0),  # All axes equal
            (-1.0, -1.0, -1.0),  # All axes equal negative
        ],
    )
    def test_dipole_moment_parametrized(
        self,
        manager: ProvesV3Manager,
        dipole_x: float,
        dipole_y: float,
        dipole_z: float,
    ) -> None:
        """Test dipole moment calculations with various parameter combinations."""
        dipole_moment = (dipole_x, dipole_y, dipole_z)

        # Should not raise any exceptions
        current = manager._current_from_dipole_moment(dipole_moment)
        limited = manager._limit_current(current)
        manager.set_dipole_moment(dipole_moment)

        # Basic sanity checks
        assert len(current) == 3
        assert len(limited) == 3

        # Check that signs are preserved when within limits
        if abs(current[0]) <= ProvesV3Manager._coil_max_current_x_y:
            assert (current[0] >= 0) == (limited[0] >= 0)
        if abs(current[1]) <= ProvesV3Manager._coil_max_current_x_y:
            assert (current[1] >= 0) == (limited[1] >= 0)
        if abs(current[2]) <= ProvesV3Manager._coil_max_current_z:
            assert (current[2] >= 0) == (limited[2] >= 0)
