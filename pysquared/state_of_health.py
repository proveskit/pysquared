from collections import OrderedDict

from microcontroller import Processor

from .logger import Logger
from .nvm.counter import Counter
from .nvm.flag import Flag
from .nvm.register import Register, flag_register_lookup, register_lookup
from .protos.imu import IMUProto
from .protos.power_monitor import PowerMonitorProto
from .protos.radio import RadioProto
from .protos.temperature_sensor import TemperatureSensorProto

try:
    from typing import Callable, OrderedDict
except Exception:
    pass


class StateOfHealth:
    def __init__(
        self,
        logger: Logger,
        *args: PowerMonitorProto | RadioProto | IMUProto | Flag | Counter | Processor,
    ) -> None:
        self._log: Logger = logger
        self._sensors: tuple[
            PowerMonitorProto | RadioProto | IMUProto | Flag | Counter | Processor, ...
        ] = args

    def get(self) -> OrderedDict[str, object]:
        """
        Get the state of health
        """
        state: OrderedDict[str, object] = OrderedDict()

        for sensor in self._sensors:
            if isinstance(sensor, Processor):
                name = sensor.__class__.__name__
                state[f"{name}_temperature"] = sensor.temperature
            if isinstance(sensor, Flag):
                flag_class = flag_register_lookup[sensor._index]
                flag_name = register_lookup(flag_class, sensor._bit)
                register_name = register_lookup(Register, sensor._index)
                state[f"{register_name}_{flag_name}_{sensor.__class__.__name__}"] = (
                    sensor.get()
                )
            if isinstance(sensor, Counter):
                register_name = register_lookup(Register, sensor._index)
                state[f"{register_name}_{sensor.__class__.__name__}"] = sensor.get()
            if isinstance(sensor, RadioProto):
                name = sensor.__class__.__name__
                state[f"{name}_modulation"] = sensor.get_modulation().__name__
            if isinstance(sensor, PowerMonitorProto):
                name = sensor.__class__.__name__
                state[f"{name}_current_avg"] = self.avg_readings(sensor.get_current)
                state[f"{name}_bus_voltage_avg"] = self.avg_readings(
                    sensor.get_bus_voltage
                )
                state[f"{name}_shunt_voltage_avg"] = self.avg_readings(
                    sensor.get_shunt_voltage
                )
            if isinstance(sensor, TemperatureSensorProto):
                name = sensor.__class__.__name__
                state[f"{name}_temperature"] = sensor.get_temperature()

        self._log.info("State of Health", state=state)

        return state

    def avg_readings(
        self, func: Callable[..., float | None], num_readings: int = 50
    ) -> float | None:
        """
        Get the average of the readings from a function

        :param func: The function to call
        :param num_readings: The number of readings to take
        :return: The average of the readings
        :rtype: float | None
        """
        readings: float = 0
        for _ in range(num_readings):
            reading = func()
            if reading is None:
                self._log.warning(f"Couldn't acquire {func.__name__}")
                return

            readings += reading
        return readings / num_readings
