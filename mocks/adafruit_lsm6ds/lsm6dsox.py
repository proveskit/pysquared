from busio import I2C


class LSM6DSOX:
    def __init__(self, i2c_bus: I2C, address: int) -> None: ...
