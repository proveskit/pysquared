"""Unit tests for the CommandDataHandler class.

This module contains unit tests for the `CommandDataHandler` class, which is
responsible for processing commands received by the satellite. The tests cover
initialization, command parsing, and execution of various commands.
"""

import hmac
import json
from unittest.mock import MagicMock, patch

import pytest
from pysquared.cdh import CommandDataHandler
from pysquared.config.config import Config
from pysquared.hardware.radio.packetizer.packet_manager import PacketManager
from pysquared.logger import Logger
from pysquared.nvm.counter import Counter16


@pytest.fixture
def mock_logger() -> Logger:
    """Mocks the Logger class."""
    return MagicMock(spec=Logger)


@pytest.fixture
def mock_packet_manager() -> PacketManager:
    """Mocks the PacketManager class."""
    return MagicMock(spec=PacketManager)


@pytest.fixture
def mock_config() -> Config:
    """Mocks the Config class."""
    config = MagicMock(spec=Config)
    config.super_secret_code = "test_password"
    config.cubesat_name = "test_satellite"
    config.hmac_secret = "test_hmac_secret"
    config.jokes = ["Why did the satellite cross the orbit? To get to the other side!"]
    return config


@pytest.fixture
def mock_counter16() -> Counter16:
    """Mocks the Counter16 class."""
    counter = MagicMock(spec=Counter16)
    counter.get.return_value = 0  # Default to 0
    return counter


@pytest.fixture
def cdh(
    mock_logger, mock_config, mock_packet_manager, mock_counter16
) -> CommandDataHandler:
    """Provides a CommandDataHandler instance for testing."""
    return CommandDataHandler(
        logger=mock_logger,
        config=mock_config,
        packet_manager=mock_packet_manager,
        last_command_counter=mock_counter16,
        hmac_class=hmac.new,
    )


def test_cdh_init(mock_logger, mock_config, mock_packet_manager, mock_counter16):
    """Tests CommandDataHandler initialization.

    Args:
        mock_logger: Mocked Logger instance.
        mock_config: Mocked Config instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_counter16: Mocked Counter16 instance.
    """
    cdh = CommandDataHandler(
        mock_logger, mock_config, mock_packet_manager, mock_counter16
    )

    assert cdh._log is mock_logger
    assert cdh._config is mock_config
    assert cdh._packet_manager is mock_packet_manager
    assert cdh._last_command_counter is mock_counter16


def test_listen_for_commands_no_message(cdh, mock_packet_manager):
    """Tests listen_for_commands when no message is received.

    Args:
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
    """
    mock_packet_manager.listen.return_value = None

    cdh.listen_for_commands(30)

    mock_packet_manager.listen.assert_called_once_with(30)
    # If no message received, function should simply return


def test_listen_for_commands_missing_hmac(cdh, mock_packet_manager, mock_logger):
    """Tests listen_for_commands with missing HMAC/counter.

    Args:
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_logger: Mocked Logger instance.
    """
    # Create a message without HMAC or counter (old password-based)
    message = {"password": "wrong_password", "command": "send_joke", "args": []}
    mock_packet_manager.listen.return_value = json.dumps(message).encode("utf-8")

    cdh.listen_for_commands(30)

    mock_packet_manager.listen.assert_called_once_with(30)
    mock_logger.debug.assert_any_call("Missing HMAC or counter in message", msg=message)


def test_listen_for_commands_missing_hmac_name_check(
    cdh, mock_packet_manager, mock_logger
):
    """Tests listen_for_commands with missing HMAC (satellite name irrelevant without HMAC).

    Args:
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_logger: Mocked Logger instance.
    """
    # Create a message without HMAC
    message = {"password": "test_password", "name": "wrong_name", "args": []}
    mock_packet_manager.listen.return_value = json.dumps(message).encode("utf-8")

    cdh.listen_for_commands(30)

    mock_packet_manager.listen.assert_called_once_with(30)
    # Should reject due to missing HMAC, not name mismatch
    mock_logger.debug.assert_any_call("Missing HMAC or counter in message", msg=message)


