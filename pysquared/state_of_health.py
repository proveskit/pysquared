from pysquared.config.config import Config
from pysquared.logger import Logger
from pysquared.protos.power_monitor import PowerMonitorProto

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


class CRITICAL(State):
    pass


class PowerHealth:
    def __init__(
        self,
        logger: Logger,
        config: Config,
        power_monitor: PowerMonitorProto,
    ) -> None:
        self.logger: Logger = logger
        self.config: Config = config
        self._sensor: PowerMonitorProto = power_monitor

    def get(self) -> NOMINAL | DEGRADED | CRITICAL:
        """
        Get the power health
        """
        errors: List[str] = []
        self.logger.debug("Power monitor: ", sensor=self._sensor)

        if isinstance(self._sensor, PowerMonitorProto):
            bus_voltage = self._avg_reading(self._sensor.get_bus_voltage)
            current = self._avg_reading(self._sensor.get_current)

            # Critical check first - if battery voltage is below critical threshold
            if bus_voltage and bus_voltage <= self.config.critical_battery_voltage:
                self.logger.warning(
                    f"CRITICAL: Battery voltage {bus_voltage}V is at or below critical threshold {self.config.critical_battery_voltage}V"
                )
                return CRITICAL()

            # Check current deviation from normal
            if (
                current
                and abs(current - self.config.normal_charge_current)
                > self.config.normal_charge_current
            ):
                errors.append(
                    f"Current reading {current} is outside of normal range {self.config.normal_charge_current}"
                )

            # Check bus voltage deviation from normal
            voltage_tolerance = (
                abs(
                    self.config.normal_battery_voltage
                    - self.config.critical_battery_voltage
                )
                / 2
            )
            if (
                bus_voltage
                and abs(bus_voltage - self.config.normal_battery_voltage)
                > voltage_tolerance
            ):
                errors.append(
                    f"Bus voltage reading {bus_voltage}V is outside of normal range {self.config.normal_battery_voltage}V ±{voltage_tolerance}V"
                )

        if len(errors) > 0:
            self.logger.info(
                "Power health is NOMINAL with minor deviations", errors=errors
            )
            return DEGRADED()
        else:
            self.logger.info("Power health is NOMINAL")
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
