from busio import I2C


class RV3028:
    def __init__(self, i2c_bus: I2C) -> None: ...

    def configure_backup_switchover(self, mode: str, interrupt: bool) -> None: ...
