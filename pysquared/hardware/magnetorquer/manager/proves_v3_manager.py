"""This module implements the Proves V3 magnetorquer manager.
It provides an interface for controlling the magnetorquers on the Proves V3 hardware.
It inherits from the MagnetorquerProto protocol to ensure it implements the required methods.

Coding style for this file foregoes more complex programming constructs in favor readability.
We assume that non-programmers may read this code to understand and validate detumbling logic.
"""

import math

from ....protos.magnetorquer import MagnetorquerProto


class ProvesV3Manager(MagnetorquerProto):
    """Manager for Proves V3 hardware components."""

    _coil_voltage = 3.3
    """Voltage supplied to the magnetorquers in Volts."""

    _coil_num_turns_x_y = 2 * 24
    """Number of turns in the x and y-axis magnetorquer coil.
    The x and y magenetorquer coil consists of 2 layers of 24 turns each.
    """

    _coil_length_x_y = 0.053
    """Length of the x and y-axis coil in meters."""

    _coil_width_x_y = 0.045
    """Width of the x and y-axis coil in meters."""

    _coil_area_x_y = _coil_length_x_y * _coil_width_x_y

    _coil_resistance_x_y = 57.2
    """Resistance of the x and y-axis coil in ohms."""

    _coil_max_current_x_y = _coil_voltage / _coil_resistance_x_y
    """Maximum current for the x and y-axis magnetorquers in Amperes."""

    _coil_num_turns_z = 3 * 51
    """Number of turns in the z-axis magnetorquer coil.
    The z magenetorquer coil consists of 3 layers of 51 turns each.
    """

    _coil_diameter_z = 0.05755
    """Diameter of the z-axis coil in meters."""

    _coil_area_z = math.pi * (_coil_diameter_z / 2) ** 2
    """Area of the z-axis coil in square meters."""

    _coil_resistance_z = 248.8
    """Resistance of the z-axis coil in ohms."""

    _coil_max_current_z = _coil_voltage / _coil_resistance_z
    """Maximum current for the z-axis magnetorquer in Amperes."""

    def __init__(self) -> None:
        """Initializes the Proves V3 Manager."""
        pass

    def set_dipole_moment(self, dipole_moment: tuple[float, float, float]) -> None:
        """Set the magnetic dipole moment for all three axes.

        Args:
            dipole_moment: A tuple containing the dipole moment for each axis (x, y, z) in A⋅m².
        """
        # Convert dipole moment to current for each axis.
        current = self._current_from_dipole_moment(dipole_moment)

        # Limit the current to the maximum allowed current.
        limited_current = self._limit_current(current)

        # On Proves V3 we have 2 x-axis, 2 y-axis, and 1 z-axis magnetorquers.
        # To not cancel out the x and y components we reverse the current for one of each.
        _ = limited_current[0]  # x1
        _ = -limited_current[0]  # x2
        _ = limited_current[1]  # y1
        _ = -limited_current[1]  # y2
        _ = limited_current[2]  # z1

        # TODO(nateinaction): Set the current for each magnetorquer

    def _limit_current(
        self, current: tuple[float, float, float]
    ) -> tuple[float, float, float]:
        """Limits the current for each axis to max_current.

        TODO(nateinaction): Michael said that we may want to output a percentage of max current instead of the actual current.

        Args:
            current: A tuple containing the current for each axis (x, y, z) in Amperes.

        Returns:
            A tuple containing the limited current for each axis.
        """
        return (
            min(abs(current[0]), self._coil_max_current_x_y)
            * (1 if current[0] >= 0 else -1),
            min(abs(current[1]), self._coil_max_current_x_y)
            * (1 if current[1] >= 0 else -1),
            min(abs(current[2]), self._coil_max_current_z)
            * (1 if current[2] >= 0 else -1),
        )

    def _current_from_dipole_moment(
        self, dipole_moment: tuple[float, float, float]
    ) -> tuple[float, float, float]:
        """
        Converts the dipole moment to current for each axis.

        I = m / (N * A)

        I is the coil current in A
        m is magnetic dipole moment in A·m²
        N is the number of turns of the coil
        A is the area of one turn of the coil in m²

        Args:
            dipole_moment: A tuple containing the dipole moment for each axis (x, y, z) in A⋅m².

        Returns:
            A tuple containing the current for each axis (current_x, current_y, current_z) in Amperes.
        """
        current_x = dipole_moment[0] / (self._coil_num_turns_x_y * self._coil_area_x_y)
        current_y = dipole_moment[1] / (self._coil_num_turns_x_y * self._coil_area_x_y)
        current_z = dipole_moment[2] / (self._coil_num_turns_z * self._coil_area_z)
        return (current_x, current_y, current_z)
