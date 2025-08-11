"""This protocol specifies the interface that any magnetorquer implementation must
adhere to, ensuring consistent behavior across different magnetorquer hardware.
"""


class MagnetorquerProto:
    """Protocol defining the interface for magnetorquer control."""

    def set_dipole_moment(self, dipole_moment: tuple[float, float, float]) -> None:
        """Set the magnetic dipole moment for all three axes.

        Args:
            dipole_moment: A tuple containing the dipole moment for each axis (x, y, z) in A⋅m².
        """
        ...
