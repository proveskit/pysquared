import json
import os
import tempfile

import pytest

from pysquared.config.config import Config


@pytest.fixture(autouse=True)
def cleanup():
    temp_dir = tempfile.mkdtemp()
    file = os.path.join(temp_dir, "config.test.json")

    source_file = f"{os.path.dirname(__file__)}/files/config.test.json"
    with open(source_file, "r") as src, open(file, "w") as dest:
        dest.write(src.read())

    yield file
    os.remove(file)


def test_radio_cfg(cleanup) -> None:
    file = cleanup
    with open(file, "r") as f:
        json_data = json.loads(f.read())

    config = Config(file)

    # Test basic radio config properties
    assert (
        config.radio.transmit_frequency == json_data["radio"]["transmit_frequency"]
    ), "No match for: transmit_frequency"
    assert config.radio.start_time == json_data["radio"]["start_time"], (
        "No match for: start_time"
    )

    # Test FSK config properties
    assert (
        config.radio.fsk.broadcast_address
        == json_data["radio"]["fsk"]["broadcast_address"]
    ), "No match for: fsk.broadcast_address"
    assert config.radio.fsk.node_address == json_data["radio"]["fsk"]["node_address"], (
        "No match for: fsk.node_address"
    )
    assert (
        config.radio.fsk.modulation_type == json_data["radio"]["fsk"]["modulation_type"]
    ), "No match for: fsk.modulation_type"

    # Test LoRa config properties
    assert config.radio.lora.ack_delay == json_data["radio"]["lora"]["ack_delay"], (
        "No match for: lora.ack_delay"
    )
    assert config.radio.lora.coding_rate == json_data["radio"]["lora"]["coding_rate"], (
        "No match for: lora.coding_rate"
    )
    assert (
        config.radio.lora.cyclic_redundancy_check
        == json_data["radio"]["lora"]["cyclic_redundancy_check"]
    ), "No match for: lora.cyclic_redundancy_check"
    assert (
        config.radio.lora.spreading_factor
        == json_data["radio"]["lora"]["spreading_factor"]
    ), "No match for: lora.spreading_factor"
    assert (
        config.radio.lora.transmit_power == json_data["radio"]["lora"]["transmit_power"]
    ), "No match for: lora.transmit_power"


def test_strings(cleanup) -> None:
    file = cleanup
    with open(file, "r") as f:
        json_data = json.loads(f.read())

    config = Config(file)

    assert config.cubesat_name == json_data["cubesat_name"], (
        "No match for: cubesat_name"
    )
    assert config.super_secret_code == json_data["super_secret_code"], (
        "No match for: super_secret_code"
    )
    assert config.repeat_code == json_data["repeat_code"], "No match for: repeat_code"


def test_ints(cleanup) -> None:
    file = cleanup
    with open(file, "r") as f:
        json_data = json.loads(f.read())

    config = Config(file)

    assert config.sleep_duration == json_data["sleep_duration"], (
        "No match for: sleep_duration"
    )
    assert config.normal_temp == json_data["normal_temp"], "No match for: normal_temp"
    assert config.normal_battery_temp == json_data["normal_battery_temp"], (
        "No match for: normal_battery_temp"
    )
    assert config.normal_micro_temp == json_data["normal_micro_temp"], (
        "No match for: normal_micro_temp"
    )
    assert config.reboot_time == json_data["reboot_time"], "No match for: reboot_time"

    assert (
        config.longest_allowable_sleep_time == json_data["longest_allowable_sleep_time"]
    ), "No match for: longest_allowable_sleep_time"


def test_floats(cleanup) -> None:
    file = cleanup
    with open(file, "r") as f:
        json_data = json.loads(f.read())

    config = Config(file)

    assert config.normal_charge_current == json_data["normal_charge_current"], (
        "No match for: normal_charge_current"
    )
    assert config.normal_battery_voltage == json_data["normal_battery_voltage"], (
        "No match for: normal_battery_voltage"
    )
    assert config.degraded_battery_voltage == json_data["degraded_battery_voltage"], (
        "No match for: degraded_battery_voltage"
    )
    assert config.critical_battery_voltage == json_data["critical_battery_voltage"], (
        "No match for: critical_battery_voltage"
    )


