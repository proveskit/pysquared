"""This file provides functions for detumbling the satellite using the b-dot algorithm."""

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
    def _magnitude(B_now: Magnetic) -> float:
        """
        Computes the magnitude of the magnetic field vector.

        Args:
            B_now: Magnetic object containing the current magnetic field vector.

        Returns:
            The magnitude of the magnetic field vector.
        """
        return pow(B_now.value[0] ** 2 + B_now.value[1] ** 2 + B_now.value[2] ** 2, 0.5)

    @staticmethod
    def _dB_dt(B_now: Magnetic, B_prev: Magnetic) -> tuple[float, float, float]:
        """
        Computes the time derivative of the magnetic field vector.

        Args:
            B_now: Magnetic object containing the current magnetic field vector
            B_prev: Magnetic object containing the previous magnetic field vector
            dt: time difference between measurements (in seconds)

        Returns:
            dB_dt: tuple of dB/dt (dBx/dt, dBy/dt, dBz/dt)
        """
        dt = B_now.timestamp - B_prev.timestamp
        Bx_dt = (B_now.value[0] - B_prev.value[0]) / dt
        By_dt = (B_now.value[1] - B_prev.value[1]) / dt
        Bz_dt = (B_now.value[2] - B_prev.value[2]) / dt
        return (Bx_dt, By_dt, Bz_dt)

    def dipole_moment(
        self, current_mag_field: Magnetic, previous_mag_field: Magnetic
    ) -> tuple[float, float, float]:
        """
        Calculates the required dipole moment to detumble the satellite.

        m = -k * (dB/dt) / |B|

        m is the dipole moment
        k is a gain constant
        dB/dt is the time derivative of the magnetic field reading
        |B| is the magnitude of the magnetic field vector

        Args:
            mag_field (tuple): The measured magnetic field vector (length 3).
            ang_vel (tuple): The measured angular velocity vector (length 3).

        Returns:
            list: The dipole moment vector to be applied (length 3).
        """
        scalar_coef = -self._gain / self._magnitude(current_mag_field)
        dB_dt = self._dB_dt(current_mag_field, previous_mag_field)
        return (scalar_coef * dB_dt[0], scalar_coef * dB_dt[1], scalar_coef * dB_dt[2])
