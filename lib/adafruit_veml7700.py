# SPDX-FileCopyrightText: 2019 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_veml7700`
================================================================================

CircuitPython driver for VEML7700 high precision I2C ambient light sensor.


* Author(s): Kattni Rembor

Implementation Notes
--------------------

**Hardware:**

* `Adafruit VEML7700 Lux Sensor - I2C Light Sensor
  <https://www.adafruit.com/product/4162>`_ (Product ID: 4162)

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads

* Adafruit's Bus Device library:
  https://github.com/adafruit/Adafruit_CircuitPython_BusDevice

* Adafruit's Register library:
  https://github.com/adafruit/Adafruit_CircuitPython_Register
"""

from micropython import const
import adafruit_bus_device.i2c_device as i2cdevice
from adafruit_register.i2c_struct import ROUnaryStruct
from adafruit_register.i2c_bits import RWBits
from adafruit_register.i2c_bit import RWBit

try:
    import typing  # pylint: disable=unused-import
    from busio import I2C
except ImportError:
    pass

__version__ = "2.0.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_VEML7700.git"


class VEML7700:
    """Driver for the VEML7700 ambient light sensor.

    :param ~busio.I2C i2c_bus: The I2C bus the device is connected to
    :param int address: The I2C device address. Defaults to :const:`0x10`

    """

    # Ambient light sensor gain settings
    ALS_GAIN_1 = const(0x0)
    ALS_GAIN_2 = const(0x1)
    ALS_GAIN_1_8 = const(0x2)
    ALS_GAIN_1_4 = const(0x3)

    # Ambient light integration time settings

    ALS_25MS = const(0xC)
    ALS_50MS = const(0x8)
    ALS_100MS = const(0x0)
    ALS_200MS = const(0x1)
    ALS_400MS = const(0x2)
    ALS_800MS = const(0x3)

    # Gain value integers
    gain_values = {
        ALS_GAIN_2: 2,
        ALS_GAIN_1: 1,
        ALS_GAIN_1_4: 0.25,
        ALS_GAIN_1_8: 0.125,
    }

    # Integration time value integers
    integration_time_values = {
        ALS_25MS: 25,
        ALS_50MS: 50,
        ALS_100MS: 100,
        ALS_200MS: 200,
        ALS_400MS: 400,
        ALS_800MS: 800,
    }

    # ALS - Ambient light sensor high resolution output data
    light = ROUnaryStruct(0x04, "<H")
    """Ambient light data.

    This example prints the ambient light data. Cover the sensor to see the values change.

    .. code-block:: python

        import time
        import board
        import adafruit_veml7700

        i2c = board.I2C()  # uses board.SCL and board.SDA
        veml7700 = adafruit_veml7700.VEML7700(i2c)

        while True:
            print("Ambient light:", veml7700.light)
            time.sleep(0.1)
    """

    # WHITE - White channel output data
    white = ROUnaryStruct(0x05, "<H")
    """White light data.

    This example prints the white light data. Cover the sensor to see the values change.

    .. code-block:: python

        import time
        import board
        import adafruit_veml7700

        i2c = board.I2C()  # uses board.SCL and board.SDA
        veml7700 = adafruit_veml7700.VEML7700(i2c)

        while True:
            print("White light:", veml7700.white)
            time.sleep(0.1)
    """

    # ALS_CONF_0 - ALS gain, integration time, shutdown.
    light_shutdown = RWBit(0x00, 0, register_width=2)
    """Ambient light sensor shutdown. When ``True``, ambient light sensor is disabled."""
    light_gain = RWBits(2, 0x00, 11, register_width=2)
    """Ambient light gain setting. Gain settings are 2, 1, 1/4 and 1/8. Settings options are:
    ALS_GAIN_2, ALS_GAIN_1, ALS_GAIN_1_4, ALS_GAIN_1_8.

    This example sets the ambient light gain to 2 and prints the ambient light sensor data.

    .. code-block:: python

        import time
        import board
        import adafruit_veml7700

        i2c = board.I2C()  # uses board.SCL and board.SDA
        veml7700 = adafruit_vcnl4040.VCNL4040(i2c)

        veml7700.light_gain = veml7700.ALS_GAIN_2

        while True:
            print("Ambient light:", veml7700.light)
            time.sleep(0.1)

    """
    light_integration_time = RWBits(4, 0x00, 6, register_width=2)
    """Ambient light integration time setting. Longer time has higher sensitivity. Can be:
    ALS_25MS, ALS_50MS, ALS_100MS, ALS_200MS, ALS_400MS, ALS_800MS.

    This example sets the ambient light integration time to 400ms and prints the ambient light
    sensor data.

    .. code-block:: python

        import time
        import board
        import adafruit_veml7700

        i2c = board.I2C()  # uses board.SCL and board.SDA
        veml7700 = adafruit_vcnl4040.VCNL4040(i2c)

        veml7700.light_integration_time = veml7700.ALS_400MS

        while True:
            print("Ambient light:", veml7700.light)
            time.sleep(0.1)

    """

    def __init__(self, i2c_bus: I2C, address: int = 0x10) -> None:
        self.i2c_device = i2cdevice.I2CDevice(i2c_bus, address)
        for _ in range(3):
            try:
                # Set lowest gain to keep from overflow on init if bright light
                self.light_gain = self.ALS_GAIN_1_8
                #
                self.light_shutdown = False  # Enable the ambient light sensor
                break
            except OSError:
                pass
        else:
            raise RuntimeError("Unable to enable VEML7700 device")

    def integration_time_value(self) -> int:
        """Integration time value in integer form. Used for calculating :meth:`resolution`."""
        integration_time = self.light_integration_time
        return self.integration_time_values[integration_time]

    def gain_value(self) -> float:
        """Gain value in integer form. Used for calculating :meth:`resolution`."""
        gain = self.light_gain
        return self.gain_values[gain]

    def resolution(self) -> float:
        """Calculate the :meth:`resolution`` necessary to calculate lux. Based on
        integration time and gain settings."""
        resolution_at_max = 0.0036
        gain_max = 2
        integration_time_max = 800

        if (
            self.gain_value() == gain_max
            and self.integration_time_value() == integration_time_max
        ):
            return resolution_at_max
        return (
            resolution_at_max
            * (integration_time_max / self.integration_time_value())
            * (gain_max / self.gain_value())
        )

    @property
    def lux(self) -> float:
        """Light value in lux.

        This example prints the light data in lux. Cover the sensor to see the values change.

        .. code-block:: python

            import time
            import board
            import adafruit_veml7700

            i2c = board.I2C()  # uses board.SCL and board.SDA
            veml7700 = adafruit_veml7700.VEML7700(i2c)

            while True:
                print("Lux:", veml7700.lux)
                time.sleep(0.1)
        """
        return self.resolution() * self.light
