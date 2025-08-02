"""This module provides a Beacon class for sending periodic status messages.

The Beacon class collects data from various sensors and system components, formats it
as a JSON string, and sends it using a provided packet manager. This is typically
used for sending telemetry or health information from a satellite or remote device.

**Usage:**
```python
logger = Logger()
packet_manager = PacketManager(logger, radio)
boot_time = time.time()
beacon = Beacon(logger, "MySat", packet_manager, boot_time, imu, power_monitor)
beacon.send()
```
"""

import json
import time
from collections import OrderedDict

try:
    from mocks.circuitpython.microcontroller import Processor
except ImportError:
    from microcontroller import Processor

from .hardware.radio.packetizer.packet_manager import PacketManager
from .logger import Logger
from .nvm.counter import Counter
from .nvm.flag import Flag
from .protos.imu import IMUProto
from .protos.power_monitor import PowerMonitorProto
from .protos.radio import RadioProto
from .protos.temperature_sensor import TemperatureSensorProto
from .sensor_reading.avg import avg_readings

try:
    from typing import OrderedDict
except Exception:
    pass


class Beacon:
    """A beacon for sending status messages."""

    def __init__(
        self,
        logger: Logger,
        name: str,
        packet_manager: PacketManager,
        boot_time: float,
        *args: PowerMonitorProto
        | RadioProto
        | IMUProto
        | TemperatureSensorProto
        | Flag
        | Counter
        | Processor,
    ) -> None:
        """Initializes the Beacon.

        Args:
            logger: The logger to use.
            name: The name of the beacon.
            packet_manager: The packet manager to use for sending the beacon.
            boot_time: The time the system booted.
            *args: A list of sensors and other components to include in the beacon.
        """
        self._log: Logger = logger
        self._name: str = name
        self._packet_manager: PacketManager = packet_manager
        self._boot_time: float = boot_time
        self._sensors: tuple[
            PowerMonitorProto
            | RadioProto
            | IMUProto
            | TemperatureSensorProto
            | Flag
            | Counter
            | Processor,
            ...,
        ] = args

    def send(self) -> bool:
        """Sends the beacon.

        Returns:
            True if the beacon was sent successfully, False otherwise.
        """
        state: OrderedDict[str, object] = OrderedDict()
        state["name"] = self._name

        # Warning: CircuitPython does not support time.gmtime(), when testing this code it will use your local timezone
        now = time.localtime()
        state["time"] = (
            f"{now.tm_year}-{now.tm_mon:02d}-{now.tm_mday:02d} {now.tm_hour:02d}:{now.tm_min:02d}:{now.tm_sec:02d}"
        )

        state["uptime"] = time.time() - self._boot_time

        for index, sensor in enumerate(self._sensors):
            if isinstance(sensor, Processor):
                sensor_name = sensor.__class__.__name__
                state[f"{sensor_name}_{index}_temperature"] = sensor.temperature
            if isinstance(sensor, Flag):
                state[f"{sensor.get_name()}_{index}"] = sensor.get()
            if isinstance(sensor, Counter):
                state[f"{sensor.get_name()}_{index}"] = sensor.get()
            if isinstance(sensor, RadioProto):
                sensor_name = sensor.__class__.__name__
                state[f"{sensor_name}_{index}_modulation"] = (
                    sensor.get_modulation().__name__
                )
            if isinstance(sensor, IMUProto):
                sensor_name: str = sensor.__class__.__name__
                try:
                    state[f"{sensor_name}_{index}_acceleration"] = (
                        sensor.get_acceleration()
                    )
                except Exception as e:
                    self._log.error(
                        "Error retrieving acceleration",
                        e,
                        sensor=sensor_name,
                        index=index,
                    )

                try:
                    state[f"{sensor_name}_{index}_gyroscope"] = sensor.get_gyro_data()
                except Exception as e:
                    self._log.error(
                        "Error retrieving gyroscope data",
                        e,
                        sensor=sensor_name,
                        index=index,
                    )
            if isinstance(sensor, PowerMonitorProto):
                sensor_name: str = sensor.__class__.__name__
                try:
                    state[f"{sensor_name}_{index}_current_avg"] = avg_readings(
                        sensor.get_current
                    )
                except Exception as e:
                    self._log.error(
                        "Error retrieving current", e, sensor=sensor_name, index=index
                    )

                try:
                    state[f"{sensor_name}_{index}_bus_voltage_avg"] = avg_readings(
                        sensor.get_bus_voltage
                    )
                except Exception as e:
                    self._log.error(
                        "Error retrieving bus voltage",
                        e,
                        sensor=sensor_name,
                        index=index,
                    )

                try:
                    state[f"{sensor_name}_{index}_shunt_voltage_avg"] = avg_readings(
                        sensor.get_shunt_voltage
                    )
                except Exception as e:
                    self._log.error(
                        "Error retrieving shunt voltage",
                        e,
                        sensor=sensor_name,
                        index=index,
                    )
            if isinstance(sensor, TemperatureSensorProto):
                sensor_name = sensor.__class__.__name__
                try:
                    reading = sensor.get_temperature()
                    state[f"{sensor_name}_{index}_temperature"] = reading.to_dict()
                except Exception as e:
                    self._log.error(
                        "Error retrieving temperature",
                        e,
                        sensor=sensor_name,
                        index=index,
                    )

        b = json.dumps(state, separators=(",", ":")).encode("utf-8")
        return self._packet_manager.send(b)
