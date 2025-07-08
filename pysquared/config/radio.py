"""This module provides classes for handling and validating radio configuration parameters, including support for both FSK and LoRa modulation schemes.

Classes:
    RadioConfig: Handles top-level radio configuration and validation.
    FSKConfig: Handles FSK-specific configuration and validation.
    LORAConfig: Handles LoRa-specific configuration and validation.
"""

# type-hinting only
try:
    from typing import Literal
except ImportError:
    pass


class RadioConfig:
    """
    Handles radio configuration and validation for PySquared.

    Attributes:
        license (str): The radio license identifier.
        modulation (Literal["LoRa", "FSK"]): The modulation type.
        transmit_frequency (int): The transmission frequency in MHz.
        start_time (int): The radio start time in seconds.
        fsk (FSKConfig): FSK-specific configuration handler.
        lora (LORAConfig): LoRa-specific configuration handler.
        RADIO_SCHEMA (dict): Validation schema for radio configuration keys.

    Methods:
        validate(key, value):
            Validates a radio configuration value against its schema.
    """

    def __init__(self, radio_dict: dict) -> None:
        """
        Initializes the RadioConfig object with values from a dictionary.

        Args:
            radio_dict (dict): Dictionary containing radio configuration values.
        """

        self.license: str = radio_dict["license"]
        self.modulation: Literal["LoRa", "FSK"] = radio_dict["modulation"]
        self.transmit_frequency: int = radio_dict["transmit_frequency"]
        self.start_time: int = radio_dict["start_time"]
        self.fsk: FSKConfig = FSKConfig(radio_dict["fsk"])
        self.lora: LORAConfig = LORAConfig(radio_dict["lora"])

        self.RADIO_SCHEMA = {
            "license": {"type": str},
            "modulation": {"type": str, "allowed_values": ["LoRa", "FSK"]},
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
        """
        Validates a radio configuration value against its schema.

        Args:
            key (str): The configuration key to validate.
            value: The value to validate.

        Raises:
            KeyError: If the key is not found in any schema.
            TypeError: If the value is not of the expected type or not allowed.
            ValueError: If the value is out of the allowed range.
        """

        if key in self.RADIO_SCHEMA:
            schema = self.RADIO_SCHEMA[key]
        elif key in self.fsk.FSK_SCHEMA:
            schema = self.fsk.FSK_SCHEMA[key]
        elif key in self.lora.LORA_SCHEMA:
            schema = self.lora.LORA_SCHEMA[key]
        else:
            raise KeyError

        if "allowed_values" in schema:
            if value not in schema["allowed_values"]:
                raise TypeError

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
    """
    Handles FSK-specific radio configuration and validation.

    Attributes:
        broadcast_address (int): Broadcast address for FSK.
        node_address (int): Node address for FSK.
        modulation_type (int): Modulation type for FSK.
        FSK_SCHEMA (dict): Validation schema for FSK configuration keys.
    """

    def __init__(self, fsk_dict: dict) -> None:
        """
        Initializes the FSKConfig object with values from a dictionary.

        Args:
            fsk_dict (dict): Dictionary containing FSK configuration values.
        """

        self.broadcast_address: int = fsk_dict["broadcast_address"]
        self.node_address: int = fsk_dict["node_address"]
        self.modulation_type: int = fsk_dict["modulation_type"]

        self.FSK_SCHEMA = {
            "broadcast_address": {"type": int, "min": 0, "max": 255},
            "node_address": {"type": int, "min": 0, "max": 255},
            "modulation_type": {"type": int, "min": 0, "max": 1},
        }


class LORAConfig:
    """
    Handles LoRa-specific radio configuration and validation.

    Attributes:
        ack_delay (float): Acknowledgement delay in seconds.
        coding_rate (int): Coding rate for LoRa.
        cyclic_redundancy_check (bool): CRC enabled flag.
        spreading_factor (Literal[6, 7, 8, 9, 10, 11, 12]): LoRa spreading factor.
        transmit_power (int): Transmit power in dBm.
        LORA_SCHEMA (dict): Validation schema for LoRa configuration keys.
    """

    def __init__(self, lora_dict: dict) -> None:
        """
        Initializes the LORAConfig object with values from a dictionary.

        Args:
            lora_dict (dict): Dictionary containing LoRa configuration values.
        """

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