def test_listen_for_commands_missing_command_no_hmac(
    cdh, mock_packet_manager, mock_logger
):
    """Tests listen_for_commands with missing HMAC.

    Args:
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_logger: Mocked Logger instance.
    """
    # Create a message without HMAC
    message = {"password": "test_password", "name": "test_satellite", "args": []}
    mock_packet_manager.listen.return_value = json.dumps(message).encode("utf-8")

    cdh.listen_for_commands(30)

    mock_packet_manager.listen.assert_called_once_with(30)
    # Should reject due to missing HMAC
    mock_logger.debug.assert_any_call("Missing HMAC or counter in message", msg=message)


def test_listen_for_commands_nonlist_args_no_hmac(
    cdh, mock_packet_manager, mock_logger
):
    """Tests listen_for_commands with missing HMAC.

    Args:
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_logger: Mocked Logger instance.
    """
    # Create a message without HMAC
    message = {
        "password": "test_password",
        "name": "test_satellite",
        "command": "send_joke",
        "args": "not_a_list",
    }
    mock_packet_manager.listen.return_value = json.dumps(message).encode("utf-8")

    cdh.listen_for_commands(30)

    mock_packet_manager.listen.assert_called_once_with(30)
    # Should reject due to missing HMAC
    mock_logger.debug.assert_any_call("Missing HMAC or counter in message", msg=message)


def test_listen_for_commands_invalid_json(cdh, mock_packet_manager, mock_logger):
    """Tests listen_for_commands with invalid JSON.

    Args:
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_logger: Mocked Logger instance.
    """
    message = b"this is not valid json"
    mock_packet_manager.listen.return_value = message

    cdh.listen_for_commands(30)

    mock_packet_manager.listen.assert_called_once_with(30)
    mock_logger.error.assert_called_once()
    assert mock_logger.error.call_args[0][0] == "Failed to process command message"


@patch("random.choice")
def test_send_joke(mock_random_choice, cdh, mock_packet_manager, mock_config):
    """Tests the send_joke method.

    Args:
        mock_random_choice: Mocked random.choice function.
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_config: Mocked Config instance.
    """
    mock_random_choice.return_value = mock_config.jokes[0]

    cdh.send_joke()

    mock_random_choice.assert_called_once_with(mock_config.jokes)
    mock_packet_manager.send.assert_called_once_with(
        mock_config.jokes[0].encode("utf-8")
    )


def test_change_radio_modulation_success(cdh, mock_config, mock_logger):
    """Tests change_radio_modulation with valid modulation value.

    Args:
        cdh: CommandDataHandler instance.
        mock_config: Mocked Config instance.
        mock_logger: Mocked Logger instance.
    """
    modulation = ["FSK"]

    cdh.change_radio_modulation(modulation)

    mock_config.update_config.assert_called_once_with(
        "modulation", modulation[0], temporary=False
    )
    mock_logger.info.assert_called_once()


def test_change_radio_modulation_failure(
    cdh, mock_config, mock_logger, mock_packet_manager
):
    """Tests change_radio_modulation with an error case.

    Args:
        cdh: CommandDataHandler instance.
        mock_config: Mocked Config instance.
        mock_logger: Mocked Logger instance.
        mock_packet_manager: Mocked PacketManager instance.
    """
    modulation = ["INVALID"]
    mock_config.update_config.side_effect = ValueError("Invalid modulation")

    cdh.change_radio_modulation(modulation)

    mock_logger.error.assert_called_once()
    mock_packet_manager.send.assert_called_once_with(
        "Failed to change radio modulation: Invalid modulation".encode("utf-8")
    )


def test_change_radio_modulation_no_modulation(cdh, mock_logger, mock_packet_manager):
    """Tests change_radio_modulation when no modulation is specified.

    Args:
        cdh: CommandDataHandler instance.
        mock_logger: Mocked Logger instance.
        mock_packet_manager: Mocked PacketManager instance.
    """
    # Call the method with an empty list
    cdh.change_radio_modulation([])

    # Verify warning was logged
    mock_logger.warning.assert_called_once_with("No modulation specified")

    # Verify error message was sent
    mock_packet_manager.send.assert_called_once()

    # Extract the bytes that were sent
    sent_bytes = mock_packet_manager.send.call_args[0][0]
    expected_message = "No modulation specified. Please provide a modulation type."
    assert sent_bytes.decode("utf-8") == expected_message


