from ....logger import Logger
from ...decorators import with_retries
from ...exception import HardwareInitializationError

try:
    from mocks.adafruit_ina219.ina219 import INA219
except ImportError:
    from adafruit_ina219 import INA219

try:
    from busio import I2C
except ImportError:
    pass


class INA219Factory:
    """
    Factory class for creating INA219 instances.
    """

    def __init__(self, i2c: I2C, addr: int) -> None:
        self.i2c: I2C = i2c
        self.addr: int = addr

    @with_retries(max_attempts=3, initial_delay=1)
    def create(self, logger: Logger) -> INA219:
        """
        Create an INA219 instance.
        """
        logger.debug("Creating INA219 instance")
        try:
            ina219 = INA219(self.i2c, addr=self.addr)
            return ina219
        except Exception as e:
            raise HardwareInitializationError(f"Failed to initialize INA219: {e}")
