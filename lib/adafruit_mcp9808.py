# SPDX-FileCopyrightText: 2017 Scott Shawcroft for Adafruit Industries
# SPDX-FileCopyrightText: 2021 Jose David Montoya
# SPDX-License-Identifier: MIT

"""
`adafruit_mcp9808`
====================================================

CircuitPython library to support MCP9808 high accuracy temperature sensor.

* Author(s): Scott Shawcroft, Jose David M.

Implementation Notes
--------------------

**Hardware:**

* `Adafruit MCP9808 High Accuracy I2C Temperature Sensor Breakout
  <https://www.adafruit.com/products/1782>`_ (Product ID: 1782)

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's Bus Device library:
  https://github.com/adafruit/Adafruit_CircuitPython_BusDevice

* Adafruit's Register library:
  https://github.com/adafruit/Adafruit_CircuitPython_Register


**Notes:**

#.  Datasheet: http://www.adafruit.com/datasheets/MCP9808.pdf

"""

from micropython import const
from adafruit_bus_device.i2c_device import I2CDevice
from adafruit_register.i2c_bits import RWBits
from adafruit_register.i2c_bit import ROBit

try:
    import typing  # pylint: disable=unused-import
    from typing_extensions import Literal
    from busio import I2C
except ImportError:
    pass

__version__ = "3.3.24"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MCP9808.git"


_MCP9808_DEFAULT_ADDRESS = const(0x18)
_MCP9808_DEVICE_ID = const(0x54)
_MCP9808_REG_CONFIGURATION = const(0x01)
_MCP9808_REG_UPPER_TEMP = const(0x02)
_MCP9808_REG_LOWER_TEMP = const(0x03)
_MCP9808_REG_CRITICAL_TEMP = const(0x04)
_MCP9808_REG__TEMP = const(0x05)
_MCP9808_REG_MANUFACTURER_ID = const(0x06)
_MCP9808_REG_DEVICE_ID = const(0x07)
_MCP9808_REG_RESOLUTION = const(0x08)

# Resolution settings

_MCP9808_RESOLUTION_HALF_C = const(0x0)
_MCP9808_RESOLUTION_QUARTER_C = const(0x1)
_MCP9808_RESOLUTION_EIGHTH_C = const(0x2)
_MCP9808_RESOLUTION_SIXTEENTH_C = const(0x3)