@patch("pysquared.cdh.microcontroller")
def test_reset(mock_microcontroller, cdh, mock_logger):
    """Tests the reset method.

    Args:
        mock_microcontroller: Mocked microcontroller module.
        cdh: CommandDataHandler instance.
        mock_logger: Mocked Logger instance.
    """
    mock_microcontroller.reset = MagicMock()
    mock_microcontroller.on_next_reset = MagicMock()
    mock_microcontroller.RunMode = MagicMock()
    mock_microcontroller.RunMode.NORMAL = MagicMock()

    cdh.reset()

    mock_microcontroller.on_next_reset.assert_called_once_with(
        mock_microcontroller.RunMode.NORMAL
    )
    mock_microcontroller.reset.assert_called_once()
    mock_logger.info.assert_called_once()


@patch("time.sleep")
@patch("pysquared.cdh.microcontroller")
def test_listen_for_commands_reset(
    mock_microcontroller, mock_sleep, cdh, mock_packet_manager
):
    """Tests listen_for_commands with reset command.

    Args:
        mock_microcontroller: Mocked microcontroller module.
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_counter16: Mocked Counter16 instance.
    """
    # Set up mocked attributes
    mock_microcontroller.reset = MagicMock()
    mock_microcontroller.on_next_reset = MagicMock()

    counter = 1
    message_dict = {
        "name": "test_satellite",
        "command": "reset",
        "args": [],
        "counter": counter,
    }
    message_str = json.dumps(message_dict, separators=(",", ":"))
    hmac_value = cdh._hmac_authenticator.generate_hmac(message_str, counter)
    message_dict["hmac"] = hmac_value

    mock_packet_manager.listen.return_value = json.dumps(message_dict).encode("utf-8")

    cdh.listen_for_commands(30)

    mock_microcontroller.on_next_reset.assert_called_once_with(
        mock_microcontroller.RunMode.NORMAL
    )
    mock_microcontroller.reset.assert_called_once()


@patch("time.sleep")
@patch("random.choice")
def test_listen_for_commands_send_joke(
    mock_random_choice,
    mock_sleep,
    cdh,
    mock_packet_manager,
    mock_config,
    mock_counter16,
):
    """Tests listen_for_commands with send_joke command.

    Args:
        mock_random_choice: Mocked random.choice function.
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_config: Mocked Config instance.
        mock_counter16: Mocked Counter16 instance.
    """
    counter = 1
    message_dict = {
        "name": "test_satellite",
        "command": "send_joke",
        "args": [],
        "counter": counter,
    }
    message_str = json.dumps(message_dict, separators=(",", ":"))
    hmac_value = cdh._hmac_authenticator.generate_hmac(message_str, counter)
    message_dict["hmac"] = hmac_value

    mock_packet_manager.listen.return_value = json.dumps(message_dict).encode("utf-8")
    mock_random_choice.return_value = mock_config.jokes[0]

    cdh.listen_for_commands(30)

    mock_packet_manager.send.assert_called_once_with(
        mock_config.jokes[0].encode("utf-8")
    )


@patch("time.sleep")
def test_listen_for_commands_change_radio_modulation(
    mock_sleep, cdh, mock_packet_manager, mock_config, mock_counter16
):
    """Tests listen_for_commands with change_radio_modulation command.

    Args:
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_config: Mocked Config instance.
        mock_counter16: Mocked Counter16 instance.
    """
    counter = 1
    message_dict = {
        "name": "test_satellite",
        "command": "change_radio_modulation",
        "args": ["FSK"],
        "counter": counter,
    }
    message_str = json.dumps(message_dict, separators=(",", ":"))
    hmac_value = cdh._hmac_authenticator.generate_hmac(message_str, counter)
    message_dict["hmac"] = hmac_value

    mock_packet_manager.listen.return_value = json.dumps(message_dict).encode("utf-8")

    cdh.listen_for_commands(30)

    mock_config.update_config.assert_called_once_with(
        "modulation", "FSK", temporary=False
    )


