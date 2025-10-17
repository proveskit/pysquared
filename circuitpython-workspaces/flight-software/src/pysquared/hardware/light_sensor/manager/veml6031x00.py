"""This module defines the `VEML6031X00Manager` class and a minimal CircuitPython-style
driver for the Vishay VEML6031X00 ambient light sensor.

It exposes a manager compatible with `LightSensorProto` and returns readings as
`Light` and `Lux` objects, mirroring the API of `VEML7700Manager`.

References:
- Vishay VEML6031X00 Datasheet: https://www.vishay.com/docs/80007/veml6031x00.pdf
"""

import time

from busio import I2C

from ....logger import Logger
from ....protos.light_sensor import LightSensorProto
from ....sensor_reading.error import (
    SensorReadingUnknownError,
    SensorReadingValueError,
)
from ....sensor_reading.light import Light
from ....sensor_reading.lux import Lux
from ...exception import HardwareInitializationError

try:
    # CircuitPython does not ship typing, guard import
    pass
except ImportError:
    pass


class _VEML6031X00:
    """Minimal CircuitPython-style driver for VEML6031X00.

    Implements the subset needed by our manager:
    - configuration (enable/disable)
    - read ambient-light data and compute lux

    Notes
    -----
    The device supports two 7-bit I2C addresses per ordering code; the default for
    VEML6031X00 is 0x29 according to the datasheet (see table "SLAVE ADDRESS OPTIONS").
    """

    # I2C address (7-bit) for VEML6031X00 variant
    _DEFAULT_ADDRESS: int = 0x29

    # Register map (16-bit registers, little-endian LSB first)
    _REG_ALS_CONF: int = 0x00
    _REG_ALS_WH: int = 0x01
    _REG_ALS_WL: int = 0x02
    _REG_POWER_SAVING: int = 0x03
    _REG_ALS: int = 0x04
    _REG_WHITE: int = 0x05
    _REG_ALS_INT: int = 0x06

    # ALS_CONF bit fields we'll use (see datasheet). We'll default to gain x1 and IT 100ms.
    # Bits: [15:0] = {RESERVED, SD, INT_EN, PERS[1:0], IT[2:0], GAIN[1:0]}
    _ALS_CONF_SD_BIT: int = (
        0x0001  # SD at bit0 (datasheet SD at bit0: 0=enable, 1=shutdown)
    )

    # Integration time field (IT[2:0]) positions start at bit 6 in some VEML family devices.
    # For VEML6031X00 the mapping per datasheet table:
    # 3'b000=100ms, 001=200ms, 010=400ms, 011=800ms, 100=50ms, 101=25ms, 110=12.5ms, 111=6.25ms
    _IT_SHIFT: int = 6

    # Gain field (GAIN[1:0]) positions at bits [11:10]: 00=x1, 01=x2, 10=x0.5, 11=x0.125 (per datasheet table)
    _GAIN_SHIFT: int = (
        11 - 1
    )  # compute below to avoid mypy in CP; we set explicitly in code

    # Cached configuration
    _als_conf: int

    def __init__(self, i2c: I2C, address: int | None = None) -> None:
        """Initialize the device with default configuration.

        Args:
            i2c: Initialized I2C bus.
            address: Optional 7-bit I2C address; defaults to 0x29.
        """
        self._i2c: I2C = i2c
        self._address: int = address if address is not None else self._DEFAULT_ADDRESS
        # Defaults: power on (SD=0), gain x1, IT=100ms
        it_code: int = 0  # 100ms
        gain_code: int = 0  # x1
        self._als_conf = self._encode_als_conf(
            sd=False, it_code=it_code, gain_code=gain_code
        )
        self._write_u16(self._REG_ALS_CONF, self._als_conf)

    # Public properties matching style used by VEML7700 driver
    @property
    def light(self) -> float:
        """Return non-unit light reading (ambient-light raw counts)."""
        als_counts = self._read_u16(self._REG_ALS)
        return float(als_counts)

    @property
    def lux(self) -> float:
        """Return computed lux value based on counts and configuration.

        Lux = counts * resolution(gain, integration_time)
        Resolution table is provided in datasheet. We implement a compact
        resolver for the default configuration and common settings.
        """
        counts = self._read_u16(self._REG_ALS)
        resolution = self._resolution_lx_per_count(self._als_conf)
        return float(counts) * resolution

    # Internals
    def _resolution_lx_per_count(self, als_conf: int) -> float:
        """Compute lux-per-count resolution from the current configuration.

        Args:
            als_conf: Encoded ALS_CONF register shadow.

        Returns:
            Resolution in lux per count.
        """
        # Decode integration time and gain
        it_code = (als_conf >> self._IT_SHIFT) & 0x7
        # Gain bits per datasheet at [11:10]; compute explicitly
        gain_code = (als_conf >> 11) & 0x3

        # Base resolution for IT=100ms, GAIN=x1 is 0.0272 lx/ct (from datasheet table)
        base_resolution = 0.0272

        # Adjust for integration time scaling (double IT halves resolution per-count)
        # Mapping relative to 100ms
        it_scale = {
            0: 1.0,  # 100ms
            1: 0.5,  # 200ms -> 0.0272/2
            2: 0.25,  # 400ms -> 0.0272/4
            3: 0.125,  # 800ms -> 0.0272/8
            4: 2.0,  # 50ms  -> 0.0272*2
            5: 4.0,  # 25ms  -> 0.0272*4
            6: 8.0,  # 12.5ms
            7: 16.0,  # 6.25ms
        }.get(it_code, 1.0)

        # Gain scaling relative to x1
        gain_scale = {
            0: 1.0,  # x1
            1: 0.5,  # x2 gain halves lx/ct
            2: 2.0,  # x0.5 doubles lx/ct
            3: 8.0,  # x0.125 multiplies by 8
        }.get(gain_code, 1.0)

        return base_resolution * it_scale * gain_scale

    def _encode_als_conf(self, sd: bool, it_code: int, gain_code: int) -> int:
        """Encode shutdown, integration time, and gain into ALS_CONF register value."""
        conf = 0
        # SD bit 0: 0 = enable, 1 = shutdown
        if sd:
            conf |= self._ALS_CONF_SD_BIT
        # IT at bits [8:6]
        conf |= (it_code & 0x7) << self._IT_SHIFT
        # GAIN at bits [11:10]
        conf |= (gain_code & 0x3) << 10
        return conf

    def _write_u16(self, register: int, value: int) -> None:
        """Write a 16-bit little-endian value to a register."""
        # VEML devices use little-endian (LSB first) for 16-bit registers
        data = bytes((register & 0xFF, value & 0xFF, (value >> 8) & 0xFF))
        while not self._i2c.try_lock():
            pass
        try:
            self._i2c.writeto(self._address, data)
        finally:
            self._i2c.unlock()

    def _read_u16(self, register: int) -> int:
        """Read a 16-bit little-endian value from a register."""
        # Write register, then read 2 bytes LSB first
        reg = bytes((register & 0xFF,))
        buf = bytearray(2)
        while not self._i2c.try_lock():
            pass
        try:
            # Use repeated start via writeto_then_readfrom to satisfy typing and behavior
            self._i2c.writeto_then_readfrom(self._address, reg, buf)
        finally:
            self._i2c.unlock()
        return buf[0] | (buf[1] << 8)


