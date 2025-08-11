"""This file provides functions for detumbling the satellite using the B-dot algorithm.

Coding style for this file foregoes more complex programming constructs in favor readability.
We assume that non-programmers may read this code to understand and validate detumbling logic.

Units and concepts used in this file:
- B-dot detumbling algorithm
    - https://en.wikipedia.org/wiki/Spacecraft_detumbling#Magnetic_control:_B-dot
- Magnetic field (B-field) strength in micro-Tesla (uT)
    - https://en.wikipedia.org/wiki/Magnetic_field
    - https://en.wikipedia.org/wiki/Tesla_(unit)
- Dipole moment in Ampere-square meter (A⋅m²)
    - https://en.wikipedia.org/wiki/Magnetic_dipole
    - https://en.wikipedia.org/wiki/Ampere
    - https://en.wikipedia.org/wiki/Square_metre
"""

import math

from ..sensor_reading.magnetic import Magnetic


class BDotDetumble:
    """B-dot detumbling for attitude control.

    Example usage:
    ```python
        b_dot_detumble = BDotDetumble(gain=1.0)
        current_mag_field = Magnetic(value=(0.1, 0.2, 0.3), timestamp=1234567890)
        previous_mag_field = Magnetic(value=(0.1, 0.2, 0.3), timestamp=1234567880)
        dipole_moment = b_dot_detumble.dipole_moment(current_mag_field, previous_mag_field)
        print(dipole_moment)
    ```
    """

    def __init__(self, gain: float = 1.0):
        """Initializes the BDotDetumble class.

        Args:
            gain: Gain constant for the B-dot detumbling algorithm.

        TODO(nateinaction): Create system for teams to set values that compute gain for them.
        """
        self._gain = gain

    @staticmethod
    def _magnitude(current_mag_field: Magnetic) -> float:
        """
        Computes the magnitude of the magnetic field vector.

        Args:
            current_mag_field: Magnetic object containing the current magnetic field vector.

        Returns:
            The magnitude of the magnetic field vector.
        """
        return math.sqrt(
            current_mag_field.value[0] ** 2
            + current_mag_field.value[1] ** 2
            + current_mag_field.value[2] ** 2
        )

    @staticmethod
    def _dB_dt(
        current_mag_field: Magnetic, previous_mag_field: Magnetic
    ) -> tuple[float, float, float]:
        """
        Computes the time derivative of the magnetic field vector.

        Args:
            current_mag_field: Magnetic object containing the current magnetic field vector
            previous_mag_field: Magnetic object containing the previous magnetic field vector

        Returns:
            dB_dt: tuple of dB/dt (dBx/dt, dBy/dt, dBz/dt) in micro-Tesla per second (uT/s).

        Raises:
            ValueError: If the time difference between the current and previous magnetic field readings is too small to compute dB/dt.
        """
        dt = current_mag_field.timestamp - previous_mag_field.timestamp
        if dt < 1e-6:
            raise ValueError(
                "Timestamp difference between current and previous magnetic field readings is too small to compute dB/dt."
            )

        dBx_dt = (current_mag_field.value[0] - previous_mag_field.value[0]) / dt
        dBy_dt = (current_mag_field.value[1] - previous_mag_field.value[1]) / dt
        dBz_dt = (current_mag_field.value[2] - previous_mag_field.value[2]) / dt
        return (dBx_dt, dBy_dt, dBz_dt)

    def dipole_moment(
        self, current_mag_field: Magnetic, previous_mag_field: Magnetic
    ) -> tuple[float, float, float]:
        """
        Computes the required dipole moment to detumble the satellite.

        m = -k * (dB/dt) / |B|

        m is the dipole moment in A⋅m²
        k is a gain constant
        dB/dt is the time derivative of the magnetic field reading in micro-Tesla per second (uT/s)
        |B| is the magnitude of the magnetic field vector in micro-Tesla (uT)

        Args:
            current_mag_field: Magnetic object containing the current magnetic field vector.
            previous_mag_field: Magnetic object containing the previous magnetic field vector.

        Returns:
            The dipole moment in A⋅m² as a tuple (moment_x, moment_y, moment_z).

        Raises:
            ValueError: If the magnitude of the current magnetic field is too small to compute the dipole moment.
                or if the time difference between the current and previous magnetic field readings is less than or equal to 0.
        """
        magnitude = self._magnitude(current_mag_field)
        if magnitude < 1e-6:
            raise ValueError(
                "Current magnetic field magnitude is too small to compute dipole moment."
            )

        if current_mag_field.timestamp <= previous_mag_field.timestamp:
            raise ValueError(
                "Current magnetic field timestamp must be greater than previous magnetic field timestamp."
            )

        try:
            dBx_dt, dBy_dt, dBz_dt = self._dB_dt(current_mag_field, previous_mag_field)
        except ValueError:
            raise

        moment_x = -self._gain * dBx_dt / magnitude
        moment_y = -self._gain * dBy_dt / magnitude
        moment_z = -self._gain * dBz_dt / magnitude
        return (moment_x, moment_y, moment_z)
