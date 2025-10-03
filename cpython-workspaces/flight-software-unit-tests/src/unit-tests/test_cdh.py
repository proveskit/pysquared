"""Unit tests for the CommandDataHandler class.

This module contains unit tests for the `CommandDataHandler` class, which is
responsible for processing commands received by the satellite. The tests cover
initialization, command parsing, and execution of various commands.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from pysquared.cdh import CommandDataHandler
from pysquared.config.config import Config
from pysquared.hardware.radio.packetizer.packet_manager import PacketManager
from pysquared.logger import Logger


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
    config.jokes = ["Why did the satellite cross the orbit? To get to the other side!"]
    return config


@pytest.fixture
def cdh(mock_logger, mock_config, mock_packet_manager) -> CommandDataHandler:
    """Provides a CommandDataHandler instance for testing."""
    return CommandDataHandler(
        logger=mock_logger,
        config=mock_config,
        packet_manager=mock_packet_manager,
    )


def test_cdh_init(mock_logger, mock_config, mock_packet_manager):
    """Tests CommandDataHandler initialization.

    Args:
        mock_logger: Mocked Logger instance.
        mock_config: Mocked Config instance.
        mock_packet_manager: Mocked PacketManager instance.
    """
    cdh = CommandDataHandler(mock_logger, mock_config, mock_packet_manager)

    assert cdh._log is mock_logger
    assert cdh._config is mock_config
    assert cdh._packet_manager is mock_packet_manager


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


def test_listen_for_commands_invalid_password(cdh, mock_packet_manager, mock_logger):
    """Tests listen_for_commands with invalid password.

    Args:
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_logger: Mocked Logger instance.
    """
    # Create a message with wrong password
    message = {"password": "wrong_password", "command": "send_joke", "args": []}
    mock_packet_manager.listen.return_value = json.dumps(message).encode("utf-8")

    cdh.listen_for_commands(30)

    mock_packet_manager.listen.assert_called_once_with(30)
    mock_logger.debug.assert_any_call("Invalid password in message", msg=message)


def test_listen_for_commands_invalid_name(cdh, mock_packet_manager, mock_logger):
    """Tests listen_for_commands with missing command field.

    Args:
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_logger: Mocked Logger instance.
    """
    # Create a message with valid password and satellite name but no command
    message = {"password": "test_password", "name": "wrong_name", "args": []}
    mock_packet_manager.listen.return_value = json.dumps(message).encode("utf-8")

    cdh.listen_for_commands(30)

    mock_packet_manager.listen.assert_called_once_with(30)
    mock_logger.debug.assert_any_call("Satellite name mismatch in message", msg=message)


def test_listen_for_commands_missing_command(cdh, mock_packet_manager, mock_logger):
    """Tests listen_for_commands with missing command field.

    Args:
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_logger: Mocked Logger instance.
    """
    # Create a message with valid password but no command
    message = {"password": "test_password", "name": "test_satellite", "args": []}
    mock_packet_manager.listen.return_value = json.dumps(message).encode("utf-8")

    cdh.listen_for_commands(30)

    mock_packet_manager.listen.assert_called_once_with(30)
    mock_logger.warning.assert_any_call("No command found in message", msg=message)


def test_listen_for_commands_nonlist_args(cdh, mock_packet_manager, mock_logger):
    """Tests listen_for_commands with missing command field.

    Args:
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_logger: Mocked Logger instance.
    """
    # Create a message with valid password but no command
    message = {
        "password": "test_password",
        "name": "test_satellite",
        "command": "send_joke",
        "args": "not_a_list",
    }
    mock_packet_manager.listen.return_value = json.dumps(message).encode("utf-8")

    cdh.listen_for_commands(30)

    mock_packet_manager.listen.assert_called_once_with(30)
    mock_logger.debug.assert_any_call(
        "Received command message", cmd="send_joke", args=[]
    )


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
    """
    # Set up mocked attributes
    mock_microcontroller.reset = MagicMock()
    mock_microcontroller.on_next_reset = MagicMock()

    message = {
        "password": "test_password",
        "name": "test_satellite",
        "command": "reset",
        "args": [],
    }
    mock_packet_manager.listen.return_value = json.dumps(message).encode("utf-8")

    cdh.listen_for_commands(30)

    mock_microcontroller.on_next_reset.assert_called_once_with(
        mock_microcontroller.RunMode.NORMAL
    )
    mock_microcontroller.reset.assert_called_once()


@patch("time.sleep")
@patch("random.choice")
def test_listen_for_commands_send_joke(
    mock_random_choice, mock_sleep, cdh, mock_packet_manager, mock_config
):
    """Tests listen_for_commands with send_joke command.

    Args:
        mock_random_choice: Mocked random.choice function.
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_config: Mocked Config instance.
    """
    message = {
        "password": "test_password",
        "name": "test_satellite",
        "command": "send_joke",
        "args": [],
    }
    mock_packet_manager.listen.return_value = json.dumps(message).encode("utf-8")
    mock_random_choice.return_value = mock_config.jokes[0]

    cdh.listen_for_commands(30)

    mock_packet_manager.send.assert_called_once_with(
        mock_config.jokes[0].encode("utf-8")
    )


@patch("time.sleep")
def test_listen_for_commands_change_radio_modulation(
    mock_sleep, cdh, mock_packet_manager, mock_config
):
    """Tests listen_for_commands with change_radio_modulation command.

    Args:
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_config: Mocked Config instance.
    """
    message = {
        "password": "test_password",
        "name": "test_satellite",
        "command": "change_radio_modulation",
        "args": ["FSK"],
    }
    mock_packet_manager.listen.return_value = json.dumps(message).encode("utf-8")

    cdh.listen_for_commands(30)

    mock_config.update_config.assert_called_once_with(
        "modulation", "FSK", temporary=False
    )


@patch("time.sleep")
def test_listen_for_commands_unknown_command(
    mock_sleep, cdh, mock_packet_manager, mock_logger
):
    """Tests listen_for_commands with an unknown command.

    Args:
        cdh: CommandDataHandler instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_logger: Mocked Logger instance.
    """
    message = {
        "password": "test_password",
        "name": "test_satellite",
        "command": "unknown_command",
        "args": [],
    }
    mock_packet_manager.listen.return_value = json.dumps(message).encode("utf-8")

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
