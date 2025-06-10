"""
Class for encapsulating config.json. The goal is to
distribute these values across the files & variables
that use them. Instantiation happens in main.

Also it allow values to be set temporarily or permanently using the
update_config method. Validation occurs before the update.

It is assumed the key and value to update are not empty when the
funciton is called. Also, it's important not to use the same key for
different values in the config file.
"""

import json

from .radio import RadioConfig


class Config:
    def __init__(self, config_path: str) -> None:
        self.config_file = config_path
        # parses json & assigns data to variables
        with open(self.config_file, "r") as f:
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
        self.longest_allowable_sleep_time: int = json_data[
            "longest_allowable_sleep_time"
        ]

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
            "detumble_enable_z": {"type": bool},
            "detumble_enable_x": {"type": bool},
            "detumble_enable_y": {"type": bool},
            "debug": {"type": bool},
            "heating": {"type": bool},
            "turbo_clock": {"type": bool},
        }

    # validates values from input
    def validate(self, key: str, value) -> None:
        if key in self.CONFIG_SCHEMA:
            schema = self.CONFIG_SCHEMA[key]
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

            # checks string range
            else:
                if "min_length" in schema and len(value) < schema["min_length"]:
                    raise ValueError
                if "max_length" in schema and len(value) > schema["max_length"]:
                    raise ValueError
        else:
            # Delegate radio-related validation to RadioConfig
            self.radio.validate(key, value)

    # permanently updates values
    def _save_config(self, key: str, value) -> None:
        with open(self.config_file, "r") as f:
            json_data = json.loads(f.read())

        json_data[key] = value

        with open(self.config_file, "w") as f:
            f.write(json.dumps(json_data))

    # handles temp or permanent updates
    def update_config(self, key: str, value, temporary: bool) -> None:
        # validates key and value and should raise error if any
        if key in self.CONFIG_SCHEMA:
            self.validate(key, value)
            # if permanent, saves to config
            if not temporary:
                self._save_config(key, value)
            # updates RAM
            setattr(self, key, value)
        else:
            # Delegate radio-related validation to RadioConfig
            self.radio.validate(key, value)
            # if permanent, saves to config
            if not temporary:
                with open(self.config_file, "r") as f:
                    json_data = json.loads(f.read())
                if key in self.radio.RADIO_SCHEMA:
                    json_data["radio"][key] = value
                elif key in self.radio.fsk.FSK_SCHEMA:
                    json_data["radio"]["fsk"][key] = value
                else:  # key is in self.radio.lora.LORA_SCHEMA
                    json_data["radio"]["lora"][key] = value
                with open(self.config_file, "w") as f:
                    f.write(json.dumps(json_data))
            # updates RAM
            if key in self.radio.RADIO_SCHEMA:
                setattr(self.radio, key, value)
            elif key in self.radio.fsk.FSK_SCHEMA:
                setattr(self.radio.fsk, key, value)
            else:  # key is in self.radio.lora.LORA_SCHEMA
                setattr(self.radio.lora, key, value)
