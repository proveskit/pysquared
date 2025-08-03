"""Unit tests for the detumble module.

This module contains unit tests for the `detumble` module, which provides
functions for spacecraft detumbling. The tests cover dot product, cross product,
and magnetorquer dipole calculations.
"""

import pytest

import pysquared.detumble as detumble


def test_dot_product():
    """Tests the dot_product function with positive values."""
    # dot_product is only ever called to give the square of mag_field
    mag_field_vector = (30.0, 45.0, 60.0)
    result = detumble.dot_product(mag_field_vector, mag_field_vector)
    assert result == 6525.0  # 30.0*30.0 + 45.0*45.0 + 60.0*60.0 = 6525.0


def test_dot_product_negatives():
    """Tests the dot_product function with negative vectors."""
    vector1 = (-1, -2, -3)
    vector2 = (-4, -5, -6)
    result = detumble.dot_product(vector1, vector2)
    assert result == 32  # -1*-4 + -2*-5 + -3*-6


def test_dot_product_large_val():
    """Tests the dot_product function with large value vectors."""
    vector1 = (1e6, 1e6, 1e6)
    vector2 = (1e6, 1e6, 1e6)
    result = detumble.dot_product(vector1, vector2)
    assert result == 3e12  # 1e6*1e6 + 1e6*1e6 + 1e6*1e6 = 3e12


def test_dot_product_zero():
    """Tests the dot_product function with zero values."""
    vector = (0.0, 0.0, 0.0)
    result = detumble.dot_product(vector, vector)
    assert result == 0.0


def test_x_product():
    """Tests the x_product (cross product) function."""
    mag_field_vector = (30.0, 45.0, 60.0)
    ang_vel_vector = (0.0, 0.02, 0.015)
    expected_result = [-0.525, 0.45, 0.6]
    # x_product takes in tuple arguments and returns a list value
    actual_result = detumble.x_product(
        mag_field_vector, ang_vel_vector
    )  # cross product
    assert pytest.approx(actual_result[0], 0.001) == expected_result[0]
    assert pytest.approx(actual_result[1], 0.001) == expected_result[1]
    assert pytest.approx(actual_result[2], 0.001) == expected_result[2]
    # due to floating point arithmetic, accept answer within 5 places


def test_x_product_negatives():
    """Tests the x_product function with negative values."""
    mag_field_vector = (-30.0, -45.0, -60.0)
    ang_vel_vector = (-0.02, -0.02, -0.015)
    expected_result = [-0.525, -0.75, -0.3]
    actual_result = detumble.x_product(mag_field_vector, ang_vel_vector)
    assert pytest.approx(actual_result[0], 0.001) == expected_result[0]
    assert pytest.approx(actual_result[1], 0.001) == expected_result[1]
    assert pytest.approx(actual_result[2], 0.001) == expected_result[2]


def test_x_product_large_val():
    """Tests the x_product function with large values."""
    mag_field_vector = (1e6, 1e6, 1e6)
    ang_vel_vector = (1e6, 1e6, 1e6)  # cross product of parallel vector equals 0
    result = detumble.x_product(mag_field_vector, ang_vel_vector)
    assert result == [0.0, 0.0, 0.0]


def test_x_product_zero():
    """Tests the x_product function with zero values."""
    mag_field_vector = (0.0, 0.0, 0.0)
    ang_vel_vector = (0.0, 0.02, 0.015)
    result = detumble.x_product(mag_field_vector, ang_vel_vector)
    assert result == [0.0, 0.0, 0.0]


# Bigger context: magnetorquer_dipole() is called by do_detumble() in (FC board) functions.py & (Batt Board) battery_functions.py
# mag_field: mag. field strength at x, y, & z axis (tuple) (magnetometer reading)
# ang_vel: ang. vel. at x, y, z axis (tuple) (angular_velocityscope reading)
def test_magnetorquer_dipole():
    """Tests the magnetorquer_dipole function with valid inputs."""
    mag_field = (30.0, -45.0, 60.0)
    ang_vel = (0.0, 0.02, 0.015)
    expected_result = [0.023211, -0.00557, -0.007426]
    actual_result = detumble.magnetorquer_dipole(mag_field, ang_vel)
    assert pytest.approx(actual_result[0], 0.001) == expected_result[0]
    assert pytest.approx(actual_result[1], 0.001) == expected_result[1]
    assert pytest.approx(actual_result[2], 0.001) == expected_result[2]


def test_magnetorquer_dipole_zero_mag_field():
    """Tests magnetorquer_dipole with a zero magnetic field, expecting ZeroDivisionError."""
    mag_field = (0.0, 0.0, 0.0)
    ang_vel = (0.0, 0.02, 0.015)
    with pytest.raises(ZeroDivisionError):
        detumble.magnetorquer_dipole(mag_field, ang_vel)


def test_magnetorquer_dipole_zero_ang_vel():
    """Tests magnetorquer_dipole with zero angular velocity."""
    mag_field = (30.0, -45.0, 60.0)
    ang_vel = (0.0, 0.0, 0.0)
    result = detumble.magnetorquer_dipole(mag_field, ang_vel)
    assert result == [0.0, 0.0, 0.0]
