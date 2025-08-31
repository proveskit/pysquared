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
        state = self._build_beacon_state()
        beacon_data = json.dumps(state, separators=(",", ":")).encode("utf-8")
        return self._packet_manager.send(beacon_data)

    def _build_beacon_state(self) -> OrderedDict[str, object]:
        """Builds the beacon state dictionary with system info and sensor data.

        Returns:
            OrderedDict containing the beacon state data.
        """
        state: OrderedDict[str, object] = OrderedDict()
        self._add_system_info(state)
        self._add_sensor_data(state)
        return state

    def _add_system_info(self, state: OrderedDict[str, object]) -> None:
        """Adds system information to the beacon state.

        Args:
            state: The state dictionary to update.
        """
        state["name"] = self._name

        now = time.localtime()  # type: ignore # PR: https://github.com/adafruit/circuitpython/pull/10603
        state["time"] = (
            f"{now.tm_year}-{now.tm_mon:02d}-{now.tm_mday:02d} {now.tm_hour:02d}:{now.tm_min:02d}:{now.tm_sec:02d}"  # type: ignore # PR: https://github.com/adafruit/circuitpython/pull/10603
        )

        state["uptime"] = time.time() - self._boot_time

    def _add_sensor_data(self, state: OrderedDict[str, object]) -> None:
        """Adds sensor data to the beacon state.

        Args:
            state: The state dictionary to update.
        """
        for index, sensor in enumerate(self._sensors):
            if isinstance(sensor, Processor):
                self._add_processor_data(state, sensor, index)
            elif isinstance(sensor, Flag):
                self._add_flag_data(state, sensor, index)
            elif isinstance(sensor, Counter):
                self._add_counter_data(state, sensor, index)
            elif isinstance(sensor, RadioProto):
                self._add_radio_data(state, sensor, index)
            elif isinstance(sensor, IMUProto):
                self._add_imu_data(state, sensor, index)
            elif isinstance(sensor, PowerMonitorProto):
                self._add_power_monitor_data(state, sensor, index)
            elif isinstance(sensor, TemperatureSensorProto):
                self._add_temperature_sensor_data(state, sensor, index)

    def _add_processor_data(
        self, state: OrderedDict[str, object], sensor: Processor, index: int
    ) -> None:
        """Adds processor data to the beacon state."""
        sensor_name = sensor.__class__.__name__
        state[f"{sensor_name}_{index}_temperature"] = sensor.temperature

    def _add_flag_data(
        self, state: OrderedDict[str, object], sensor: Flag, index: int
    ) -> None:
        """Adds flag data to the beacon state."""
        state[f"{sensor.get_name()}_{index}"] = sensor.get()

    def _add_counter_data(
        self, state: OrderedDict[str, object], sensor: Counter, index: int
    ) -> None:
        """Adds counter data to the beacon state."""
        state[f"{sensor.get_name()}_{index}"] = sensor.get()

    def _add_radio_data(
        self, state: OrderedDict[str, object], sensor: RadioProto, index: int
    ) -> None:
        """Adds radio data to the beacon state."""
        sensor_name = sensor.__class__.__name__
        state[f"{sensor_name}_{index}_modulation"] = sensor.get_modulation().__name__

    def _add_imu_data(
        self, state: OrderedDict[str, object], sensor: IMUProto, index: int
    ) -> None:
        """Adds IMU data to the beacon state."""
        sensor_name = sensor.__class__.__name__

        self._safe_add_sensor_reading(
            state,
            f"{sensor_name}_{index}_acceleration",
            lambda: sensor.get_acceleration().to_dict(),
            "Error retrieving acceleration",
            sensor_name,
            index,
        )

        self._safe_add_sensor_reading(
            state,
            f"{sensor_name}_{index}_angular_velocity",
            lambda: sensor.get_angular_velocity().to_dict(),
            "Error retrieving angular velocity",
            sensor_name,
            index,
        )

    def _add_power_monitor_data(
        self, state: OrderedDict[str, object], sensor: PowerMonitorProto, index: int
    ) -> None:
        """Adds power monitor data to the beacon state."""
        sensor_name = sensor.__class__.__name__

        self._safe_add_sensor_reading(
            state,
            f"{sensor_name}_{index}_current_avg",
            lambda: avg_readings(sensor.get_current),
            "Error retrieving current",
            sensor_name,
            index,
        )

        self._safe_add_sensor_reading(
            state,
            f"{sensor_name}_{index}_bus_voltage_avg",
            lambda: avg_readings(sensor.get_bus_voltage),
            "Error retrieving bus voltage",
            sensor_name,
            index,
        )

        self._safe_add_sensor_reading(
            state,
            f"{sensor_name}_{index}_shunt_voltage_avg",
            lambda: avg_readings(sensor.get_shunt_voltage),
            "Error retrieving shunt voltage",
            sensor_name,
            index,
        )

    def _add_temperature_sensor_data(
        self,
        state: OrderedDict[str, object],
        sensor: TemperatureSensorProto,
        index: int,
    ) -> None:
        """Adds temperature sensor data to the beacon state."""
        sensor_name = sensor.__class__.__name__

        self._safe_add_sensor_reading(
            state,
            f"{sensor_name}_{index}_temperature",
            lambda: sensor.get_temperature().to_dict(),
            "Error retrieving temperature",
            sensor_name,
            index,
        )

    def _safe_add_sensor_reading(
        self,
        state: OrderedDict[str, object],
        key: str,
        reading_func,
        error_msg: str,
        sensor_name: str,
        index: int,
    ) -> None:
        """Safely adds a sensor reading to the state with error handling.

        Args:
            state: The state dictionary to update.
            key: The key to store the reading under.
            reading_func: Function that returns the sensor reading.
            error_msg: Error message to log if reading fails.
            sensor_name: Name of the sensor for logging.
            index: Index of the sensor for logging.
        """
        try:
            state[key] = reading_func()
        except Exception as e:
            self._log.error(error_msg, e, sensor=sensor_name, index=index)