def test_bools(cleanup) -> None:
    file = cleanup
    with open(file, "r") as f:
        json_data = json.loads(f.read())

    config = Config(file)

    assert config.detumble_enable_z == json_data["detumble_enable_z"], (
        "No match for: detumble_enable_z"
    )
    assert config.detumble_enable_x == json_data["detumble_enable_x"], (
        "No match for: detumble_enable_x"
    )
    assert config.detumble_enable_y == json_data["detumble_enable_y"], (
        "No match for: detumble_enable_y"
    )
    assert config.debug == json_data["debug"], "No match for: debug"
    assert config.heating == json_data["heating"], "No match for: heating"
    assert config.turbo_clock == json_data["turbo_clock"], "No match for: turbo_clock"


def test_validation_updateable(cleanup) -> None:
    file = cleanup
    config = Config(file)

    # raises KeyError
    with pytest.raises(KeyError):
        config.validate("not_in_config", "trash")

    # config
    try:
        config.validate("cubesat_name", "maia")
    except KeyError as e:
        print(e)

    # fsk
    try:
        config.validate("ack_delay", 1.5)
    except KeyError as e:
        print(e)

    # lora
    try:
        config.validate("node_address", 11)
    except KeyError as e:
        print(e)


def test_validation_type(cleanup) -> None:
    file = cleanup
    config = Config(file)

    # raises TypeError
    with pytest.raises(TypeError):
        config.validate("cubesat_name", 1)

    # config
    try:
        config.validate("cubesat_name", "maia")
    except KeyError as e:
        print(e)


def test_validation_range(cleanup) -> None:
    file = cleanup
    config = Config(file)

    # normal config
    with pytest.raises(ValueError):
        config.validate("cubesat_name", "")
    with pytest.raises(ValueError):
        config.validate("cubesat_name", "more_than_seven")

    # transmit_frequency specific
    with pytest.raises(ValueError):
        config.validate("transmit_frequency", 0.0)
    with pytest.raises(ValueError):
        config.validate("transmit_frequency", 500.0)
    with pytest.raises(ValueError):
        config.validate("transmit_frequency", 916.0)
    try:
        config.validate("transmit_frequency", 436.0)
    except ValueError as e:
        print(e)

    with pytest.raises(ValueError):
        config.validate("cubesat_name", "more_than_10____")

    with pytest.raises(ValueError):
        config.validate("cubesat_name", "more_than_10____")

    # config
    try:
        config.validate("cubesat_name", "accept")
    except ValueError as e:
        print(e)


def test_save_config(cleanup) -> None:
    file = cleanup
    config = Config(file)
    try:
        config._save_config("cubesat_name", "accept")
    except ValueError as e:
        print(e)


def test_update_config(cleanup) -> None:
    file = cleanup
    config = Config(file)

    # config temp
    try:
        config.update_config("cubesat_name", "accept", False)
    except ValueError as e:
        print(e)
    # config permanent
    try:
        config.update_config("cubesat_name", "accept", True)
    except ValueError as e:
        print(e)

    # fsk temp
    try:
        config.update_config("ack_delay", 1.0, False)
    except ValueError as e:
        print(e)
    # fsk permanent
    try:
        config.update_config("ack_delay", 1.0, True)
    except ValueError as e:
        print(e)

    # lora temp
    try:
        config.update_config("broadcast_address", 1, False)
    except ValueError as e:
        print(e)
    # lora permanent
    try:
        config.update_config("broadcast_address", 1, True)
    except ValueError as e:
        print(e)


def test_allowed_values(cleanup) -> None:
    file = cleanup
    config = Config(file)

    with pytest.raises(TypeError):
        config.validate("modulation", "DefinitelyRealModulation")

    config.validate("modulation", "LoRa")
    config.validate("modulation", "FSK")
