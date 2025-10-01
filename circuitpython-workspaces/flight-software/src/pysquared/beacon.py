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

from microcontroller import Processor

from .binary_encoder import BinaryDecoder, BinaryEncoder
from .hardware.radio.packetizer.packet_manager import PacketManager
from .logger import Logger
from .nvm.counter import Counter
from .nvm.flag import Flag
from .protos.imu import IMUProto
from .protos.magnetometer import MagnetometerProto
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
        | MagnetometerProto
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
            | MagnetometerProto
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
        state = self._build_state()
        # Use binary encoding for efficiency
        b = self._encode_binary_state(state)
        return self._packet_manager.send(b)

    def _encode_binary_state(self, state: OrderedDict[str, object]) -> bytes:
        """Encode the state dictionary using binary encoding for efficiency.

        Uses explicit encoding based on known beacon data structure for safety and performance.

        Args:
            state: The state dictionary to encode

        Returns:
            Binary encoded data
        """
        encoder = BinaryEncoder()

        for key, value in state.items():
            self._encode_known_value(encoder, key, value)

        return encoder.to_bytes()

    def _encode_known_value(
        self, encoder: BinaryEncoder, key: str, value: object
    ) -> None:
        """Encode a value based on its actual type.

        This method uses direct type checking for cleaner and more reliable encoding
        without relying on key name patterns.

        Args:
            encoder: The binary encoder to add data to
            key: The key name for the value
            value: The value to encode
        """
        if isinstance(value, dict):
            self._encode_sensor_dict(encoder, key, value)
        elif isinstance(value, (list, tuple)):
            if len(value) == 3 and all(isinstance(v, (int, float)) for v in value):
                # Handle 3D vectors (acceleration, gyroscope) by splitting into components
                for i, v in enumerate(value):
                    encoder.add_float(f"{key}_{i}", float(v))
            else:
                # Non-numeric or non-3D arrays as strings
                encoder.add_string(key, str(value))
        elif isinstance(value, bool):
            encoder.add_int(key, int(value))
        elif isinstance(value, int):
            encoder.add_int(key, value)
        elif isinstance(value, float):
            encoder.add_float(key, value)
        else:
            # Fallback for all other types (strings, etc.)
            encoder.add_string(key, str(value))

    def _safe_float_convert(self, value: object) -> float:
        """Safely convert a value to float with proper type checking.

        Args:
            value: The value to convert to float

        Returns:
            Float representation of the value

        Raises:
            ValueError: If the value cannot be converted to float
        """
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            return float(value)
        else:
            raise ValueError(f"Cannot convert {type(value).__name__} to float: {value}")

    def _encode_sensor_dict(
        self, encoder: BinaryEncoder, key: str, sensor_data: dict
    ) -> None:
        """Encode sensor data dictionary with known structure.

        Handles sensor readings that come from to_dict() methods with known structure
        like {timestamp: float, value: float|list}.

        Args:
            encoder: The binary encoder to add data to
            key: The base key name
            sensor_data: Dictionary containing sensor readings
        """
        for dict_key, dict_value in sensor_data.items():
            full_key = f"{key}_{dict_key}"
            if dict_key == "timestamp":
                encoder.add_float(full_key, self._safe_float_convert(dict_value))
            elif isinstance(dict_value, (list, tuple)) and len(dict_value) == 3:
                # Handle 3D vectors (acceleration, gyroscope)
                for i, v in enumerate(dict_value):
                    encoder.add_float(f"{full_key}_{i}", self._safe_float_convert(v))
            elif isinstance(dict_value, (int, float)):
                encoder.add_float(full_key, float(dict_value))
            else:
                encoder.add_string(full_key, str(dict_value))

    def _build_state(self) -> OrderedDict[str, object]:
        """Build the beacon state dictionary from sensors.

        Returns:
            OrderedDict containing all beacon data
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
            elif isinstance(sensor, MagnetometerProto):
                self._add_magnetometer_data(state, sensor, index)
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

    def _add_magnetometer_data(
        self, state: OrderedDict[str, object], sensor: MagnetometerProto, index: int
    ) -> None:
        """Adds magnetometer data to the beacon state."""
        sensor_name = sensor.__class__.__name__

        self._safe_add_sensor_reading(
            state,
            f"{sensor_name}_{index}_magnetic_field",
            lambda: sensor.get_magnetic_field().to_dict(),
            "Error retrieving magnetic field",
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

    def send_json(self) -> bool:
        """Sends the beacon using JSON encoding (legacy method).

        Returns:
            True if the beacon was sent successfully, False otherwise.
        """
        state = self._build_state()
        b = json.dumps(state, separators=(",", ":")).encode("utf-8")
        return self._packet_manager.send(b)

    @staticmethod
    def decode_binary_beacon(data: bytes, key_map: dict | None = None) -> dict:
        """Decode binary beacon data received from another satellite.

        Args:
            data: Binary encoded beacon data
            key_map: Optional key mapping for decoding (hash -> key name)

        Returns:
            Dictionary containing decoded beacon data
        """
        decoder = BinaryDecoder(data, key_map)
        return decoder.get_all()

    def generate_key_mapping(self) -> dict:
        """Create a key mapping for this beacon's data structure.

        This method generates a template beacon packet and returns the key mapping
        that can be used to decode binary beacon data with the same structure.

        Returns:
            Dictionary mapping key hashes to key names
        """
        # Create a template state to get the key structure
        state = self._build_template_state()

        # Encode to get key mapping
        encoder = BinaryEncoder()
        for key, value in state.items():
            if isinstance(value, str):
                encoder.add_string(key, value)
            elif isinstance(value, float):
                encoder.add_float(key, value)
            elif isinstance(value, int):
                encoder.add_int(key, value)
            elif isinstance(value, bool):
                encoder.add_int(key, int(value), size=1)

        # Generate the binary data to populate key map
        encoder.to_bytes()
        return encoder.get_key_map()

    def _build_template_state(self) -> OrderedDict[str, object]:
        """Build a template state dictionary for key mapping.

        Returns:
            OrderedDict containing template beacon data with the same structure
        """
        state: OrderedDict[str, object] = OrderedDict()
        self._add_template_system_info(state)
        self._add_template_sensor_data(state)
        return state

    def _add_template_system_info(self, state: OrderedDict[str, object]) -> None:
        """Add template system information to the state dictionary.

        Args:
            state: The state dictionary to update
        """
        state["name"] = self._name
        state["time"] = "template"
        state["uptime"] = 0.0

    def _add_template_sensor_data(self, state: OrderedDict[str, object]) -> None:
        """Add template sensor data to the state dictionary.

        This method adds template data for each sensor type to ensure consistent
        structure even when sensors fail during actual data collection.

        Args:
            state: The state dictionary to update
        """
        for index, sensor in enumerate(self._sensors):
            self._add_template_for_sensor(state, sensor, index)

    def _add_template_for_sensor(
        self, state: OrderedDict[str, object], sensor, index: int
    ) -> None:
        """Add template data for a specific sensor.

        Args:
            state: The state dictionary to update
            sensor: The sensor instance
            index: The sensor index
        """
        if isinstance(sensor, Processor):
            sensor_name = sensor.__class__.__name__
            state[f"{sensor_name}_{index}_temperature"] = 0.0
        elif isinstance(sensor, Flag):
            state[f"{sensor.get_name()}_{index}"] = False
        elif isinstance(sensor, Counter):
            state[f"{sensor.get_name()}_{index}"] = 0
        elif isinstance(sensor, RadioProto):
            sensor_name = sensor.__class__.__name__
            state[f"{sensor_name}_{index}_modulation"] = "template"
        elif isinstance(sensor, IMUProto):
            sensor_name = sensor.__class__.__name__
            # Add template data for all IMU fields that would be created
            state[f"{sensor_name}_{index}_acceleration_timestamp"] = 0.0
            state[f"{sensor_name}_{index}_angular_velocity_timestamp"] = 0.0
            for i in range(3):
                state[f"{sensor_name}_{index}_acceleration_value_{i}"] = 0.0
                state[f"{sensor_name}_{index}_angular_velocity_value_{i}"] = 0.0
        elif isinstance(sensor, MagnetometerProto):
            sensor_name = sensor.__class__.__name__
            # Add template data for all magnetometer fields that would be created
            state[f"{sensor_name}_{index}_magnetic_field_timestamp"] = 0.0
            for i in range(3):
                state[f"{sensor_name}_{index}_magnetic_field_value_{i}"] = 0.0
        elif isinstance(sensor, PowerMonitorProto):
            sensor_name = sensor.__class__.__name__
            state[f"{sensor_name}_{index}_current_avg"] = 0.0
            state[f"{sensor_name}_{index}_bus_voltage_avg"] = 0.0
            state[f"{sensor_name}_{index}_shunt_voltage_avg"] = 0.0
        elif isinstance(sensor, TemperatureSensorProto):
            sensor_name = sensor.__class__.__name__
            state[f"{sensor_name}_{index}_temperature_timestamp"] = 0.0
            state[f"{sensor_name}_{index}_temperature_value"] = 0.0
