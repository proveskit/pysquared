import json
import os

from pysquared.config.config import Config

os.path.dirname(__file__)
file = f"{os.path.dirname(__file__)}/files/config.test.json"


def test_radio_cfg() -> None:
    with open(file, "r") as f:
        json_data = json.loads(f.read())

    config = Config(file)

    # Test basic radio config properties
    assert (
        config.radio.sender_id == json_data["radio"]["sender_id"]
    ), "No match for: sender_id"
    assert (
        config.radio.receiver_id == json_data["radio"]["receiver_id"]
    ), "No match for: receiver_id"
    assert (
        config.radio.transmit_frequency == json_data["radio"]["transmit_frequency"]
    ), "No match for: transmit_frequency"
    assert (
        config.radio.start_time == json_data["radio"]["start_time"]
    ), "No match for: start_time"

    # Test FSK config properties
    assert (
        config.radio.fsk.broadcast_address
        == json_data["radio"]["fsk"]["broadcast_address"]
    ), "No match for: fsk.broadcast_address"
    assert (
        config.radio.fsk.node_address == json_data["radio"]["fsk"]["node_address"]
    ), "No match for: fsk.node_address"
    assert (
        config.radio.fsk.modulation_type == json_data["radio"]["fsk"]["modulation_type"]
    ), "No match for: fsk.modulation_type"

    # Test LoRa config properties
    assert (
        config.radio.lora.ack_delay == json_data["radio"]["lora"]["ack_delay"]
    ), "No match for: lora.ack_delay"
    assert (
        config.radio.lora.coding_rate == json_data["radio"]["lora"]["coding_rate"]
    ), "No match for: lora.coding_rate"
    assert (
        config.radio.lora.cyclic_redundancy_check
        == json_data["radio"]["lora"]["cyclic_redundancy_check"]
    ), "No match for: lora.cyclic_redundancy_check"
    assert (
        config.radio.lora.max_output == json_data["radio"]["lora"]["max_output"]
    ), "No match for: lora.max_output"
    assert (
        config.radio.lora.spreading_factor
        == json_data["radio"]["lora"]["spreading_factor"]
    ), "No match for: lora.spreading_factor"
    assert (
        config.radio.lora.transmit_power == json_data["radio"]["lora"]["transmit_power"]
    ), "No match for: lora.transmit_power"


def test_strings() -> None:
    with open(file, "r") as f:
        json_data = json.loads(f.read())

    config = Config(file)

    assert (
        config.cubesat_name == json_data["cubesat_name"]
    ), "No match for: cubesat_name"
    assert (
        config.super_secret_code == json_data["super_secret_code"]
    ), "No match for: super_secret_code"
    assert config.repeat_code == json_data["repeat_code"], "No match for: repeat_code"


def test_ints() -> None:
    with open(file, "r") as f:
        json_data = json.loads(f.read())

    config = Config(file)

    assert (
        config.sleep_duration == json_data["sleep_duration"]
    ), "No match for: sleep_duration"
    assert config.normal_temp == json_data["normal_temp"], "No match for: normal_temp"
    assert (
        config.normal_battery_temp == json_data["normal_battery_temp"]
    ), "No match for: normal_battery_temp"
    assert (
        config.normal_micro_temp == json_data["normal_micro_temp"]
    ), "No match for: normal_micro_temp"
    assert config.reboot_time == json_data["reboot_time"], "No match for: reboot_time"


def test_floats() -> None:
    with open(file, "r") as f:
        json_data = json.loads(f.read())

    config = Config(file)

    assert (
        config.last_battery_temp == json_data["last_battery_temp"]
    ), "No match for: last_battery_temp"
    assert (
        config.normal_charge_current == json_data["normal_charge_current"]
    ), "No match for: normal_charge_current"
    assert (
        config.normal_battery_voltage == json_data["normal_battery_voltage"]
    ), "No match for: normal_battery_voltage"
    assert (
        config.critical_battery_voltage == json_data["critical_battery_voltage"]
    ), "No match for: critical_battery_voltage"
    assert (
        config.current_draw == json_data["current_draw"]
    ), "No match for: current_draw"


def test_bools() -> None:
    with open(file, "r") as f:
        json_data = json.loads(f.read())

    config = Config(file)

    assert (
        config.detumble_enable_z == json_data["detumble_enable_z"]
    ), "No match for: detumble_enable_z"
    assert (
        config.detumble_enable_x == json_data["detumble_enable_x"]
    ), "No match for: detumble_enable_x"
    assert (
        config.detumble_enable_y == json_data["detumble_enable_y"]
    ), "No match for: detumble_enable_y"
    assert config.debug == json_data["debug"], "No match for: debug"
    assert config.heating == json_data["heating"], "No match for: heating"
    assert config.is_licensed == json_data["is_licensed"], "No match for: is_licensed"
    assert config.turbo_clock == json_data["turbo_clock"], "No match for: turbo_clock"
