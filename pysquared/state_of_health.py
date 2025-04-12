from collections import OrderedDict

from pysquared.functions import functions
from pysquared.logger import Logger
from pysquared.protos.imu import IMUProto
from pysquared.protos.power_monitor import PowerMonitorProto
from pysquared.protos.radio import RadioProto
from pysquared.satellite import Satellite

import microcontroller

try:
    from typing import Any, OrderedDict
except Exception:
    pass


class StateOfHealth:
    def __init__(
        self,
        c: Satellite,
        logger: Logger,
        battery_power_monitor: PowerMonitorProto,
        solar_power_monitor: PowerMonitorProto,
        radio_manager: RadioProto,
        imu_manager: IMUProto,
    ) -> None:
        self.c: Satellite = c
        self.logger: Logger = logger
        self.battery_power_monitor: PowerMonitorProto = battery_power_monitor
        self.solar_power_monitor: PowerMonitorProto = solar_power_monitor
        self.radio_manager: RadioProto = radio_manager
        self.imu_manager: IMUProto = imu_manager

        self.state: OrderedDict[str, Any] = OrderedDict(
            [
                # init all values in ordered dict to None
                ("system_voltage", None),
                ("system_current", None),
                ("solar_voltage", None),
                ("solar_current", None),
                ("battery_voltage", None),
                ("radio_temperature", None),
                ("radio_modulation", None),
                ("microcontroller_temperature", None),
                ("internal_temperature", None),
                ("error_count", None),
                ("power_mode", None),
                ("uptime", None),
                ("boot_count", None),
                ("burned_flag", None),
                ("brownout_flag", None),
                ("fsk_flag", None),
            ]
        )

    def update(self):
        """
        Update the state of health
        """
        try:
            self.state["system_voltage"] = self.system_voltage()
            self.state["system_current"] = self.current_draw()
            self.state["solar_voltage"] = self.solar_voltage()
            self.state["solar_current"] = self.charge_current()
            self.state["battery_voltage"] = self.battery_voltage()
            self.state["radio_temperature"] = self.radio_manager.get_temperature()
            self.state["radio_modulation"] = self.radio_manager.get_modulation()
            self.state["microcontroller_temperature"] = microcontroller.cpu.temperature
            self.state["internal_temperature"] = self.imu_manager.get_temperature()
            self.state["error_count"] = self.logger.get_error_count()
            self.state["power_mode"] = self.c.power_mode
            self.state["uptime"] = self.c.get_system_uptime
            self.state["boot_count"] = self.c.boot_count.get()
            self.state["burned_flag"] = self.c.f_burned.get()
            self.state["brownout_flag"] = self.c.f_brownout.get()

        except Exception as e:
            self.logger.error("Couldn't acquire data for state of health", err=e)

        self.logger.info("State of Health", state=self.state)

    def system_voltage(self) -> float | None:
        """
        Get the system voltage

        :return: The system voltage in volts
        :rtype: float | None

        """
        voltage: float = 0
        try:
            for _ in range(50):
                voltage += (
                    self.battery_power_monitor.get_bus_voltage()
                    + self.battery_power_monitor.get_shunt_voltage()
                )
            return voltage / 50
        except Exception as e:
            self.logger.error("Couldn't acquire system voltage", err=e)

    def battery_voltage(self) -> float | None:
        """
        Get the battery voltage

        :return: The battery voltage in volts
        :rtype: float | None

        """
        voltage: float = 0
        try:
            for _ in range(50):
                voltage += self.battery_power_monitor.get_bus_voltage()
            return voltage / 50 + 0.2  # volts and correction factor
        except Exception as e:
            self.logger.error("Couldn't acquire battery voltage", err=e)

    def current_draw(self) -> float | None:
        """
        Get the current draw

        :return: The current draw in amps
        :rtype: float | None

        """
        current: float = 0
        try:
            for _ in range(50):
                current += self.battery_power_monitor.get_current()
            return current / 50
        except Exception as e:
            self.logger.error("Couldn't acquire current draw", err=e)

    def charge_current(self) -> float | None:
        """
        Get the charge current

        :return: The charge current in amps
        :rtype: float | None

        """
        current: float = 0
        try:
            for _ in range(50):
                current += self.solar_power_monitor.get_current()
            return current / 50
        except Exception as e:
            self.logger.error("Couldn't acquire charge current", err=e)

    def solar_voltage(self) -> float | None:
        """
        Get the solar voltage

        :return: The solar voltage in volts
        :rtype: float | None

        """
        voltage: float = 0
        try:
            for _ in range(50):
                voltage += self.solar_power_monitor.get_bus_voltage()
            return voltage / 50
        except Exception as e:
            self.logger.error("Couldn't acquire solar voltage", err=e)
