from microcontroller import Processor

from pysquared.config.config import Config
from pysquared.logger import Logger
from pysquared.protos.power_monitor import PowerMonitorProto
from pysquared.protos.temperature_sensor import TemperatureSensorProto

try:
    from typing import Callable, List

except Exception:
    pass


class State:
    pass


class NOMINAL(State):
    pass


class DEGRADED(State):
    pass


class StateOfHealth:
    def __init__(
        self,
        logger: Logger,
        config: Config,
        *args: PowerMonitorProto | TemperatureSensorProto | Processor,
    ) -> None:
        self.logger: Logger = logger
        self.config: Config = config
        self._sensors: tuple[
            PowerMonitorProto | TemperatureSensorProto | Processor, ...
        ] = args

    def get(self) -> NOMINAL | DEGRADED:
        """
        Get the state of health
        """
        errors: List[str] = []
        for sensor in self._sensors:
            if isinstance(sensor, PowerMonitorProto):
                bus_voltage = self._avg_reading(sensor.get_bus_voltage)
                shunt_voltage = self._avg_reading(sensor.get_shunt_voltage)
                current = self._avg_reading(sensor.get_current)

                # range is hardcoded for now
                if current and abs(current - self.config.normal_charge_current) > 10:
                    errors.append(
                        f"Current reading {current} is outside of normal range {self.config.normal_charge_current}"
                    )
                if (
                    bus_voltage
                    and abs(bus_voltage - self.config.normal_battery_voltage) > 10
                ):
                    errors.append(
                        f"Bus voltage reading {bus_voltage} is outside of normal range {self.config.normal_battery_voltage}"
                    )
                if (
                    shunt_voltage
                    and abs(shunt_voltage - self.config.normal_battery_voltage) > 10
                ):
                    errors.append(
                        f"Shunt voltage reading {shunt_voltage} is outside of normal range {self.config.normal_battery_voltage}"
                    )
            elif isinstance(sensor, TemperatureSensorProto):
                temperature = self._avg_reading(sensor.get_temperature)
                self.logger.debug("Temp: ", temperature=temperature)
                if temperature and abs(temperature - self.config.normal_temp) > 10:
                    errors.append(
                        f"Temperature reading {temperature} is outside of normal range {self.config.normal_temp}"
                    )
            elif isinstance(sensor, Processor):
                temperature = sensor.temperature
                self.logger.debug("Temp: ", temperature=temperature)
                if (
                    temperature
                    and abs(temperature - self.config.normal_micro_temp) > 10
                ):
                    errors.append(
                        f"Processor temperature reading {temperature} is outside of normal range {self.config.normal_micro_temp}"
                    )

        if len(errors) > 0:
            self.logger.warning("State of health is DEGRADED", errors=errors)
            return DEGRADED()
        else:
            self.logger.info("State of health is NOMINAL")
            return NOMINAL()

    def _avg_reading(
        self, func: Callable[..., float | None], num_readings: int = 50
    ) -> float | None:
        """
        Get average reading from a sensor

        :param func: function to call
        :param num_readings: number of readings to take
        :return: average of the readings
        """
        readings: float = 0.0
        for _ in range(num_readings):
            reading = func()
            if reading is None:
                self.logger.warning(f"Couldn't get reading from {func.__name__}")
                return
            readings += reading
        return readings / num_readings
