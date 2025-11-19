"""This module defines the `ProvesMagnetorquerManager` class, which provides a high-level interface
for controlling the PROVES V3 magnetorquer coils using DRV2605L haptic motor drivers.
The system uses 5 DRV2605L chips to control embedded PCB magnetorquer coils on the
X+, X-, Y+, Y-, and Z- faces of the CubeSat.

**Usage:**
```python
logger = Logger()
i2c = busio.I2C(board.SCL, board.SDA)
magnetorquer = ProvesMagnetorquerManager(
    logger,
    i2c,
    addr_x_plus=0x5A,
    addr_x_minus=0x5B,
    addr_y_plus=0x5C,
    addr_y_minus=0x5D,
    addr_z_minus=0x5E
)
# Set dipole moment in A⋅m² for each axis
magnetorquer.set_dipole_moment((0.001, 0.0, -0.001))
```
"""

import math

from adafruit_drv2605 import DRV2605, MODE_REALTIME
from busio import I2C

from ....logger import Logger
from ....protos.magnetorquer import MagnetorquerProto
from ...exception import HardwareInitializationError


class ProvesMagnetorquerManager(MagnetorquerProto):
    """Manager for PROVES V3 magnetorquer hardware using DRV2605L drivers.

    This manager controls 5 DRV2605L haptic motor drivers that actuate embedded
    PCB magnetorquer coils. The coils are arranged on different faces of the CubeSat:
    X+ and X- faces (rectangular coils), Y+ and Y- faces (rectangular coils),
    and Z- face (circular coil).
    """

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
    """Area of the x and y-axis coil in square meters."""

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

    def __init__(
        self,
        logger: Logger,
        i2c: I2C,
        addr_x_plus: int = 0x5A,  # TODO: FIX THIS ADDRESS
        addr_x_minus: int = 0x5B,  # TODO: FIX THIS ADDRESS
        addr_y_plus: int = 0x5C,  # TODO: FIX THIS ADDRESS
        addr_y_minus: int = 0x5D,  # TODO: FIX THIS ADDRESS
        addr_z_minus: int = 0x5E,  # TODO: FIX THIS ADDRESS
    ) -> None:
        """Initializes the ProvesMagnetorquerManager.

        Args:
            logger: The logger to use.
            i2c: The I2C bus connected to the DRV2605 chips.
            addr_x_plus: I2C address for the X+ face magnetorquer driver.
            addr_x_minus: I2C address for the X- face magnetorquer driver.
            addr_y_plus: I2C address for the Y+ face magnetorquer driver.
            addr_y_minus: I2C address for the Y- face magnetorquer driver.
            addr_z_minus: I2C address for the Z- face magnetorquer driver.

        Raises:
            HardwareInitializationError: If any DRV2605 chip fails to initialize.
        """
        self._log: Logger = logger

        try:
            self._log.debug("Initializing magnetorquer DRV2605 drivers")

            # Initialize all 5 DRV2605 chips
            self._drv_x_plus: DRV2605 = DRV2605(i2c, addr_x_plus)
            self._drv_x_minus: DRV2605 = DRV2605(i2c, addr_x_minus)
            self._drv_y_plus: DRV2605 = DRV2605(i2c, addr_y_plus)
            self._drv_y_minus: DRV2605 = DRV2605(i2c, addr_y_minus)
            self._drv_z_minus: DRV2605 = DRV2605(i2c, addr_z_minus)

            # Configure all drivers for real-time control using ERM mode
            for drv in [
                self._drv_x_plus,
                self._drv_x_minus,
                self._drv_y_plus,
                self._drv_y_minus,
                self._drv_z_minus,
            ]:
                drv.use_ERM()
                drv.mode = MODE_REALTIME
                drv.realtime_value = 0  # Start with zero output

            self._log.debug("Magnetorquer DRV2605 drivers initialized successfully")

        except Exception as e:
            raise HardwareInitializationError(
                "Failed to initialize magnetorquer DRV2605 drivers"
            ) from e

    def set_dipole_moment(self, dipole_moment: tuple[float, float, float]) -> None:
        """Set the magnetic dipole moment for all three axes.

        The dipole moment is achieved by controlling the current through each coil
        using the DRV2605 drivers in real-time mode. The dipole moment is related
        to the current by: dipole_moment = N * I * A, where N is the number of turns,
        I is the current, and A is the coil area.

        Args:
            dipole_moment: A tuple containing the dipole moment for each axis (x, y, z) in A⋅m².
                          Positive values actuate the positive face, negative values actuate
                          the negative face.

        Raises:
            ValueError: If any dipole moment exceeds the maximum achievable value.
            RuntimeError: If communication with the DRV2605 chips fails.
        """
        x_dipole, y_dipole, z_dipole = dipole_moment

        try:
            # Calculate and set X-axis dipole moment
            self._set_axis_dipole(
                x_dipole,
                self._drv_x_plus,
                self._drv_x_minus,
                self._coil_num_turns_x_y,
                self._coil_area_x_y,
                self._coil_max_current_x_y,
                "X",
            )

            # Calculate and set Y-axis dipole moment
            self._set_axis_dipole(
                y_dipole,
                self._drv_y_plus,
                self._drv_y_minus,
                self._coil_num_turns_x_y,
                self._coil_area_x_y,
                self._coil_max_current_x_y,
                "Y",
            )

            # Calculate and set Z-axis dipole moment
            # Z-axis only has negative face coil
            z_current = self._dipole_to_current(
                z_dipole, self._coil_num_turns_z, self._coil_area_z
            )

            # Validate Z-axis current
            if abs(z_current) > self._coil_max_current_z:
                raise ValueError(
                    f"Z-axis dipole moment {z_dipole:.6f} A⋅m² exceeds maximum "
                    f"({self._coil_max_current_z * self._coil_num_turns_z * self._coil_area_z:.6f} A⋅m²)"
                )

            # Set Z-axis current (only Z- face, so negate the sign for proper direction)
            z_value = self._current_to_drv_value(-z_current, self._coil_max_current_z)
            self._drv_z_minus.realtime_value = z_value

        except ValueError:
            # Re-raise ValueError with context
            raise
        except Exception as e:
            raise RuntimeError("Failed to set magnetorquer dipole moment") from e

    def _set_axis_dipole(
        self,
        dipole: float,
        drv_plus: DRV2605,
        drv_minus: DRV2605,
        num_turns: float,
        area: float,
        max_current: float,
        axis_name: str,
    ) -> None:
        """Set the dipole moment for a single axis with both positive and negative faces.

        Args:
            dipole: Desired dipole moment in A⋅m².
            drv_plus: DRV2605 driver for the positive face.
            drv_minus: DRV2605 driver for the negative face.
            num_turns: Number of turns in the coil.
            area: Area of the coil in m².
            max_current: Maximum current for the coil in A.
            axis_name: Name of the axis for logging/error messages.

        Raises:
            ValueError: If the dipole moment exceeds the maximum achievable value.
        """
        # Calculate required current
        current = self._dipole_to_current(dipole, num_turns, area)

        # Validate current against maximum
        if abs(current) > max_current:
            max_dipole = max_current * num_turns * area
            raise ValueError(
                f"{axis_name}-axis dipole moment {dipole:.6f} A⋅m² exceeds maximum "
                f"({max_dipole:.6f} A⋅m²)"
            )

        # Set the appropriate driver based on current direction
        if current >= 0:
            # Positive dipole: activate positive face, deactivate negative face
            plus_value = self._current_to_drv_value(current, max_current)
            drv_plus.realtime_value = plus_value
            drv_minus.realtime_value = 0
        else:
            # Negative dipole: activate negative face, deactivate positive face
            minus_value = self._current_to_drv_value(-current, max_current)
            drv_plus.realtime_value = 0
            drv_minus.realtime_value = minus_value

    @staticmethod
    def _dipole_to_current(dipole: float, num_turns: float, area: float) -> float:
        """Convert dipole moment to required current.

        Args:
            dipole: Desired dipole moment in A⋅m².
            num_turns: Number of turns in the coil.
            area: Area of the coil in m².

        Returns:
            Required current in Amperes.
        """
        # dipole_moment = N * I * A
        # Therefore: I = dipole_moment / (N * A)
        return dipole / (num_turns * area)

    @staticmethod
    def _current_to_drv_value(current: float, max_current: float) -> int:
        """Convert current to DRV2605 realtime value.

        The DRV2605 in ERM mode with open-loop control expects a signed 8-bit value
        where 127 represents maximum forward drive and -127 represents maximum reverse.
        For unidirectional control (as used here), we map 0-max_current to 0-127.

        Args:
            current: Desired current in Amperes.
            max_current: Maximum current capability in Amperes.

        Returns:
            DRV2605 realtime value (0-127).
        """
        # Clamp current to valid range
        current = max(0.0, min(current, max_current))

        # Scale to 0-127 range
        if max_current > 0:
            value = int((current / max_current) * 127)
        else:
            value = 0

        return max(0, min(value, 127))
