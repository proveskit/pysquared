"""
Mock for Adafruit INA219

https://github.com/adafruit/Adafruit_CircuitPython_INA219/blob/main/adafruit_ina219.py
"""


class INA219:
    def __init__(self, i2c, addr) -> None:
        self.i2c = i2c
        self.addr = addr

    bus_voltage = 0.0
    shunt_voltage = 0.0
    current = 0.0
