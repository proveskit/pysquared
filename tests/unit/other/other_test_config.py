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
    "joke_reply": list,
}


def validate_config(config: Dict[str, Any]) -> None:
    """Validate config data against schema and business rules."""
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
        "sender_id": int,
        "receiver_id": int,
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
        "max_output": bool,
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
    """Load and parse the config file."""
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON in config file: {e}")
    except FileNotFoundError:
        pytest.fail(f"Config file not found at {config_path}")


@pytest.fixture
def config_data():
    """Fixture to load the config data."""
    workspace_root = Path(__file__).parent.parent.parent
    config_path = workspace_root / "config.json"
    return load_config(str(config_path))


def test_config_file_exists():
    """Test that config.json exists."""
    workspace_root = Path(__file__).parent.parent.parent
    config_path = workspace_root / "config.json"
    assert config_path.exists(), "config.json file not found"


def test_config_is_valid_json(config_data):
    """Test that config.json is valid JSON."""
    assert isinstance(config_data, dict), "Config file is not a valid JSON object"


def test_config_validation(config_data):
    """Test that config.json matches the expected schema and business rules."""
    try:
        validate_config(config_data)
    except (ValueError, TypeError) as e:
        pytest.fail(str(e))


def test_field_types(config_data):
    """Test that all fields have correct types."""
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
    list_fields = ["jokes", "joke_reply"]
    for field in list_fields:
        assert isinstance(config_data[field], list), f"{field} must be a list"
        assert all(
            isinstance(item, str) for item in config_data[field]
        ), f"All items in {field} must be strings"

    # Test radio config
    assert isinstance(config_data["radio"], dict), "radio must be a dictionary"

    # Test basic radio fields
    radio_basic_fields = {
        "sender_id": int,
        "receiver_id": int,
        "transmit_frequency": float,
        "start_time": int,
    }
    for field, expected_type in radio_basic_fields.items():
        assert isinstance(
            config_data["radio"][field], expected_type
        ), f"radio.{field} must be a {expected_type.__name__}"

    # Test FSK fields
    assert isinstance(
        config_data["radio"]["fsk"], dict
    ), "radio.fsk must be a dictionary"
    fsk_fields = {
        "broadcast_address": int,
        "node_address": int,
        "modulation_type": int,
    }
    for field, expected_type in fsk_fields.items():
        assert isinstance(
            config_data["radio"]["fsk"][field], expected_type
        ), f"radio.fsk.{field} must be a {expected_type.__name__}"

    # Test LoRa fields
    assert isinstance(
        config_data["radio"]["lora"], dict
    ), "radio.lora must be a dictionary"
    lora_fields = {
        "ack_delay": float,
        "coding_rate": int,
        "cyclic_redundancy_check": bool,
        "max_output": bool,
        "spreading_factor": int,
        "transmit_power": int,
    }
    for field, expected_type in lora_fields.items():
        assert isinstance(
            config_data["radio"]["lora"][field], expected_type
        ), f"radio.lora.{field} must be a {expected_type.__name__}"


def test_voltage_ranges(config_data):
    """Test that voltage values are within expected ranges."""
    voltage_fields = [
        "battery_voltage",
        "normal_battery_voltage",
        "critical_battery_voltage",
    ]
    for field in voltage_fields:
        value = config_data[field]
        assert 5.2 <= value <= 8.4, f"{field} must be between 5.2V and 8.4V"


def test_time_values(config_data):
    """Test that time values are positive."""
    assert config_data["sleep_duration"] > 0, "sleep_duration must be positive"
    assert config_data["reboot_time"] > 0, "reboot_time must be positive"


def test_current_draw_positive(config_data):
    """Test that current draw is not negative."""
    assert config_data["current_draw"] >= 0, "current_draw cannot be negative"


def test_lists_not_empty(config_data):
    """Test that list fields are not empty."""
    assert len(config_data["jokes"]) > 0, "jokes list cannot be empty"
    assert len(config_data["joke_reply"]) > 0, "joke_reply list cannot be empty"
    assert all(
        isinstance(joke, str) for joke in config_data["jokes"]
    ), "All jokes must be strings"
    assert all(
        isinstance(reply, str) for reply in config_data["joke_reply"]
    ), "All joke replies must be strings"
