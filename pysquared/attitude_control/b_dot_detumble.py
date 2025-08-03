"""This file provides functions for detumbling the satellite using the B-dot algorithm."""

import math

from ..sensor_reading.magnetic import Magnetic


class BDotDetumble:
    """B-dot detumbling for attitude control."""

    def __init__(self, gain: float = 1.0):
        """Initializes the BDotDetumble class.

        Args:
            gain: Gain constant for the B-dot detumbling algorithm.
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
            dB_dt: tuple of dB/dt (dBx/dt, dBy/dt, dBz/dt)

        Raises:
            ValueError: If the time difference between the current and previous magnetic field readings is too small to compute dB/dt.
        """
        dt = current_mag_field.timestamp - previous_mag_field.timestamp
        if dt < 1e-6:
            raise ValueError(
                "Timestamp difference between current and previous magnetic field readings is too small to compute dB/dt."
            )

        Bx_dt = (current_mag_field.value[0] - previous_mag_field.value[0]) / dt
        By_dt = (current_mag_field.value[1] - previous_mag_field.value[1]) / dt
        Bz_dt = (current_mag_field.value[2] - previous_mag_field.value[2]) / dt
        return (Bx_dt, By_dt, Bz_dt)

    def dipole_moment(
        self, current_mag_field: Magnetic, previous_mag_field: Magnetic
    ) -> tuple[float, float, float]:
        """
        Computes the required dipole moment to detumble the satellite.

        m = -k * (dB/dt) / |B|

        m is the dipole moment
        k is a gain constant
        dB/dt is the time derivative of the magnetic field reading
        |B| is the magnitude of the magnetic field vector

        Args:
            current_mag_field: Magnetic object containing the current magnetic field vector.
            previous_mag_field: Magnetic object containing the previous magnetic field vector.

        Returns:
            The dipole moment vector to be applied.

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
            Bx_dt, By_dt, Bz_dt = self._dB_dt(current_mag_field, previous_mag_field)
        except ValueError:
            raise

        moment_x = -self._gain * Bx_dt / magnitude
        moment_y = -self._gain * By_dt / magnitude
        moment_z = -self._gain * Bz_dt / magnitude
        return (moment_x, moment_y, moment_z)
