"""
Mock for Adafruit LIS2MDL
https://github.com/adafruit/Adafruit_CircuitPython_LIS2MDL/blob/main/adafruit_lis2mdl.py
"""


class LIS2MDL:
    def __init__(self, i2c) -> None:
        self.i2c = i2c

    magnetic: tuple[float, float, float] = (0.0, 0.0, 0.0)