class MCP9808:
    """Interface to the MCP9808 temperature sensor.

    :param ~busio.I2C i2c_bus: The I2C bus the MCP9808 is connected to.
    :param int address: The I2C address of the device. Defaults to :const:`0x18`

    **MCP9808 Settings**
        You could set the MCP9808 with different temperature limits and compare them with the
        ambient temperature Ta

        - above_critical: this value will be set to `True` when Ta is above this limit
        - above_upper: this value will be set to `True` when Ta is above this limit
        - below_lower: this value will be set to `True` when Ta is below this limit

        To get this value, you will need to read the temperature, and then access the attribute


    **Quickstart: Importing and using the MCP9808**

        Here is an example of using the :class:`MCP9808` class.
        First you will need to import the libraries to use the sensor

        .. code-block:: python

            import board
            import adafruit_mcp9808

        Once this is done you can define your `board.I2C` object and define your sensor object

        .. code-block:: python

            i2c = board.I2C()   # uses board.SCL and board.SDA
            mcp = adafruit_mcp9808.MCP9808(i2c_bus)

        Now you have access to the change in temperature using the
        :attr:`temperature` attribute. This temperature is in Celsius.

        .. code-block:: python

            temperature = mcp.temperature

    """

    _MCP9808_REG_RESOLUTION_SET = RWBits(2, 0x08, 0, register_width=2)
    above_critical = ROBit(_MCP9808_REG__TEMP, 7, register_width=1)
    """True when the temperature is above the currently
    set critical temperature. False Otherwise"""

    above_upper = ROBit(_MCP9808_REG__TEMP, 6, register_width=1)
    """True when the temperature is above the currently
    set high temperature. False Otherwise"""

    below_lower = ROBit(_MCP9808_REG__TEMP, 5, register_width=1)
    """True when the temperature is below the currently
    set lower temperature. False Otherwise"""

    def __init__(self, i2c_bus: I2C, address: int = _MCP9808_DEFAULT_ADDRESS) -> None:
        self.i2c_device = I2CDevice(i2c_bus, address)

        # Verify the manufacturer and device ids to ensure we are talking to
        # what we expect.
        self.buf = bytearray(3)
        self.buf[0] = _MCP9808_REG_MANUFACTURER_ID
        with self.i2c_device as i2c:
            i2c.write_then_readinto(self.buf, self.buf, out_end=1, in_start=1)

        ok = self.buf[2] == _MCP9808_DEVICE_ID and self.buf[1] == 0

        # Check device id.
        self.buf[0] = _MCP9808_REG_DEVICE_ID
        with self.i2c_device as i2c:
            i2c.write_then_readinto(self.buf, self.buf, out_end=1, in_start=1)

        if not ok or self.buf[1] != 0x04:
            raise ValueError(
                "Unable to find MCP9808 at i2c address " + str(hex(address))
            )

    @property
    def temperature(self) -> float:
        """Temperature in Celsius. Read-only."""
        self.buf[0] = _MCP9808_REG__TEMP
        with self.i2c_device as i2c:
            i2c.write_then_readinto(self.buf, self.buf, out_end=1, in_start=1)

        return self._temp_conv()

    def _temp_conv(self) -> float:
        """Internal function to convert temperature given by the sensor"""
        # Clear flags from the value
        self.buf[1] = self.buf[1] & 0x1F
        if self.buf[1] & 0x10 == 0x10:
            self.buf[1] = self.buf[1] & 0x0F
            return (self.buf[1] * 16 + self.buf[2] / 16.0) - 256
        return self.buf[1] * 16 + self.buf[2] / 16.0

    def _limit_temperatures(
        self, temp: int, t_address: Literal[0x02, 0x03, 0x04] = 0x02
    ) -> None:
        """Internal function to setup limit temperature

        :param int temp: temperature limit
        :param int t_address: register address for the temperature limit
                                0x02 : Upper Limit
                                0x03 : Lower Limit
                                0x04 : Critical Limit
        """

        if temp < 0:
            negative = True
            temp = abs(temp)
        else:
            negative = False

        self.buf[0] = t_address

        self.buf[1] = temp >> 4
        if negative:
            self.buf[1] = self.buf[1] | 0x10

        self.buf[2] = (temp & 0x0F) << 4

        with self.i2c_device as i2c:
            i2c.write(self.buf)

    def _get_temperature(self, address: Literal[0x02, 0x03, 0x04]) -> float:
        self.buf[0] = address
        with self.i2c_device as i2c:
            i2c.write_then_readinto(self.buf, self.buf, out_end=1, in_start=1)

        return self._temp_conv()

    def _set_temperature(self, temp: int, address: Literal[0x02, 0x03, 0x04]) -> None:
        self._limit_temperatures(temp, address)

    @property
    def upper_temperature(self) -> float:
        """Upper alarm temperature in Celsius"""

        return self._get_temperature(_MCP9808_REG_UPPER_TEMP)

    @upper_temperature.setter
    def upper_temperature(self, temp: int) -> None:
        """Setup Upper temperature"""

        self._limit_temperatures(temp, _MCP9808_REG_UPPER_TEMP)

    @property
    def lower_temperature(self) -> float:
        """Lower alarm temperature in Celsius"""

        return self._get_temperature(_MCP9808_REG_LOWER_TEMP)

    @lower_temperature.setter
    def lower_temperature(self, temp: int) -> None:
        """Setup Lower temperature"""

        self._limit_temperatures(temp, _MCP9808_REG_LOWER_TEMP)

    @property
    def critical_temperature(self) -> float:
        """Critical alarm temperature in Celsius"""

        return self._get_temperature(_MCP9808_REG_CRITICAL_TEMP)

    @critical_temperature.setter
    def critical_temperature(self, temp: int) -> None:
        """Setup Critical temperature"""

        self._limit_temperatures(temp, _MCP9808_REG_CRITICAL_TEMP)

    @property
    def resolution(self) -> Literal[0, 1, 2, 3]:
        """Temperature Resolution in Celsius

        =======   ============   ==============
         Value     Resolution     Reading Time
        =======   ============   ==============
          0          0.5°C            30 ms
          1          0.25°C           65 ms
          2         0.125°C          130 ms
          3         0.0625°C         250 ms
        =======   ============   ==============

        """

        return self._MCP9808_REG_RESOLUTION_SET

    @resolution.setter
    def resolution(self, resol_value: Literal[0, 1, 2, 3] = 3) -> None:
        """Setup Critical temperature"""

        self._MCP9808_REG_RESOLUTION_SET = resol_value  # pylint: disable=invalid-name
