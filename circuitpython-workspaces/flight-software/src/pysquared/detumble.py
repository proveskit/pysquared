"""This module provides functions for satellite detumbling using magnetorquers.
Includes vector math utilities and the main dipole calculation for attitude control.
"""


def dot_product(vector1: tuple, vector2: tuple) -> float:
    """
    Computes the dot product of two 3-element vectors.

    Args:
        vector1 (tuple): First vector (length 3).
        vector2 (tuple): Second vector (length 3).

    Returns:
        float: The dot product of the two vectors.
    """
    return sum([a * b for a, b in zip(vector1, vector2)])


def x_product(vector1: tuple, vector2: tuple) -> list:
    """
    Computes the cross product of two 3-element vectors.

    Args:
        vector1 (tuple): First vector (length 3).
        vector2 (tuple): Second vector (length 3).

    Returns:
        list: The cross product vector (length 3).
    """
    return [
        vector1[1] * vector2[2] - vector1[2] * vector2[1],
        vector1[0] * vector2[2] - vector1[2] * vector2[0],
        vector1[0] * vector2[1] - vector1[1] * vector2[0],
    ]


def gain_func() -> float:
    """
    Returns the gain value for the detumble control law.

    Returns:
        float: Gain value (default 1.0).
    """
    return 1.0


def magnetorquer_dipole(mag_field: tuple, ang_vel: tuple) -> list:
    """
    Calculates the required dipole moment for the magnetorquers to detumble the satellite.

    Args:
        mag_field (tuple): The measured magnetic field vector (length 3).
        ang_vel (tuple): The measured angular velocity vector (length 3).

    Returns:
        list: The dipole moment vector to be applied (length 3).
    """
    gain = gain_func()
    scalar_coef = -gain / pow(dot_product(mag_field, mag_field), 0.5)
    dipole_out = x_product(mag_field, ang_vel)
    for i in range(3):
        dipole_out[i] *= scalar_coef
    return dipole_out
