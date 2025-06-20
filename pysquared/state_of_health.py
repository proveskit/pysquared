from typing import Any

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
        *args: PowerMonitorProto | TemperatureSensorProto | Any,
    ) -> None:
        self.logger: Logger = logger
        self.config: Config = config
        self._sensors: tuple[PowerMonitorProto | TemperatureSensorProto | Any, ...] = (
            args
        )

    def get(self) -> NOMINAL | DEGRADED:
        """
        Get the state of health by checking all sensors
        """
        errors: List[str] = []

        for sensor in self._sensors:
            self.logger.debug("Sensor: ", sensor=sensor)
            sensor_errors = self._check_sensor(sensor)
            errors.extend(sensor_errors)

        return self._determine_state(errors)

    def _check_sensor(self, sensor) -> List[str]:
        """
        Check a single sensor and return any errors found
        """
        if isinstance(sensor, PowerMonitorProto):
            return self._check_power_monitor(sensor)
        elif isinstance(sensor, TemperatureSensorProto):
            return self._check_temperature_sensor(sensor)
        elif hasattr(sensor, "temperature"):  # CPU-like object
            return self._check_cpu_sensor(sensor)
        else:
            return []

    def _check_power_monitor(self, sensor: PowerMonitorProto) -> List[str]:
        """
        Check power monitor sensor readings
        """
        errors = []

        # Get average readings
        bus_voltage = self._avg_reading(sensor.get_bus_voltage)
        shunt_voltage = self._avg_reading(sensor.get_shunt_voltage)
        current = self._avg_reading(sensor.get_current)

        # Check current reading
        if current and self._is_out_of_range(
            current, self.config.normal_charge_current
        ):
            errors.append(
                f"Current reading {current} is outside of normal range {self.config.normal_charge_current}"
            )

        # Check bus voltage reading
        if bus_voltage and self._is_out_of_range(
            bus_voltage, self.config.normal_battery_voltage
        ):
            errors.append(
                f"Bus voltage reading {bus_voltage} is outside of normal range {self.config.normal_battery_voltage}"
            )

        # Check shunt voltage reading
        if shunt_voltage and self._is_out_of_range(
            shunt_voltage, self.config.normal_battery_voltage
        ):
            errors.append(
                f"Shunt voltage reading {shunt_voltage} is outside of normal range {self.config.normal_battery_voltage}"
            )

        return errors

    def _check_temperature_sensor(self, sensor: TemperatureSensorProto) -> List[str]:
        """
        Check temperature sensor readings
        """
        temperature = self._avg_reading(sensor.get_temperature)
        self.logger.debug("Temp: ", temperature=temperature)

        if temperature and self._is_out_of_range(temperature, self.config.normal_temp):
            return [
                f"Temperature reading {temperature} is outside of normal range {self.config.normal_temp}"
            ]

        return []

    def _check_cpu_sensor(self, sensor) -> List[str]:
        """
        Check CPU-like sensor readings
        """
        temperature = sensor.temperature
        self.logger.debug("Temp: ", temperature=temperature)

        if temperature and self._is_out_of_range(
            temperature, self.config.normal_micro_temp
        ):
            return [
                f"Processor temperature reading {temperature} is outside of normal range {self.config.normal_micro_temp}"
            ]

        return []

    def _is_out_of_range(
        self, reading: float, normal_value: float, tolerance: float = 10
    ) -> bool:
        """
        Check if a reading is outside the acceptable range

        :param reading: The sensor reading to check
        :param normal_value: The expected normal value
        :param tolerance: The acceptable deviation from normal (default: 10)
        :return: True if reading is out of range, False otherwise
        """
        return abs(reading - normal_value) > tolerance

    def _determine_state(self, errors: List[str]) -> NOMINAL | DEGRADED:
        """
        Determine the final state based on collected errors
        """
        if errors:
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
                return None
            readings += reading
        return readings / num_readings
