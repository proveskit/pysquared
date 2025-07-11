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


class UNKNOWN(State):
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
        self._power_monitor: PowerMonitorProto = power_monitor

    def get(self) -> NOMINAL | DEGRADED | CRITICAL | UNKNOWN:
        """
        Get the power health
        """
        errors: List[str] = []
        self.logger.debug("Power monitor: ", sensor=self._power_monitor)

        # Wrap sensor reading calls in try/catch and handle None values
        try:
            bus_voltage = self._avg_reading(self._power_monitor.get_bus_voltage)
            if bus_voltage is None:
                self.logger.warning(
                    "Power monitor failed to provide bus voltage reading"
                )
                return UNKNOWN()

            current = self._avg_reading(self._power_monitor.get_current)
            if current is None:
                self.logger.warning("Power monitor failed to provide current reading")
                return UNKNOWN()

        except Exception as e:
            self.logger.error("Exception occurred while reading from power monitor", e)
            return UNKNOWN()

        # Critical check first - if battery voltage is below critical threshold
        if bus_voltage <= self.config.critical_battery_voltage:
            self.logger.warning(
                f"CRITICAL: Battery voltage {bus_voltage:.1f}V is at or below critical threshold {self.config.critical_battery_voltage}V"
            )
            return CRITICAL()

        # Check current deviation from normal
        if (
            abs(current - self.config.normal_charge_current)
            > self.config.normal_charge_current
        ):
            errors.append(
                f"Current reading {current:.1f} is outside of normal range {self.config.normal_charge_current}"
            )

        # Check if bus voltage is below degraded threshold
        if bus_voltage <= self.config.degraded_battery_voltage:
            errors.append(
                f"Bus voltage reading {bus_voltage:.1f}V is at or below degraded threshold {self.config.degraded_battery_voltage}V"
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
                func_name = getattr(func, "__name__", "unknown_function")
                self.logger.warning(f"Couldn't get reading from {func_name}")
                return
            readings += reading
        return readings / num_readings
