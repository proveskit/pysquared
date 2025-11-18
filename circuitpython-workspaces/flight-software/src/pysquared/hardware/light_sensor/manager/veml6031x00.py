"""VEML6031x00 light sensor manager for CircuitPython.

This module provides a CircuitPython implementation to interact with the
VEML6031/VEML6030 ambient light sensor family using direct I2C register
access. It mirrors the behavior of the Zephyr driver with support for
single-measurement (active force) mode and data-ready polling.

Usage:
    logger = Logger()
    i2c = initialize_i2c_bus(logger, board.SCL, board.SDA, 100000)
    sensor = VEML6031x00Manager(logger, i2c)
    lux = sensor.get_lux()
"""

import time

from adafruit_tca9548a import TCA9548A_Channel
from busio import I2C

from ....logger import Logger
from ....protos.light_sensor import LightSensorProto
from ....sensor_reading.error import (
    SensorReadingTimeoutError,
    SensorReadingUnknownError,
    SensorReadingValueError,
)
from ....sensor_reading.light import Light
from ....sensor_reading.lux import Lux
from ...exception import HardwareInitializationError

# I2C default address
_DEFAULT_I2C_ADDR = 0x29

# Registers (16-bit command codes)
_REG_ALS_CONF_0 = 0x00
_REG_ALS_CONF_1 = 0x01
_REG_ALS_WH_L = 0x04
_REG_ALS_WH_H = 0x05
_REG_ALS_WL_L = 0x06
_REG_ALS_WL_H = 0x07
_REG_ALS_DATA_L = 0x10
_REG_ALS_DATA_H = 0x11
_REG_IR_DATA_L = 0x12
_REG_IR_DATA_H = 0x13
_REG_ID_L = 0x14
_REG_ID_H = 0x15
_REG_ALS_INT = 0x17

# Device constants
_DEFAULT_ID = 0x01
_ALS_AF_DATA_READY = 1 << 3
_ALS_DATA_OVERFLOW = 0xFFFF


# Enumerations for settings (indices into resolution matrix)
class _Div4:
    """Effective photodiode size selection indices."""

    SIZE_4_4 = 0
    SIZE_1_4 = 1
    COUNT = 2


class _Gain:
    """Gain selection indices for ambient-light channel."""

    GAIN_1 = 0
    GAIN_2 = 1
    GAIN_0_66 = 2
    GAIN_0_5 = 3
    COUNT = 4


class _It:
    """Integration time selection indices (shortest to longest)."""

    IT_3_125MS = 0
    IT_6_25MS = 1
    IT_12_5MS = 2
    IT_25MS = 3
    IT_50MS = 4
    IT_100MS = 5
    IT_200MS = 6
    IT_400MS = 7
    COUNT = 8


# Integration time values in microseconds matching _It indices
_IT_US = [
    3125,
    6250,
    12500,
    25000,
    50000,
    100000,
    200000,
    400000,
]


# Resolution matrix [div4][gain][itim] in lux/count (from Zephyr driver)
_RESOLUTION = (
    # size 4/4
    (
        (0.8704, 0.4352, 0.2176, 0.1088, 0.0544, 0.0272, 0.0136, 0.0068),  # gain 1
        (0.4352, 0.2176, 0.1088, 0.0544, 0.0272, 0.0136, 0.0068, 0.0034),  # gain 2
        (1.3188, 0.6504, 0.3297, 0.1648, 0.0824, 0.0412, 0.0206, 0.0103),  # gain 0.66
        (1.7408, 0.8704, 0.4352, 0.2176, 0.1088, 0.0544, 0.0272, 0.0136),  # gain 0.5
    ),
    # size 1/4
    (
        (3.4816, 1.7408, 0.8704, 0.4352, 0.2176, 0.1088, 0.0544, 0.0272),  # gain 1
        (1.7408, 0.8704, 0.4352, 0.2176, 0.1088, 0.0544, 0.0272, 0.0136),  # gain 2
        (5.2752, 2.6376, 1.3188, 0.6594, 0.3297, 0.1648, 0.0824, 0.0412),  # gain 0.66
        (6.9632, 3.4816, 1.7408, 0.8704, 0.4352, 0.2176, 0.1088, 0.0544),  # gain 0.5
    ),
)


def _in_range(val: int, min_v: int, max_v: int) -> bool:
    """Return True if val is between min_v and max_v inclusive."""
    return (val >= min_v) and (val <= max_v)


