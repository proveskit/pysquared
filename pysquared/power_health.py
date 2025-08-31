"""This module provides a PowerHealth class for monitoring the power system.

The PowerHealth class checks the battery voltage and current draw to determine the
overall health of the power system. It returns one of four states: NOMINAL,
DEGRADED, CRITICAL, or UNKNOWN.

**Usage:**
```python
logger = Logger()
config = Config("config.json")
power_monitor = INA219Manager(logger, i2c)
power_health = PowerHealth(logger, config, power_monitor)
health_status = power_health.get()
```
"""

from .config.config import Config
from .logger import Logger
from .protos.power_monitor import PowerMonitorProto
from .sensor_reading.avg import avg_readings


class State:
    """Base class for power health states."""

    pass


class NOMINAL(State):
    """Represents a nominal power health state."""

    pass


class DEGRADED(State):
    """Represents a degraded power health state."""

    pass


class CRITICAL(State):
    """Represents a critical power health state."""

    pass


class UNKNOWN(State):
    """Represents an unknown power health state."""

    pass


class PowerHealth:
    """Monitors the power system and determines its health."""

    def __init__(
        self,
        logger: Logger,
        config: Config,
        power_monitor: PowerMonitorProto,
    ) -> None:
        """Initializes the PowerHealth monitor.

        Args:
            logger: The logger to use.
            config: The configuration to use.
            power_monitor: The power monitor to use.
        """
        self.logger: Logger = logger
        self.config: Config = config
        self._power_monitor: PowerMonitorProto = power_monitor

    def get(self) -> NOMINAL | DEGRADED | CRITICAL | UNKNOWN:
        """Gets the current power health.

        Returns:
            The current power health state.
        """
        try:
            bus_voltage = avg_readings(self._power_monitor.get_bus_voltage)
        except Exception as e:
            self.logger.error("Error retrieving bus voltage", e)
            return UNKNOWN()

        try:
            current = avg_readings(self._power_monitor.get_current)
        except Exception as e:
            self.logger.error("Error retrieving current", e)
            return UNKNOWN()

        if bus_voltage <= self.config.critical_battery_voltage:
            self.logger.warning(
                "Power is CRITICAL",
                voltage=bus_voltage,
                threshold=self.config.critical_battery_voltage,
            )
            return CRITICAL()

        if (
            abs(current - self.config.normal_charge_current)
            > self.config.normal_charge_current
        ):
            self.logger.warning(
                "Power is DEGRADED: Current above threshold",
                current=current,
                threshold=self.config.normal_charge_current,
            )
            return DEGRADED()

        if bus_voltage <= self.config.degraded_battery_voltage:
            self.logger.warning(
                "Power is DEGRADED: Bus voltage below threshold",
                voltage=bus_voltage,
                threshold=self.config.degraded_battery_voltage,
            )
            return DEGRADED()

        self.logger.debug("Power health is NOMINAL")
        return NOMINAL()
