"""
Class for encapsulating config.json. The goal is to
distribute these values across the files & variables
that use them. Instantiation happens in main.

Also it allow values to be set temporarily or permanently using the
Attempting to follow the FPrime model.
"""

import json

from .radio import RadioConfig


class Config:
    def __init__(self, config_path: str) -> None:
        self.temp_config_file = "tests/unit/files/config.test.json"
        # parses json & assigns data to variables
        with open(config_path, "r") as f:
            json_data = json.loads(f.read())

        self.radio: RadioConfig = RadioConfig(json_data["radio"])
        self.cubesat_name: str = json_data["cubesat_name"]
        self.sleep_duration: int = json_data["sleep_duration"]
        self.detumble_enable_z: bool = json_data["detumble_enable_z"]
        self.detumble_enable_x: bool = json_data["detumble_enable_x"]
        self.detumble_enable_y: bool = json_data["detumble_enable_y"]
        self.jokes: list[str] = json_data["jokes"]
        self.debug: bool = json_data["debug"]
        self.heating: bool = json_data["heating"]
        self.normal_temp: int = json_data["normal_temp"]
        self.normal_battery_temp: int = json_data["normal_battery_temp"]
        self.normal_micro_temp: int = json_data["normal_micro_temp"]
        self.normal_charge_current: float = json_data["normal_charge_current"]
        self.normal_battery_voltage: float = json_data["normal_battery_voltage"]
        self.critical_battery_voltage: float = json_data["critical_battery_voltage"]
        self.reboot_time: int = json_data["reboot_time"]
        self.turbo_clock: bool = json_data["turbo_clock"]
        self.super_secret_code: str = json_data["super_secret_code"]
        self.repeat_code: str = json_data["repeat_code"]
        self.joke_reply: list[str] = json_data["joke_reply"]

        self.CONFIG_SCHEMA = {
            "cubesat_name": {"type": str, "min_length": 1, "max_length": 10},
            "super_secret_code": {"type": bytes, "min": 1, "max": 24},
            "repeat_code": {"type": bytes, "min": 1, "max": 4},
            "normal_charge_current": {"type": float, "min": 0.0, "max": 2000.0},
            "normal_battery_voltage": {"type": float, "min": 6.0, "max": 8.4},
            "critical_battery_voltage": {"type": float, "min": 5.4, "max": 7.2},
            "sleep_duration": {"type": int, "min": 1, "max": 86400},
            "normal_temp": {"type": int, "min": 5, "max": 40},
            "normal_battery_temp": {"type": int, "min": 1, "max": 35},
            "normal_micro_temp": {"type": int, "min": 1, "max": 50},
            "reboot_time": {"type": int, "min": 3600, "max": 604800},
            "detumble_enable_z": {"type": bool, "allowed_values": [True, False]},
            "detumble_enable_x": {"type": bool, "allowed_values": [True, False]},
            "detumble_enable_y": {"type": bool, "allowed_values": [True, False]},
            "debug": {"type": bool, "allowed_values": [True, False]},
            "heating": {"type": bool, "allowed_values": [True, False]},
            "turbo_clock": {"type": bool, "allowed_values": [True, False]},
        }

        self.RADIO_SCHEMA = {
            "license": {"type": bool, "allowed_values": [True, False]},
            "receiver_id": {"type": int, "min": 0, "max": 255},
            "sender_id": {"type": int, "min": 0, "max": 255},
            "start_time": {"type": int, "min": 0, "max": 80000},
            "transmit_frequency": {
                "type": float,
                "min0": 435,
                "max0": 438.0,
                "min1": 915.0,
                "max1": 915.0,
            },
        }

        self.FSK_SCHEMA = {
            "ack_delay": {"type": float, "min": 0.0, "max": 2.0},
            "coding_rate": {"type": int, "min": 4, "max": 8},
            "cyclic_redundancy_check": {"type": bool, "allowed_values": [True, False]},
            "max_output": {"type": bool, "allowed_values": [True, False]},
            "spreading_factor": {"type": int, "min": 6, "max": 12},
            "transmit_power": {"type": int, "min": 5, "max": 23},
        }

        self.LORA_SCHEMA = {
            "broadcast_address": {"type": int, "min": 0, "max": 255},
            "node_address": {"type": int, "min": 0, "max": 255},
            "modulation_type": {"type": int, "min": 0, "max": 1},
        }

    # validates values from input
    def validate(self, key: str, value) -> None:
        # first checks if key is actually part of config/radio dict
        if key in self.CONFIG_SCHEMA:
            schema = self.CONFIG_SCHEMA[key]

        elif key in self.RADIO_SCHEMA:
            schema = self.RADIO_SCHEMA[key]

        elif key in self.FSK_SCHEMA:
            schema = self.FSK_SCHEMA[key]

        elif key in self.LORA_SCHEMA:
            schema = self.LORA_SCHEMA[key]

        else:
            raise KeyError

        expected_type = schema["type"]

        # checks value is of same type; also covers bools
        if not isinstance(value, expected_type):
            raise TypeError

        # checks int, float, and bytes range
        if isinstance(value, (int, float, bytes)):
            if "min" in schema and value < schema["min"]:
                raise ValueError
            if "max" in schema and value > schema["max"]:
                raise ValueError

            # specific to transmit_frequency
            if key == "transmit_frequency":
                if "min0" in schema and value < schema["min0"]:
                    raise ValueError
                if "max1" in schema and value > schema["max1"]:
                    raise ValueError
                if (
                    "max0" in schema
                    and value > schema["max0"]
                    and "min1" in schema
                    and value < schema["min1"]
                ):
                    raise ValueError

        # checks string range
        else:
            # isinstance(value, str):
            if "min_length" in schema and len(value) < schema["min_length"]:
                raise ValueError
            if "max_length" in schema and len(value) > schema["max_length"]:
                raise ValueError

    # permanently updates values
    def save_config(self, key: str, value) -> None:
        with open(self.temp_config_file, "r") as f:
            json_data = json.loads(f.read())

        json_data[key] = value

        with open(self.temp_config_file, "w") as f:
            f.write(json.dumps(json_data))

    # handles temp or permanent updates
    def update_config(self, key: str, value, temporary: bool) -> None:
        # validates key and value and should raise error if any
        self.validate(key, value)

        if key in self.CONFIG_SCHEMA:
            # if permanent, saves to config
            if not temporary:
                self.save_config(key, value)
            # updates RAM
            setattr(self, key, value)
        elif key in self.RADIO_SCHEMA:
            # if permanent, saves to config
            if not temporary:
                with open(self.temp_config_file, "r") as f:
                    json_data = json.loads(f.read())
                json_data["radio"][key] = value
                with open(self.temp_config_file, "w") as f:
                    f.write(json.dumps(json_data))
            # updates RAM
            setattr(self.radio, key, value)
        elif key in self.FSK_SCHEMA:
            # if permanent, saves to config
            if not temporary:
                with open(self.temp_config_file, "r") as f:
                    json_data = json.loads(f.read())
                json_data["radio"]["fsk"][key] = value
                with open(self.temp_config_file, "w") as f:
                    f.write(json.dumps(json_data))
            # updates RAM
            setattr(self.radio.fsk, key, value)
        else:
            # key is in self.LORA_SCHEMA
            # if permanent, saves to config
            if not temporary:
                with open(self.temp_config_file, "r") as f:
                    json_data = json.loads(f.read())
                json_data["radio"]["lora"][key] = value
                with open(self.temp_config_file, "w") as f:
                    f.write(json.dumps(json_data))
            # updates RAM
            setattr(self.radio.lora, key, value)
