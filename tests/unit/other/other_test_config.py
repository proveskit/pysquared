"""Unit tests for the configuration validation logic.

This module contains unit tests for the configuration validation functions,
ensuring that the configuration data adheres to the defined schema and business
rules. It covers type checking, range validation, and presence of required fields.
"""

import json
from pathlib import Path
from typing import Any, Dict

import pytest

# Schema definition using type hints for documentation
CONFIG_SCHEMA = {
    "cubesat_name": str,
    "last_battery_temp": float,
    "sleep_duration": int,
    "detumble_enable_z": bool,
    "detumble_enable_x": bool,
    "detumble_enable_y": bool,
    "jokes": list,
    "debug": bool,
    "heating": bool,
    "normal_temp": int,
    "normal_battery_temp": int,
    "normal_micro_temp": int,
    "normal_charge_current": float,
    "normal_battery_voltage": float,
    "critical_battery_voltage": float,
    "battery_voltage": float,
    "current_draw": float,
    "reboot_time": int,
    "turbo_clock": bool,
    "radio": dict,
    "super_secret_code": str,
    "repeat_code": str,
}


def validate_config(config: Dict[str, Any]) -> None:
    """Validates config data against schema and business rules.

    Args:
        config: The configuration dictionary to validate.

    Raises:
        ValueError: If a required field is missing, a value is out of range, or a list is empty.
        TypeError: If a field has an incorrect type.
    """
    # Validate field presence and types
    for field, expected_type in CONFIG_SCHEMA.items():
        if field not in config:
            raise ValueError(f"Required field '{field}' is missing")

        value = config[field]
        if isinstance(expected_type, list):
            if not isinstance(value, list):
                raise TypeError(f"Field '{field}' must be a list")
            if not value:  # Check if list is empty
                raise ValueError(f"Field '{field}' cannot be empty")
            if not all(isinstance(item, str) for item in value):
                raise TypeError(f"All items in '{field}' must be strings")
        elif not isinstance(value, expected_type):
            raise TypeError(f"Field '{field}' must be of type {expected_type.__name__}")

    # Validate voltage ranges
    voltage_fields = [
        "battery_voltage",
        "normal_battery_voltage",
        "critical_battery_voltage",
    ]
    for field in voltage_fields:
        value = config[field]
        if not 0 <= value <= 12.0:
            raise ValueError(f"{field} must be between 0V and 12V")

    # Validate current draw
    if config["current_draw"] < 0:
        raise ValueError("Current draw cannot be negative")

    # Validate time values
    time_fields = ["sleep_duration", "reboot_time"]
    for field in time_fields:
        if config[field] <= 0:
            raise ValueError(f"{field} must be positive")

    # Validate radio configuration
    if not isinstance(config["radio"], dict):
        raise TypeError("radio must be a dictionary")

    # Validate basic radio fields
    radio_basic_fields = {
        "transmit_frequency": float,
        "start_time": int,
        "license": str,
    }

    for field, expected_type in radio_basic_fields.items():
        if field not in config["radio"]:
            raise ValueError(f"Required radio field '{field}' is missing")
        if not isinstance(config["radio"][field], expected_type):
            raise TypeError(
                f"Radio field '{field}' must be of type {expected_type.__name__}"
            )

    # Validate FSK config
    if "fsk" not in config["radio"]:
        raise ValueError("Required radio field 'fsk' is missing")
    if not isinstance(config["radio"]["fsk"], dict):
        raise TypeError("radio.fsk must be a dictionary")

    fsk_fields = {
        "broadcast_address": int,
        "node_address": int,
        "modulation_type": int,
    }

    for field, expected_type in fsk_fields.items():
        if field not in config["radio"]["fsk"]:
            raise ValueError(f"Required radio.fsk field '{field}' is missing")
        if not isinstance(config["radio"]["fsk"][field], expected_type):
            raise TypeError(
                f"Radio.fsk field '{field}' must be of type {expected_type.__name__}"
            )

    # Validate LoRa config
    if "lora" not in config["radio"]:
        raise ValueError("Required radio field 'lora' is missing")
    if not isinstance(config["radio"]["lora"], dict):
        raise TypeError("radio.lora must be a dictionary")

    lora_fields = {
        "ack_delay": float,
        "coding_rate": int,
        "cyclic_redundancy_check": bool,
        "spreading_factor": int,
        "transmit_power": int,
    }

    for field, expected_type in lora_fields.items():
        if field not in config["radio"]["lora"]:
            raise ValueError(f"Required radio.lora field '{field}' is missing")
        if not isinstance(config["radio"]["lora"][field], expected_type):
            raise TypeError(
                f"Radio.lora field '{field}' must be of type {expected_type.__name__}"
            )

    # Validate radio config ranges
    if not 0 <= config["radio"]["lora"]["transmit_power"] <= 23:
        raise ValueError("lora.transmit_power must be between 0 and 23")
    if not 400 <= config["radio"]["transmit_frequency"] <= 450:
        raise ValueError("transmit_frequency must be between 400 and 450 MHz")


def load_config(config_path: str) -> dict:
    """Loads and parses the config file.

    Args:
        config_path: The path to the configuration file.

    Returns:
        A dictionary containing the loaded configuration.

    Raises:
        pytest.fail: If the JSON is invalid or the file is not found.
    """
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON in config file: {e}")
    except FileNotFoundError:
        pytest.fail(f"Config file not found at {config_path}")


@pytest.fixture
def config_data():
    """Fixture to load the config data from the default config.json.

    Returns:
        A dictionary containing the loaded configuration data.
    """
    workspace_root = Path(__file__).parent.parent.parent
    config_path = workspace_root / "config.json"
    return load_config(str(config_path))


