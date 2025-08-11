"""Detumble attitude control service using B-dot algorithm with magnetorquers."""

import asyncio
import time

from ..logger import Logger
from ..protos.magnetometer import MagnetometerProto
from ..protos.magnetorquer import MagnetorquerProto
from ..sensor_reading.magnetic import Magnetic
from .b_dot_detumble import BDotDetumble


class DetumbleService:
    """Attitude control service implementing B-dot detumble algorithm."""

    previous_mag_field: Magnetic | None = None

    def __init__(
        self,
        logger: Logger,
        magnetometer: MagnetometerProto,
        magnetorquer: MagnetorquerProto,
        control_period: float = 1.0,
    ) -> None:
        """Initialize the detumble service.

        Args:
            logger: Logger instance
            magnetometer: Magnetometer sensor interface
            magnetorquer: Magnetorquer control interface
            control_period: Control loop period in seconds
        """
        self._logger = logger
        self._magnetometer = magnetometer
        self._magnetorquer = magnetorquer
        self._control_period = control_period

    def execute_control_step(self) -> None:
        """Execute one step of the detumble control algorithm."""
        # Get sensor readings
        try:
            magnetic_field = self._magnetometer.get_magnetic_field()
        except Exception:
            raise

        if self.previous_mag_field is None:
            self.previous_mag_field = magnetic_field
            return

        # Calculate required dipole moment using B-dot algorithm
        try:
            dipole_moment = BDotDetumble().dipole_moment(
                current_mag_field=magnetic_field,
                previous_mag_field=self.previous_mag_field,
            )
        except Exception:
            raise
        finally:
            self.previous_mag_field = magnetic_field

        # Apply dipole moment to magnetorquers
        self._magnetorquer.set_dipole_moment(dipole_moment)

    async def run_detumble_loop(self, max_iterations: int = 1000) -> None:
        """Run the detumble control loop for a specified number of iterations.

        Args:
            max_iterations: Maximum number of control iterations
        """
        for i in range(max_iterations):
            start_time = time.monotonic()

            success = self.execute_control_step()
            if not success:
                self._logger.warning(f"Control step {i} failed, continuing...")

            # Maintain control period timing
            elapsed = time.monotonic() - start_time
            if elapsed < self._control_period:
                await asyncio.sleep(self._control_period - elapsed)