@patch("time.sleep")
def test_listen_for_commands_unknown_command(
    mock_sleep, cdh, mock_packet_manager, mock_logger, mock_counter16
):
    """Tests listen_for_commands with an unknown command.

    Args:
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_logger: Mocked Logger instance.
        mock_counter16: Mocked Counter16 instance.
    """
    counter = 1
    message_dict = {
        "name": "test_satellite",
        "command": "unknown_command",
        "args": [],
        "counter": counter,
    }
    message_str = json.dumps(message_dict, separators=(",", ":"))
    hmac_value = cdh._hmac_authenticator.generate_hmac(message_str, counter)
    message_dict["hmac"] = hmac_value

    mock_packet_manager.listen.return_value = json.dumps(message_dict).encode("utf-8")

    cdh.listen_for_commands(30)

    mock_logger.warning.assert_called_once()


# OSCAR Command Tests


@patch("time.sleep")
def test_listen_for_commands_oscar_password_triggers_oscar_command(
    mock_sleep, cdh, mock_packet_manager, mock_logger
):
    """Tests that OSCAR password triggers the oscar_command function.

    Args:
        mock_sleep: Mocked time.sleep function.
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_logger: Mocked Logger instance.
    """
    message = {
        "password": "Hello World!",
        "command": "ping",
        "args": [],
    }
    mock_packet_manager.listen.return_value = json.dumps(message).encode("utf-8")
    mock_packet_manager.get_last_rssi.return_value = -50

    cdh.listen_for_commands(30)

    # Verify OSCAR command was detected
    mock_logger.debug.assert_any_call("OSCAR command received", msg=message)

    # Verify acknowledgement was sent
    mock_packet_manager.send_acknowledgement.assert_called_once()

    # Verify ping response was sent
    mock_packet_manager.send.assert_called_once_with("Pong! -50".encode("utf-8"))


@patch("time.sleep")
def test_listen_for_commands_oscar_password_missing_command(
    mock_sleep, cdh, mock_packet_manager, mock_logger
):
    """Tests OSCAR password with missing command field.

    Args:
        mock_sleep: Mocked time.sleep function.
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_logger: Mocked Logger instance.
    """
    message = {
        "password": "Hello World!",
        "args": [],
    }
    mock_packet_manager.listen.return_value = json.dumps(message).encode("utf-8")

    cdh.listen_for_commands(30)

    # Verify OSCAR command was detected
    mock_logger.debug.assert_any_call("OSCAR command received", msg=message)

    # Verify warning was logged
    mock_logger.warning.assert_any_call(
        "No OSCAR command found in message", msg=message
    )

    # Verify error message was sent
    mock_packet_manager.send.assert_called_once()
    sent_bytes = mock_packet_manager.send.call_args[0][0]
    expected_message = f"No OSCAR command found in message: {message}"
    assert sent_bytes.decode("utf-8") == expected_message


def test_oscar_command_ping(cdh, mock_packet_manager, mock_logger):
    """Tests the oscar_command method with ping command.

    Args:
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_logger: Mocked Logger instance.
    """
    mock_packet_manager.get_last_rssi.return_value = -75

    cdh.oscar_command("ping", [])

    # Verify info log
    mock_logger.info.assert_called_once_with(
        "OSCAR ping command received. Sending pong response."
    )

    # Verify pong response was sent with RSSI
    mock_packet_manager.send.assert_called_once_with("Pong! -75".encode("utf-8"))


def test_oscar_command_repeat_with_message(cdh, mock_packet_manager, mock_logger):
    """Tests the oscar_command method with repeat command and message.

    Args:
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_logger: Mocked Logger instance.
    """
    args = ["Hello", "from", "ground", "station"]

    cdh.oscar_command("repeat", args)

    # Verify info log
    mock_logger.info.assert_called_once_with(
        "OSCAR repeat command received. Repeating message."
    )

    # Verify the message was repeated
    expected_message = "Hello from ground station"
    mock_packet_manager.send.assert_called_once_with(expected_message.encode("utf-8"))


def test_oscar_command_repeat_no_message(cdh, mock_packet_manager, mock_logger):
    """Tests the oscar_command method with repeat command but no message.

    Args:
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_logger: Mocked Logger instance.
    """
    cdh.oscar_command("repeat", [])

    # Verify warning was logged
    mock_logger.warning.assert_called_once_with(
        "No message specified for repeat command"
    )

    # Verify error message was sent
    mock_packet_manager.send.assert_called_once_with(
        "No message specified for repeat command.".encode("utf-8")
    )


