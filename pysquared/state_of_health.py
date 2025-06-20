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
        Check power monitor sensor readings against CONFIG_SCHEMA bounds
        """
        errors = []

        # Get average readings
        bus_voltage = self._avg_reading(sensor.get_bus_voltage)
        shunt_voltage = self._avg_reading(sensor.get_shunt_voltage)
        current = self._avg_reading(sensor.get_current)

        # Check current reading against normal_charge_current bounds (0.0-2000.0)
        if current is not None:
            current_errors = self._check_against_schema_bounds(
                current, "normal_charge_current", "Current reading"
            )
            errors.extend(current_errors)

        # Check bus voltage reading against normal_battery_voltage bounds (6.0-8.4)
        if bus_voltage is not None:
            bus_voltage_errors = self._check_against_schema_bounds(
                bus_voltage, "normal_battery_voltage", "Bus voltage reading"
            )
            errors.extend(bus_voltage_errors)

        # Check shunt voltage reading against normal_battery_voltage bounds (6.0-8.4)
        if shunt_voltage is not None:
            shunt_voltage_errors = self._check_against_schema_bounds(
                shunt_voltage, "normal_battery_voltage", "Shunt voltage reading"
            )
            errors.extend(shunt_voltage_errors)

        return errors

    def _check_temperature_sensor(self, sensor: TemperatureSensorProto) -> List[str]:
        """
        Check temperature sensor readings against CONFIG_SCHEMA bounds
        """
        temperature = self._avg_reading(sensor.get_temperature)
        self.logger.debug("Temp: ", temperature=temperature)

        if temperature is not None:
            return self._check_against_schema_bounds(
                temperature, "normal_temp", "Temperature reading"
            )

        return []

    def _check_cpu_sensor(self, sensor) -> List[str]:
        """
        Check CPU-like sensor readings against CONFIG_SCHEMA bounds
        """
        temperature = sensor.temperature
        self.logger.debug("Temp: ", temperature=temperature)

        if temperature is not None:
            return self._check_against_schema_bounds(
                temperature, "normal_micro_temp", "Processor temperature reading"
            )

        return []

    def _check_against_schema_bounds(
        self, reading: float, config_key: str, reading_name: str
    ) -> List[str]:
        """
        Check if a reading is within the bounds defined in CONFIG_SCHEMA

        :param reading: The sensor reading to check
        :param config_key: The config key to check against (e.g., 'normal_temp')
        :param reading_name: Human-readable name for the reading type
        :return: List of error messages if reading is out of bounds
        """
        errors = []
        if reading is None:
            return errors
        if config_key not in self.config.CONFIG_SCHEMA:
            self.logger.warning(f"Config key '{config_key}' not found in CONFIG_SCHEMA")
            return errors
        schema = self.config.CONFIG_SCHEMA[config_key]
        config_value = getattr(self.config, config_key, None)
        if config_value is None:
            self.logger.warning(f"Config value for '{config_key}' is None")
            return errors
        # Check against min bound
        if "min" in schema and reading < schema["min"]:
            errors.append(
                f"{reading_name} {reading} is below minimum bound {schema['min']} for {config_key}"
            )
        # Check against max bound
        if "max" in schema and reading > schema["max"]:
            errors.append(
                f"{reading_name} {reading} is above maximum bound {schema['max']} for {config_key}"
            )
        return errors

    def _is_out_of_range(
        self, reading: float, normal_value: float, tolerance: float = 10
    ) -> bool:
        """
        Check if a reading is outside the acceptable range
        DEPRECATED: Use _check_against_schema_bounds instead

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