class VEML6031X00Manager(LightSensorProto):
    """Manages the VEML6031X00 ambient light sensor.

    This mirrors the `VEML7700Manager` surface so it can be swapped easily.
    """

    def __init__(self, logger: Logger, i2c: I2C, address: int | None = None) -> None:
        """Initialize the manager and underlying driver.

        Args:
            logger: Logger for diagnostic messages.
            i2c: Initialized I2C bus.
            address: Optional 7-bit I2C address; defaults per part number.
        """
        self._log: Logger = logger
        try:
            self._log.debug("Initializing light sensor")
            self._light_sensor = _VEML6031X00(i2c, address)
        except Exception as e:
            raise HardwareInitializationError(
                "Failed to initialize light sensor"
            ) from e

    def get_light(self) -> Light:
        """Return non-unit-specific light level as a `Light` reading."""
        try:
            return Light(self._light_sensor.light)
        except Exception as e:
            raise SensorReadingUnknownError("Failed to get light reading") from e

    def get_lux(self) -> Lux:
        """Return lux as a `Lux` reading; validates non-zero, non-None values."""
        try:
            # Saturation check: Zephyr treats raw ambient-light 0xFFFF as saturation
            raw_counts = self._light_sensor._read_u16(self._light_sensor._REG_ALS)
            if raw_counts == 0xFFFF:
                raise SensorReadingValueError("Lux reading saturated (raw=0xFFFF)")

            lux = self._light_sensor.lux
        except SensorReadingValueError:
            # Propagate value errors (e.g., saturation) directly
            raise
        except Exception as e:
            raise SensorReadingUnknownError("Failed to get lux reading") from e

        if lux is None or lux == 0:
            raise SensorReadingValueError("Lux reading is invalid or zero")
        return Lux(lux)

    def reset(self) -> None:
        """Best-effort reset by toggling shutdown bit in configuration."""
        try:
            # Set shutdown bit
            conf_sd = self._light_sensor._encode_als_conf(
                sd=True, it_code=0, gain_code=0
            )
            self._light_sensor._write_u16(self._light_sensor._REG_ALS_CONF, conf_sd)
            time.sleep(0.1)
            # Clear shutdown bit (enable)
            conf_en = self._light_sensor._encode_als_conf(
                sd=False, it_code=0, gain_code=0
            )
            self._light_sensor._write_u16(self._light_sensor._REG_ALS_CONF, conf_en)
            self._log.debug("Light sensor reset successfully")
        except Exception as e:
            self._log.error("Failed to reset light sensor:", e)