def test_oscar_command_unknown_command(cdh, mock_packet_manager, mock_logger):
    """Tests the oscar_command method with unknown command.

    Args:
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_logger: Mocked Logger instance.
    """
    cdh.oscar_command("unknown_oscar_command", ["some", "args"])

    # Verify warning was logged
    mock_logger.warning.assert_called_once_with(
        "Unknown OSCAR command received", command="unknown_oscar_command"
    )

    # Verify error message was sent
    mock_packet_manager.send.assert_called_once_with(
        "Unknown OSCAR command received: unknown_oscar_command".encode("utf-8")
    )


@patch("time.sleep")
def test_listen_for_commands_oscar_repeat_integration(
    mock_sleep, cdh, mock_packet_manager, mock_logger
):
    """Tests full integration of OSCAR repeat command through listen_for_commands.

    Args:
        mock_sleep: Mocked time.sleep function.
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_logger: Mocked Logger instance.
    """
    message = {
        "password": "Hello World!",
        "command": "repeat",
        "args": ["Testing", "OSCAR", "repeat"],
    }
    mock_packet_manager.listen.return_value = json.dumps(message).encode("utf-8")

    cdh.listen_for_commands(30)

    # Verify OSCAR command was detected
    mock_logger.debug.assert_any_call("OSCAR command received", msg=message)

    # Verify acknowledgement was sent
    mock_packet_manager.send_acknowledgement.assert_called_once()

    # Verify the repeat message was sent
    expected_message = "Testing OSCAR repeat"
    mock_packet_manager.send.assert_called_once_with(expected_message.encode("utf-8"))


@patch("time.sleep")
def test_listen_for_commands_oscar_ping_integration(
    mock_sleep, cdh, mock_packet_manager, mock_logger
):
    """Tests full integration of OSCAR ping command through listen_for_commands.

    Args:
        mock_sleep: Mocked time.sleep function.
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_logger: Mocked Logger instance.
    """
    message = {
        "password": "Hello World!",
        "command": "ping",
        "args": [],
    }
    mock_packet_manager.listen.return_value = json.dumps(message).encode("utf-8")
    mock_packet_manager.get_last_rssi.return_value = -82

    cdh.listen_for_commands(30)

    # Verify OSCAR command was detected
    mock_logger.debug.assert_any_call("OSCAR command received", msg=message)

    # Verify acknowledgement was sent
    mock_packet_manager.send_acknowledgement.assert_called_once()

    # Verify ping response was sent
    mock_packet_manager.send.assert_called_once_with("Pong! -82".encode("utf-8"))


# HMAC Authentication Tests


@patch("time.sleep")
def test_listen_for_commands_valid_hmac(
    mock_sleep, cdh, mock_packet_manager, mock_logger, mock_counter16
):
    """Tests listen_for_commands with valid HMAC authentication.

    Args:
        mock_sleep: Mocked time.sleep function.
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_logger: Mocked Logger instance.
        mock_counter16: Mocked Counter16 instance.
    """
    counter = 1
    message_dict = {
        "name": "test_satellite",
        "command": "send_joke",
        "args": [],
        "counter": counter,
    }
    message_str = json.dumps(message_dict, separators=(",", ":"))

    # Generate valid HMAC
    hmac_value = cdh._hmac_authenticator.generate_hmac(message_str, counter)
    message_dict["hmac"] = hmac_value

    mock_packet_manager.listen.return_value = json.dumps(message_dict).encode("utf-8")

    cdh.listen_for_commands(30)

    # Verify acknowledgement was sent
    mock_packet_manager.send_acknowledgement.assert_called_once()

    # Verify command was executed
    mock_packet_manager.send.assert_called_once()

    # Verify counter was updated in NVM
    mock_counter16.set.assert_called_once_with(counter)


