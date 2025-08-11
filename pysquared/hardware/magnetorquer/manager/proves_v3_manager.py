"""This module implements the Proves V3 magnetorquer manager.
It provides an interface for controlling the magnetorquers on the Proves V3 hardware.
It inherits from the MagnetorquerProto protocol to ensure it implements the required methods.

Coding style for this file foregoes more complex programming constructs in favor readability.
We assume that non-programmers may read this code to understand and validate detumbling logic.
"""

from ....protos.magnetorquer import MagnetorquerProto


class ProvesV3Manager(MagnetorquerProto):
    """Manager for Proves V3 hardware components."""

    num_coil_turns = 100  # TODO(nateinaction): Set this to the actual number of turns in the magnetorquer coil.
    """Number of turns in the magnetorquer coil."""

    coil_area = 0.01  # TODO(nateinaction): Set this to the actual area of one turn of the coil in square meters.
    """Area of one turn of the coil in m²."""

    max_current: float = 1.0  # TODO(nateinaction): Set this to the actual maximum current for the magnetorquers in Amperes.
    """Maximum current for the magnetorquers in Amperes."""

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
            min(abs(current[0]), self.max_current) * (1 if current[0] >= 0 else -1),
            min(abs(current[1]), self.max_current) * (1 if current[1] >= 0 else -1),
            min(abs(current[2]), self.max_current) * (1 if current[2] >= 0 else -1),
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
        current_x = dipole_moment[0] / (self.num_coil_turns * self.coil_area)
        current_y = dipole_moment[1] / (self.num_coil_turns * self.coil_area)
        current_z = dipole_moment[2] / (self.num_coil_turns * self.coil_area)
        return (current_x, current_y, current_z)
