from busio import I2C


class LSM6DSOX:
    def __init__(self, i2c_bus: I2C, address: int) -> None: ...

    acceleration: tuple[float, float, float] = (0.0, 0.0, 0.0)
    gyro: tuple[float, float, float] = (0.0, 0.0, 0.0)
    temperature: float = 0.0