@patch("time.sleep")
def test_listen_for_commands_invalid_hmac(
    mock_sleep, cdh, mock_packet_manager, mock_logger
):
    """Tests listen_for_commands with invalid HMAC.

    Args:
        mock_sleep: Mocked time.sleep function.
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_logger: Mocked Logger instance.
    """
    counter = 2
    message = {
        "name": "test_satellite",
        "command": "send_joke",
        "args": [],
        "counter": counter,
        "hmac": "invalid_hmac_value_0000000000000000000000000000000000000000",
    }

    mock_packet_manager.listen.return_value = json.dumps(message).encode("utf-8")

    cdh.listen_for_commands(30)

    # Verify the message was rejected
    mock_logger.debug.assert_any_call("Invalid HMAC in message", msg=message)

    # Verify acknowledgement was NOT sent
    mock_packet_manager.send_acknowledgement.assert_not_called()


@patch("time.sleep")
def test_listen_for_commands_replay_attack(
    mock_sleep, cdh, mock_packet_manager, mock_logger, mock_counter16
):
    """Tests that replay attacks are prevented.

    Args:
        mock_sleep: Mocked time.sleep function.
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_logger: Mocked Logger instance.
        mock_counter16: Mocked Counter16 instance.
    """
    # First, send a valid command
    counter1 = 10
    mock_counter16.get.return_value = 0  # Initial counter value

    message_dict1 = {
        "name": "test_satellite",
        "command": "send_joke",
        "args": [],
        "counter": counter1,
    }
    message_str1 = json.dumps(message_dict1, separators=(",", ":"))
    hmac_value1 = cdh._hmac_authenticator.generate_hmac(message_str1, counter1)
    message_dict1["hmac"] = hmac_value1

    mock_packet_manager.listen.return_value = json.dumps(message_dict1).encode("utf-8")
    cdh.listen_for_commands(30)

    # Verify counter was updated
    mock_counter16.set.assert_called_with(counter1)

    # Now set the counter to the stored value for replay
    mock_counter16.get.return_value = counter1

    # Try to replay the same command (same counter)
    mock_packet_manager.listen.return_value = json.dumps(message_dict1).encode("utf-8")
    cdh.listen_for_commands(30)

    # Verify the replay was rejected (counter_diff == 0)
    mock_logger.debug.assert_any_call(
        "Replay attack detected - invalid counter",
        counter=counter1,
        last_valid=counter1,
        diff=0,
    )


@patch("time.sleep")
def test_listen_for_commands_old_counter(
    mock_sleep, cdh, mock_packet_manager, mock_logger, mock_counter16
):
    """Tests that old counter values are rejected.

    Args:
        mock_sleep: Mocked time.sleep function.
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_logger: Mocked Logger instance.
        mock_counter16: Mocked Counter16 instance.
    """
    # Set last valid counter to 20
    mock_counter16.get.return_value = 20

    # Try to send a command with counter 15 (older than last valid)
    counter = 15
    message_dict = {
        "name": "test_satellite",
        "command": "send_joke",
        "args": [],
        "counter": counter,
    }
    message_str = json.dumps(message_dict, separators=(",", ":"))
    hmac_value = cdh._hmac_authenticator.generate_hmac(message_str, counter)
    message_dict["hmac"] = hmac_value

    mock_packet_manager.listen.return_value = json.dumps(message_dict).encode("utf-8")

    cdh.listen_for_commands(30)

    # Verify the command was rejected (counter_diff > 0x8000 means backwards)
    mock_logger.debug.assert_any_call(
        "Replay attack detected - invalid counter",
        counter=counter,
        last_valid=20,
        diff=(15 - 20) & 0xFFFF,  # 65531 which is > 0x8000
    )

    # Verify acknowledgement was NOT sent
    mock_packet_manager.send_acknowledgement.assert_not_called()