def test_config_file_exists():
    """Tests that config.json exists.

    This test verifies that the `config.json` file is present in the expected
    location within the project structure.
    """
    workspace_root = Path(__file__).parent.parent.parent
    config_path = workspace_root / "config.json"
    assert config_path.exists(), "config.json file not found"


def test_config_is_valid_json(config_data):
    """Tests that config.json is valid JSON.

    Args:
        config_data: Fixture providing the loaded configuration data.

    This test ensures that the content of `config.json` can be successfully
    parsed as a JSON object.
    """
    assert isinstance(config_data, dict), "Config file is not a valid JSON object"


def test_config_validation(config_data):
    """Tests that config.json matches the expected schema and business rules.

    Args:
        config_data: Fixture providing the loaded configuration data.

    This test calls the `validate_config` function to ensure that the loaded
    configuration adheres to all defined validation rules, including field
    presence, types, and ranges.
    """
    try:
        validate_config(config_data)
    except (ValueError, TypeError) as e:
        pytest.fail(str(e))


def test_field_types(config_data):
    """Tests that all fields have correct types.

    Args:
        config_data: Fixture providing the loaded configuration data.

    This test individually checks the data type of various fields within the
    configuration to ensure they match the expected Python types (string, int,
    float, bool, list, dict).
    """
    # Test string fields
    string_fields = ["cubesat_name", "callsign", "super_secret_code", "repeat_code"]
    for field in string_fields:
        assert isinstance(config_data[field], str), f"{field} must be a string"

    # Test numeric fields
    float_fields = [
        "last_battery_temp",
        "normal_charge_current",
        "normal_battery_voltage",
        "critical_battery_voltage",
        "current_draw",
        "battery_voltage",
    ]
    for field in float_fields:
        assert isinstance(config_data[field], (int, float)), f"{field} must be a number"

    int_fields = [
        "sleep_duration",
        "normal_temp",
        "normal_battery_temp",
        "normal_micro_temp",
        "reboot_time",
    ]
    for field in int_fields:
        assert isinstance(config_data[field], int), f"{field} must be an integer"

    # Test boolean fields
    bool_fields = [
        "detumble_enable_z",
        "detumble_enable_x",
        "detumble_enable_y",
        "debug",
        "heating",
        "turbo_clock",
    ]
    for field in bool_fields:
        assert isinstance(config_data[field], bool), f"{field} must be a boolean"

    # Test list fields
    list_fields = ["jokes"]
    for field in list_fields:
        assert isinstance(config_data[field], list), f"{field} must be a list"
        assert all(isinstance(item, str) for item in config_data[field]), (
            f"All items in {field} must be strings"
        )

    # Test radio config
    assert isinstance(config_data["radio"], dict), "radio must be a dictionary"

    # Test basic radio fields
    radio_basic_fields = {
        "transmit_frequency": float,
        "start_time": int,
    }
    for field, expected_type in radio_basic_fields.items():
        assert isinstance(config_data["radio"][field], expected_type), (
            f"radio.{field} must be a {expected_type.__name__}"
        )

    # Test FSK fields
    assert isinstance(config_data["radio"]["fsk"], dict), (
        "radio.fsk must be a dictionary"
    )
    fsk_fields = {
        "broadcast_address": int,
        "node_address": int,
        "modulation_type": int,
    }
    for field, expected_type in fsk_fields.items():
        assert isinstance(config_data["radio"]["fsk"][field], expected_type), (
            f"radio.fsk.{field} must be a {expected_type.__name__}"
        )

    # Test LoRa fields
    assert isinstance(config_data["radio"]["lora"], dict), (
        "radio.lora must be a dictionary"
    )
    lora_fields = {
        "ack_delay": float,
        "coding_rate": int,
        "cyclic_redundancy_check": bool,
        "spreading_factor": int,
        "transmit_power": int,
    }
    for field, expected_type in lora_fields.items():
        assert isinstance(config_data["radio"]["lora"][field], expected_type), (
            f"radio.lora.{field} must be a {expected_type.__name__}"
        )


def test_voltage_ranges(config_data):
    """Tests that voltage values are within expected ranges.

    Args:
        config_data: Fixture providing the loaded configuration data.

    This test verifies that battery-related voltage values fall within a
    reasonable operational range (5.2V to 8.4V).
    """
    voltage_fields = [
        "battery_voltage",
        "normal_battery_voltage",
        "critical_battery_voltage",
    ]
    for field in voltage_fields:
        value = config_data[field]
        assert 5.2 <= value <= 8.4, f"{field} must be between 5.2V and 8.4V"


def test_time_values(config_data):
    """Tests that time values are positive.

    Args:
        config_data: Fixture providing the loaded configuration data.

    This test ensures that `sleep_duration` and `reboot_time` are positive
    integers, as negative or zero values would be illogical for these settings.
    """
    assert config_data["sleep_duration"] > 0, "sleep_duration must be positive"
    assert config_data["reboot_time"] > 0, "reboot_time must be positive"


def test_current_draw_positive(config_data):
    """Tests that current draw is not negative.

    Args:
        config_data: Fixture providing the loaded configuration data.

    This test verifies that the `current_draw` value is non-negative, as a
    negative current draw would imply an impossible scenario in this context.
    """
    assert config_data["current_draw"] >= 0, "current_draw cannot be negative"


def test_lists_not_empty(config_data):
    """Tests that list fields are not empty.

    Args:
        config_data: Fixture providing the loaded configuration data.

    This test specifically checks that the `jokes` list is not empty and that
    all its elements are strings, ensuring valid content for this field.
    """
    assert len(config_data["jokes"]) > 0, "jokes list cannot be empty"
    assert all(isinstance(joke, str) for joke in config_data["jokes"]), (
        "All jokes must be strings"
    )
