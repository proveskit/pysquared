# type-hinting only
try:
    from typing import Literal
except ImportError:
    pass


class RadioConfig:
    def __init__(self, radio_dict: dict) -> None:
        self.license: str = radio_dict["license"]
        self.modulation: str = radio_dict["modulation"]
        self.sender_id: int = radio_dict["sender_id"]
        self.receiver_id: int = radio_dict["receiver_id"]
        self.transmit_frequency: int = radio_dict["transmit_frequency"]
        self.start_time: int = radio_dict["start_time"]
        self.fsk: FSKConfig = FSKConfig(radio_dict["fsk"])
        self.lora: LORAConfig = LORAConfig(radio_dict["lora"])

        self.RADIO_SCHEMA = {
            "license": {"type": str},
            "modulation": {"type": str},
            "receiver_id": {"type": int, "min": 0, "max": 255},
            "sender_id": {"type": int, "min": 0, "max": 255},
            "start_time": {"type": int, "min": 0, "max": 80000},
            "transmit_frequency": {
                "type": (int, float),
                "min0": 435,
                "max0": 438.0,
                "min1": 915.0,
                "max1": 915.0,
            },
        }

    def validate(self, key: str, value) -> None:
        if key in self.RADIO_SCHEMA:
            schema = self.RADIO_SCHEMA[key]
        elif key in self.fsk.FSK_SCHEMA:
            schema = self.fsk.FSK_SCHEMA[key]
        elif key in self.lora.LORA_SCHEMA:
            schema = self.lora.LORA_SCHEMA[key]
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


class FSKConfig:
    def __init__(self, fsk_dict: dict) -> None:
        self.broadcast_address: int = fsk_dict["broadcast_address"]
        self.node_address: int = fsk_dict["node_address"]
        self.modulation_type: int = fsk_dict["modulation_type"]

        self.FSK_SCHEMA = {
            "broadcast_address": {"type": int, "min": 0, "max": 255},
            "node_address": {"type": int, "min": 0, "max": 255},
            "modulation_type": {"type": int, "min": 0, "max": 1},
        }


class LORAConfig:
    def __init__(self, lora_dict: dict) -> None:
        self.ack_delay: float = lora_dict["ack_delay"]
        self.coding_rate: int = lora_dict["coding_rate"]
        self.cyclic_redundancy_check: bool = lora_dict["cyclic_redundancy_check"]
        self.spreading_factor: Literal[6, 7, 8, 9, 10, 11, 12] = lora_dict[
            "spreading_factor"
        ]
        self.transmit_power: int = lora_dict["transmit_power"]

        self.LORA_SCHEMA = {
            "ack_delay": {"type": float, "min": 0.0, "max": 2.0},
            "coding_rate": {"type": int, "min": 4, "max": 8},
            "cyclic_redundancy_check": {"type": bool, "allowed_values": [True, False]},
            "max_output": {"type": bool, "allowed_values": [True, False]},
            "spreading_factor": {"type": int, "min": 6, "max": 12},
            "transmit_power": {"type": int, "min": 5, "max": 23},
        }