@patch("time.sleep")
def test_listen_for_commands_hmac_with_wrong_satellite_name(
    mock_sleep, cdh, mock_packet_manager, mock_logger
):
    """Tests HMAC authentication with wrong satellite name.

    Args:
        mock_sleep: Mocked time.sleep function.
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_logger: Mocked Logger instance.
    """
    counter = 30
    message_dict = {
        "name": "wrong_satellite",
        "command": "send_joke",
        "args": [],
        "counter": counter,
    }
    message_str = json.dumps(message_dict, separators=(",", ":"))
    hmac_value = cdh._hmac_authenticator.generate_hmac(message_str, counter)
    message_dict["hmac"] = hmac_value

    mock_packet_manager.listen.return_value = json.dumps(message_dict).encode("utf-8")

    cdh.listen_for_commands(30)

    # Verify the message was rejected due to name mismatch
    mock_logger.debug.assert_any_call(
        "Satellite name mismatch in message", msg=message_dict
    )

    # Verify acknowledgement was NOT sent
    mock_packet_manager.send_acknowledgement.assert_not_called()


@patch("time.sleep")
@patch("pysquared.cdh.microcontroller")
def test_listen_for_commands_reset_with_hmac(
    mock_microcontroller, mock_sleep, cdh, mock_packet_manager, mock_logger
):
    """Tests listen_for_commands with reset command using HMAC authentication.

    Args:
        mock_microcontroller: Mocked microcontroller module.
        mock_sleep: Mocked time.sleep function.
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_logger: Mocked Logger instance.
    """
    # Set up mocked attributes
    mock_microcontroller.reset = MagicMock()
    mock_microcontroller.on_next_reset = MagicMock()

    counter = 40
    message_dict = {
        "name": "test_satellite",
        "command": "reset",
        "args": [],
        "counter": counter,
    }
    message_str = json.dumps(message_dict, separators=(",", ":"))
    hmac_value = cdh._hmac_authenticator.generate_hmac(message_str, counter)
    message_dict["hmac"] = hmac_value

    mock_packet_manager.listen.return_value = json.dumps(message_dict).encode("utf-8")

    cdh.listen_for_commands(30)

    # Verify acknowledgement was sent
    mock_packet_manager.send_acknowledgement.assert_called_once()

    # Verify reset was called
    mock_microcontroller.on_next_reset.assert_called_once_with(
        mock_microcontroller.RunMode.NORMAL
    )
    mock_microcontroller.reset.assert_called_once()


@patch("time.sleep")
def test_listen_for_commands_counter_wraparound(
    mock_sleep, cdh, mock_packet_manager, mock_logger, mock_counter16
):
    """Tests that counter wraparound is handled correctly.

    Args:
        mock_sleep: Mocked time.sleep function.
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_logger: Mocked Logger instance.
        mock_counter16: Mocked Counter16 instance.
    """
    # Set last valid counter near max value
    mock_counter16.get.return_value = 65530

    # Send command with wrapped counter (small value)
    counter = 5
    message_dict = {
        "name": "test_satellite",
        "command": "send_joke",
        "args": [],
        "counter": counter,
    }
    message_str = json.dumps(message_dict, separators=(",", ":"))
    hmac_value = cdh._hmac_authenticator.generate_hmac(message_str, counter)
    message_dict["hmac"] = hmac_value

    mock_packet_manager.listen.return_value = json.dumps(message_dict).encode("utf-8")

    cdh.listen_for_commands(30)

    # Verify command was accepted (wraparound handled correctly)
    mock_packet_manager.send_acknowledgement.assert_called_once()
    mock_counter16.set.assert_called_once_with(counter)


@patch("time.sleep")
def test_listen_for_commands_counter_out_of_range(
    mock_sleep, cdh, mock_packet_manager, mock_logger, mock_counter16
):
    """Tests that out-of-range counter values are rejected.

    Args:
        mock_sleep: Mocked time.sleep function.
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_logger: Mocked Logger instance.
        mock_counter16: Mocked Counter16 instance.
    """
    # Send command with out-of-range counter
    counter = 70000  # > 65535
    message_dict = {
        "name": "test_satellite",
        "command": "send_joke",
        "args": [],
        "counter": counter,
    }
    message_str = json.dumps(message_dict, separators=(",", ":"))
    hmac_value = cdh._hmac_authenticator.generate_hmac(message_str, counter)
    message_dict["hmac"] = hmac_value

    mock_packet_manager.listen.return_value = json.dumps(message_dict).encode("utf-8")

    cdh.listen_for_commands(30)

    # Verify command was rejected
    mock_logger.debug.assert_any_call("Counter out of range", counter=counter)
    mock_packet_manager.send_acknowledgement.assert_not_called()
