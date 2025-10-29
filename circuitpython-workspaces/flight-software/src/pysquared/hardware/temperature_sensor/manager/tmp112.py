"""TMP112 temperature sensor manager and minimal CircuitPython-style driver.

Implements `TemperatureSensorProto` and returns `Temperature` readings.

References:
- TI TMP112 Datasheet: https://www.ti.com/lit/ds/symlink/tmp112.pdf
- Zephyr TMP112 sample (for reference API usage): https://docs.zephyrproject.org/latest/samples/sensor/tmp112/README.html
- Prior CircuitPython driver style (MCP9808): https://github.com/adafruit/Adafruit_CircuitPython_MCP9808
"""

from busio import I2C

from ....logger import Logger
from ....protos.temperature_sensor import TemperatureSensorProto
from ....sensor_reading.error import SensorReadingUnknownError
from ....sensor_reading.temperature import Temperature
from ...exception import HardwareInitializationError


class _TMP112:
    """Minimal TMP112 driver sufficient for temperature reads.

    - Default I2C address: 0x48 (ADDR=GND). Address range 0x48-0x4B depending on pins.
    - Temperature register: pointer 0x00, 12-bit two's complement, 0.0625 °C/LSB.
    """

    _DEFAULT_ADDRESS: int = 0x48

    _REG_TEMPERATURE: int = 0x00
    _REG_CONFIG: int = 0x01

    def __init__(self, i2c: I2C, address: int | None = None) -> None:
        self._i2c: I2C = i2c
        self._address: int = address if address is not None else self._DEFAULT_ADDRESS
        # No special init required for basic continuous conversion

    @property
    def temperature(self) -> float:
        """Read temperature in degrees Celsius."""
        raw = self._read_temp_raw()
        return self._convert_raw_to_celsius(raw)

    # Internals
    def _read_temp_raw(self) -> int:
        """Read the raw 12-bit temperature value from the sensor."""
        # Write pointer to temperature register, then read 2 bytes MSB first
        pointer = bytes((self._REG_TEMPERATURE & 0xFF,))
        buf = bytearray(2)
        while not self._i2c.try_lock():
            pass
        try:
            self._i2c.writeto_then_readfrom(self._address, pointer, buf)
        finally:
            self._i2c.unlock()
        msb = buf[0]
        lsb = buf[1]
        # 12-bit two's complement: bits [15:4]; combine as (msb << 4) | (lsb >> 4)
        raw12 = ((msb << 4) | (lsb >> 4)) & 0xFFF
        return raw12

    @staticmethod
    def _convert_raw_to_celsius(raw12: int) -> float:
        """Convert a 12-bit two's-complement value to degrees Celsius."""
        # Sign extend 12-bit two's complement
        if raw12 & 0x800:  # negative
            raw12 -= 1 << 12
        return float(raw12) * 0.0625


class TMP112Manager(TemperatureSensorProto):
    """Manages the TMP112 temperature sensor."""

    def __init__(self, logger: Logger, i2c: I2C, address: int | None = None) -> None:
        self._log: Logger = logger
        try:
            self._log.debug("Initializing temperature sensor")
            self._sensor = _TMP112(i2c, address)
        except Exception as e:
            raise HardwareInitializationError(
                "Failed to initialize temperature sensor"
            ) from e

    def get_temperature(self) -> Temperature:
        """Return the current temperature as a `Temperature` reading."""
        try:
            return Temperature(self._sensor.temperature)
        except Exception as e:
            raise SensorReadingUnknownError("Failed to read temperature") from e
