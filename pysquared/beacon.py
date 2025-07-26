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

try:
    from typing import Callable, OrderedDict
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
                state[f"{sensor_name}_{index}_acceleration"] = sensor.get_acceleration()
                state[f"{sensor_name}_{index}_gyroscope"] = sensor.get_gyro_data()
            if isinstance(sensor, PowerMonitorProto):
                sensor_name: str = sensor.__class__.__name__
                state[f"{sensor_name}_{index}_current_avg"] = self.avg_readings(
                    sensor.get_current
                )
                state[f"{sensor_name}_{index}_bus_voltage_avg"] = self.avg_readings(
                    sensor.get_bus_voltage
                )
                state[f"{sensor_name}_{index}_shunt_voltage_avg"] = self.avg_readings(
                    sensor.get_shunt_voltage
                )
            if isinstance(sensor, TemperatureSensorProto):
                sensor_name = sensor.__class__.__name__
                reading = sensor.get_temperature()
                state[f"{sensor_name}_{index}_temperature"] = reading.value
                state[f"{sensor_name}_{index}_temperature_timestamp"] = (
                    reading.timestamp
                )

        b = json.dumps(state, separators=(",", ":")).encode("utf-8")
        return self._packet_manager.send(b)

    def avg_readings(
        self, func: Callable[..., float | None], num_readings: int = 50
    ) -> float | None:
        """Gets the average of the readings from a function.

        Args:
            func: The function to call.
            num_readings: The number of readings to take.

        Returns:
            The average of the readings, or None if the readings could not be taken.
        """
        readings: float = 0
        for _ in range(num_readings):
            reading = func()
            if reading is None:
                self._log.warning(f"Couldn't acquire {func.__name__}")
                return

            readings += reading
        return readings / num_readings