class VEML6031x00Manager(LightSensorProto):
    """Manages the VEML6031/VEML6030 ambient light sensor via I2C.

    Implements single-shot measurement using active force mode and polls the
    data-ready bit before reading ambient light and IR data. Converts counts to lux
    using the device's resolution matrix based on configuration.
    """

    def __init__(
        self,
        logger: Logger,
        i2c: I2C | TCA9548A_Channel,
        address: int = _DEFAULT_I2C_ADDR,
        integration_time: int = _It.IT_100MS,
        gain: int = _Gain.GAIN_1,
        div4: int = _Div4.SIZE_4_4,
        persistence: int = 0,
    ) -> None:
        """Initialize the manager and validate the device ID.

        Args:
            logger: Logger to log messages.
            i2c: I2C bus or TCA channel the device is on.
            address: I2C address of the sensor (default 0x29).
            integration_time: One of `_It.*` indices (default 100ms).
            gain: One of `_Gain.*` indices (default 1x).
            div4: One of `_Div4.*` indices (default full size).
            persistence: Persistence setting for ambient-light channel (0 maps to 1 sample).
        """
        self._log: Logger = logger
        self._i2c: I2C | TCA9548A_Channel = i2c
        self._addr: int = address

        # Current configuration state
        self._sd = 0
        self._int_en = 0
        self._trig = 1
        self._af = 1
        self._ir_sd = 0
        self._cal = 1
        self._div4 = div4
        self._gain = gain
        self._itim = integration_time
        self._pers = persistence
        self._thresh_high = 0xFFFF
        self._thresh_low = 0x0000

        # Last measurement
        self._als_counts = 0
        self._ir_counts = 0
        self._als_lux = 0.0

        # Probe device ID
        try:
            self._log.debug("Initializing VEML6031x00 light sensor")
            id_l = self._read8(_REG_ID_L)
            if id_l != _DEFAULT_ID:
                raise HardwareInitializationError("Unexpected VEML6031x00 device ID")
            _ = self._read8(_REG_ID_H)
            # Apply initial configuration
            self._write_thresh_low(self._thresh_low)
            self._write_thresh_high(self._thresh_high)
            self._write_conf()
        except HardwareInitializationError:
            raise
        except Exception as e:
            raise HardwareInitializationError("Failed to initialize VEML6031x00") from e

    def get_light(self) -> Light:
        """Perform a single measurement and return raw ambient-light counts.

        Returns:
            Light: Non-unit-specific reading (sensor counts).
        """
        try:
            self._single_measurement_sequence()
            return Light(float(self._als_counts))
        except SensorReadingTimeoutError:
            raise
        except SensorReadingValueError:
            raise
        except Exception as e:
            raise SensorReadingUnknownError("Failed to get light reading") from e

    def get_lux(self) -> Lux:
        """Perform a single measurement and return the light level in lux.

        Returns:
            Lux: Light level in SI lux.
        """
        try:
            self._single_measurement_sequence()
            if self._als_lux is None or self._als_lux == 0:
                raise SensorReadingValueError("Lux reading is invalid or zero")
            return Lux(self._als_lux)
        except SensorReadingTimeoutError:
            raise
        except SensorReadingValueError:
            raise
        except Exception as e:
            raise SensorReadingUnknownError("Failed to get lux reading") from e

    def reset(self) -> None:
        """Place device into shutdown briefly and then resume operation."""
        try:
            self._sd = 1
            self._ir_sd = 1
            self._write_conf()
            time.sleep(0.05)
            self._sd = 0
            self._ir_sd = 0
            self._write_conf()
            self._log.debug("Light sensor reset successfully")
        except Exception as e:
            self._log.error("Failed to reset VEML6031x00 light sensor: %s", e)

    # --- Low-level helpers ---
    def _write_conf(self) -> None:
        """Write configuration registers based on current state.

        Encodes shutdown, gain, size, persistence, active-force trigger,
        and integration time into the two configuration bytes.
        """
        conf0 = 0
        conf1 = 0
        # conf1 bits
        conf1 |= (self._ir_sd & 0x01) << 7
        conf1 |= (self._div4 & 0x01) << 6
        conf1 |= (self._gain & 0x03) << 3
        conf1 |= (self._pers & 0x03) << 1
        conf1 |= 1 if self._cal else 0

        # conf0 bits
        conf0 |= (self._itim & 0x07) << 4
        conf0 |= (1 if self._af else 0) << 3
        conf0 |= (1 if self._trig else 0) << 2
        conf0 |= (1 if self._int_en else 0) << 1
        conf0 |= 1 if self._sd else 0

        self._write16(_REG_ALS_CONF_0, (conf1 << 8) | conf0)

    def _write_thresh_low(self, counts: int) -> None:
        """Write low threshold in sensor counts."""
        counts &= 0xFFFF
        self._write16(_REG_ALS_WL_L, counts)

    def _write_thresh_high(self, counts: int) -> None:
        """Write high threshold in sensor counts."""
        counts &= 0xFFFF
        self._write16(_REG_ALS_WH_L, counts)

    def _single_measurement_sequence(self) -> None:
        """Run active-force single measurement and update cached readings.

        Waits for the data-ready flag up to a bounded timeout, then reads
        ambient-light and IR counts and computes lux using the resolution
        matrix corresponding to the current configuration.
        """
        # Configure for single measurement (active force)
        self._ir_sd = 0
        self._cal = 1
        self._af = 1
        self._trig = 1
        self._int_en = 0
        self._sd = 0
        self._write_conf()

        # Initial read clears flags on some devices
        _ = self._read8(_REG_ALS_INT)

        # Sleep for integration time
        if _in_range(self._itim, 0, _It.COUNT - 1):
            time.sleep(_IT_US[self._itim] / 1_000_000.0)
        else:
            # Fallback minimal wait if misconfigured
            time.sleep(0.001)

        # Poll data-ready with timeout
        start = time.monotonic()
        while True:
            int_val = self._read8(_REG_ALS_INT)
            if (int_val & _ALS_AF_DATA_READY) != 0:
                break
            if time.monotonic() - start > 0.5:  # 500ms safety timeout
                raise SensorReadingTimeoutError("VEML6031x00 data ready timeout")
            time.sleep(0.001)

        # Read result registers (little endian pairs)
        als_counts = self._read16(_REG_ALS_DATA_L)
        ir_counts = self._read16(_REG_IR_DATA_L)

        if als_counts == _ALS_DATA_OVERFLOW:
            raise SensorReadingValueError("Ambient light reading overflow (saturation)")

        if not (
            _in_range(self._div4, 0, _Div4.COUNT - 1)
            and _in_range(self._gain, 0, _Gain.COUNT - 1)
            and _in_range(self._itim, 0, _It.COUNT - 1)
        ):
            raise SensorReadingUnknownError("Invalid sensor configuration indices")

        res = _RESOLUTION[self._div4][self._gain][self._itim]
        self._als_counts = als_counts
        self._ir_counts = ir_counts
        self._als_lux = als_counts * res

    def _acquire_i2c_lock(self) -> None:
        """Acquire I2C bus lock with retry logic.

        Raises:
            RuntimeError: If unable to lock the I2C bus after 200 attempts.
        """
        tries = 0
        while not self._i2c.try_lock():
            if tries >= 200:
                raise RuntimeError("Unable to lock I2C bus")
            tries += 1
            time.sleep(0)

    def _write16(self, reg: int, value: int) -> None:
        """Write a 16-bit little-endian value to a register."""
        # value is 16-bit little-endian
        buf = bytearray(3)
        buf[0] = reg & 0xFF
        buf[1] = value & 0xFF
        buf[2] = (value >> 8) & 0xFF
        self._acquire_i2c_lock()
        try:
            self._i2c.writeto(self._addr, buf)
        finally:
            self._i2c.unlock()

    def _read16(self, reg: int) -> int:
        """Read a 16-bit little-endian value from a register."""
        out_buf = bytearray(1)
        out_buf[0] = reg & 0xFF
        in_buf = bytearray(2)
        # Prefer repeated start if available
        self._acquire_i2c_lock()
        try:
            try:
                self._i2c.writeto_then_readfrom(self._addr, out_buf, in_buf)
            except AttributeError:
                # Fallback: separate ops
                self._i2c.writeto(self._addr, out_buf)
                self._i2c.readfrom_into(self._addr, in_buf)
        finally:
            self._i2c.unlock()
        return in_buf[0] | (in_buf[1] << 8)

    def _read8(self, reg: int) -> int:
        """Read an 8-bit value from a register."""
        out_buf = bytearray(1)
        out_buf[0] = reg & 0xFF
        in_buf = bytearray(1)
        self._acquire_i2c_lock()
        try:
            try:
                self._i2c.writeto_then_readfrom(self._addr, out_buf, in_buf)
            except AttributeError:
                self._i2c.writeto(self._addr, out_buf)
                self._i2c.readfrom_into(self._addr, in_buf)
        finally:
            self._i2c.unlock()
        return in_buf[0]
