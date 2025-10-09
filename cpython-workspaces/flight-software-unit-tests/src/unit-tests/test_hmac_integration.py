"""Integration tests for HMAC command authentication between ground station and flight software.

This module contains integration tests that verify the complete HMAC authentication
flow between the ground station and the satellite's command data handler.
"""

import json
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from pysquared.cdh import CommandDataHandler
from pysquared.config.config import Config
from pysquared.hardware.radio.packetizer.packet_manager import PacketManager
from pysquared.hmac_auth import HMACAuthenticator
from pysquared.logger import Logger
from pysquared.nvm.counter import Counter16


@pytest.fixture
def mock_logger():
    """Mocks the Logger class."""
    return MagicMock(spec=Logger)


@pytest.fixture
def mock_packet_manager():
    """Mocks the PacketManager class."""
    return MagicMock(spec=PacketManager)


@pytest.fixture
def mock_config():
    """Mocks the Config class."""
    config = MagicMock(spec=Config)
    config.cubesat_name = "TestSat"
    config.hmac_secret = "shared_secret_key_123"
    config.jokes = ["Why did the satellite go to school? To improve its orbit-ude!"]
    return config


@pytest.fixture
def mock_counter16():
    """Mocks the Counter16 class."""
    counter = MagicMock(spec=Counter16)
    counter.get.return_value = 0  # Start at 0
    return counter


@pytest.fixture
def flight_software_cdh(mock_logger, mock_config, mock_packet_manager, mock_counter16):
    """Provides a CommandDataHandler instance (flight software side)."""
    return CommandDataHandler(
        logger=mock_logger,
        config=mock_config,
        packet_manager=mock_packet_manager,
        last_command_counter=mock_counter16,
    )


@pytest.fixture
def ground_station_authenticator(mock_config):
    """Provides an HMACAuthenticator instance (ground station side)."""
    return HMACAuthenticator(mock_config.hmac_secret)


@pytest.fixture
def mock_hmac() -> Generator[MagicMock, None, None]:
    """Mocks the HMAC class.

    Yields:
        A MagicMock instance of HMAC.
    """
    with patch("pysquared.hmac_auth.HMAC") as mock_class:
        mock_class.return_value = MagicMock()
        yield mock_class


def test_hmac_integration_valid_command(
    flight_software_cdh,
    ground_station_authenticator,
    mock_config,
    mock_packet_manager,
    mock_counter16,
    mock_hmac,
):
    """Tests successful HMAC authentication flow from ground station to flight software.

    Args:
        flight_software_cdh: Flight software CDH instance.
        ground_station_authenticator: Ground station HMAC authenticator.
        mock_config: Mocked Config instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_counter16: Mocked Counter16 instance.
    """
    # Ground station creates a command
    gs_counter = 1
    command_message = {
        "name": "TestSat",
        "command": "send_joke",
        "args": [],
        "counter": gs_counter,
    }

    # Ground station generates HMAC
    message_str = json.dumps(command_message, separators=(",", ":"))
    mock_hmac.return_value.hexdigest.return_value = "fake_hmac_value"
    hmac_value = ground_station_authenticator.generate_hmac(message_str, gs_counter)
    command_message["hmac"] = hmac_value

    # Ground station sends the command (simulated)
    command_bytes = json.dumps(command_message).encode("utf-8")

    # Flight software receives the command
    mock_packet_manager.listen.return_value = command_bytes

    # Flight software processes the command
    with patch("time.sleep"):
        flight_software_cdh.listen_for_commands(timeout=30)

    # Verify the command was accepted
    mock_packet_manager.send_acknowledgement.assert_called_once()

    # Verify counter was updated in NVM
    mock_counter16.set.assert_called_once_with(gs_counter)

    # Verify the joke was sent
    mock_packet_manager.send.assert_called_once()
    sent_data = mock_packet_manager.send.call_args[0][0]
    assert sent_data == mock_config.jokes[0].encode("utf-8")


def test_hmac_integration_invalid_hmac(
    flight_software_cdh,
    ground_station_authenticator,
    mock_config,
    mock_packet_manager,
    mock_logger,
    mock_hmac,
):
    """Tests that flight software rejects commands with invalid HMAC.

    Args:
        flight_software_cdh: Flight software CDH instance.
        ground_station_authenticator: Ground station HMAC authenticator.
        mock_config: Mocked Config instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_logger: Mocked Logger instance.
    """
    # Ground station creates a command
    gs_counter = 2
    command_message = {
        "name": "TestSat",
        "command": "send_joke",
        "args": [],
        "counter": gs_counter,
    }

    # Attacker modifies the command but keeps the original HMAC
    message_str = json.dumps(command_message, separators=(",", ":"))
    hmac_value = ground_station_authenticator.generate_hmac(message_str, gs_counter)

    # Modify the command (tampering)
    command_message["command"] = "reset"  # Changed by attacker
    command_message["hmac"] = hmac_value  # Original HMAC (now invalid)

    # Attacker sends the tampered command
    command_bytes = json.dumps(command_message).encode("utf-8")

    # Flight software receives the tampered command
    mock_packet_manager.listen.return_value = command_bytes

    # Flight software processes the command
    with patch("time.sleep"):
        flight_software_cdh.listen_for_commands(timeout=30)

    # Verify the command was rejected
    mock_packet_manager.send_acknowledgement.assert_not_called()
    mock_logger.debug.assert_any_call("Invalid HMAC in message", msg=command_message)


def test_hmac_integration_replay_attack(
    flight_software_cdh,
    ground_station_authenticator,
    mock_config,
    mock_packet_manager,
    mock_counter16,
    mock_logger,
    mock_hmac,
):
    """Tests that flight software prevents replay attacks.

    Args:
        flight_software_cdh: Flight software CDH instance.
        ground_station_authenticator: Ground station HMAC authenticator.
        mock_config: Mocked Config instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_counter16: Mocked Counter16 instance.
        mock_logger: Mocked Logger instance.
    """
    # Ground station sends first command
    gs_counter = 10
    command_message = {
        "name": "TestSat",
        "command": "send_joke",
        "args": [],
        "counter": gs_counter,
    }

    message_str = json.dumps(command_message, separators=(",", ":"))
    mock_hmac.return_value.hexdigest.return_value = "fake_hmac_value"
    hmac_value = ground_station_authenticator.generate_hmac(message_str, gs_counter)
    command_message["hmac"] = hmac_value
    command_bytes = json.dumps(command_message).encode("utf-8")

    # Flight software receives and accepts first command
    mock_packet_manager.listen.return_value = command_bytes
    with patch("time.sleep"):
        flight_software_cdh.listen_for_commands(timeout=30)

    # Verify first command was accepted
    assert mock_counter16.set.call_count == 1

    # Update counter to simulate NVM storage
    mock_counter16.get.return_value = gs_counter

    # Attacker tries to replay the same command
    mock_packet_manager.listen.return_value = command_bytes
    with patch("time.sleep"):
        flight_software_cdh.listen_for_commands(timeout=30)

    # Verify replay was rejected
    mock_logger.debug.assert_any_call(
        "Replay attack detected - invalid counter",
        counter=gs_counter,
        last_valid=gs_counter,
        diff=0,
    )


def test_hmac_integration_counter_sequence(
    flight_software_cdh,
    ground_station_authenticator,
    mock_config,
    mock_packet_manager,
    mock_counter16,
    mock_hmac,
):
    """Tests multiple commands with incrementing counters.

    Args:
        flight_software_cdh: Flight software CDH instance.
        ground_station_authenticator: Ground station HMAC authenticator.
        mock_config: Mocked Config instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_counter16: Mocked Counter16 instance.
    """
    # Simulate sending multiple commands with incrementing counters
    for gs_counter in [1, 2, 3, 4, 5]:
        command_message = {
            "name": "TestSat",
            "command": "send_joke",
            "args": [],
            "counter": gs_counter,
        }

        message_str = json.dumps(command_message, separators=(",", ":"))
        mock_hmac.return_value.hexdigest.return_value = "fake_hmac_value"
        hmac_value = ground_station_authenticator.generate_hmac(message_str, gs_counter)
        command_message["hmac"] = hmac_value
        command_bytes = json.dumps(command_message).encode("utf-8")

        # Update the counter to reflect previous successful command
        if gs_counter > 1:
            mock_counter16.get.return_value = gs_counter - 1

        mock_packet_manager.listen.return_value = command_bytes
        with patch("time.sleep"):
            flight_software_cdh.listen_for_commands(timeout=30)

        # Verify counter was updated
        assert mock_counter16.set.call_args[0][0] == gs_counter

    # All 5 commands should have been accepted
    assert mock_counter16.set.call_count == 5


def test_hmac_integration_counter_wraparound(
    flight_software_cdh,
    ground_station_authenticator,
    mock_config,
    mock_packet_manager,
    mock_counter16,
    mock_hmac,
):
    """Tests counter wraparound handling in integration scenario.

    Args:
        flight_software_cdh: Flight software CDH instance.
        ground_station_authenticator: Ground station HMAC authenticator.
        mock_config: Mocked Config instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_counter16: Mocked Counter16 instance.
    """
    # Set counter near max value (simulating many commands sent)
    mock_counter16.get.return_value = 65530

    # Ground station sends command with wrapped counter
    gs_counter = 10  # Wrapped around from 65535 -> 0 -> 10
    command_message = {
        "name": "TestSat",
        "command": "send_joke",
        "args": [],
        "counter": gs_counter,
    }

    message_str = json.dumps(command_message, separators=(",", ":"))
    mock_hmac.return_value.hexdigest.return_value = "fake_hmac_value"
    hmac_value = ground_station_authenticator.generate_hmac(message_str, gs_counter)
    command_message["hmac"] = hmac_value
    command_bytes = json.dumps(command_message).encode("utf-8")

    mock_packet_manager.listen.return_value = command_bytes
    with patch("time.sleep"):
        flight_software_cdh.listen_for_commands(timeout=30)

    # Verify wraparound was handled correctly
    mock_packet_manager.send_acknowledgement.assert_called_once()
    mock_counter16.set.assert_called_once_with(gs_counter)


def test_hmac_integration_different_secrets(
    mock_logger,
    mock_config,
    mock_packet_manager,
    mock_counter16,
    mock_hmac,
):
    """Tests that flight software rejects commands with different HMAC secret.

    Args:
        mock_logger: Mocked Logger instance.
        mock_config: Mocked Config instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_counter16: Mocked Counter16 instance.
        mock_hmac: Mocked Hmac instance
    """
    # Flight software with one secret
    flight_software_cdh = CommandDataHandler(
        logger=mock_logger,
        config=mock_config,
        packet_manager=mock_packet_manager,
        last_command_counter=mock_counter16,
    )

    # Ground station with different secret (attacker scenario)
    wrong_authenticator = HMACAuthenticator("wrong_secret_key")

    gs_counter = 1
    command_message = {
        "name": "TestSat",
        "command": "send_joke",
        "args": [],
        "counter": gs_counter,
    }

    message_str = json.dumps(command_message, separators=(",", ":"))
    hmac_value = wrong_authenticator.generate_hmac(message_str, gs_counter)
    command_message["hmac"] = hmac_value
    command_bytes = json.dumps(command_message).encode("utf-8")

    mock_packet_manager.listen.return_value = command_bytes
    with patch("time.sleep"):
        flight_software_cdh.listen_for_commands(timeout=30)

    # Verify command was rejected due to wrong HMAC
    mock_packet_manager.send_acknowledgement.assert_not_called()
    mock_logger.debug.assert_any_call("Invalid HMAC in message", msg=command_message)


def test_hmac_integration_large_message(
    flight_software_cdh,
    ground_station_authenticator,
    mock_config,
    mock_packet_manager,
    mock_counter16,
    mock_hmac,
):
    """Tests HMAC authentication with large message requiring packetization.

    This test verifies that HMAC authentication works correctly even when
    the message is larger than the packet size (252 bytes) and needs to be
    broken into multiple packets by the packet_manager.

    Args:
        flight_software_cdh: Flight software CDH instance.
        ground_station_authenticator: Ground station HMAC authenticator.
        mock_config: Mocked Config instance.
        mock_packet_manager: Mocked PacketManager instance.
        mock_counter16: Mocked Counter16 instance.
    """
    # Create a large command message (approximately 10kB)
    # Generate a large argument list to make the message size > 10kB
    large_data = "A" * 10000  # 10kB of data
    gs_counter = 1
    command_message = {
        "name": "TestSat",
        "command": "send_joke",
        "args": [large_data],  # Large argument
        "counter": gs_counter,
    }

    # Ground station generates HMAC for the complete message
    message_str = json.dumps(command_message, separators=(",", ":"))
    mock_hmac.return_value.hexdigest.return_value = "fake_hmac_value"
    hmac_value = ground_station_authenticator.generate_hmac(message_str, gs_counter)
    command_message["hmac"] = hmac_value

    # The complete message as bytes
    command_bytes = json.dumps(command_message).encode("utf-8")

    # Verify the message is indeed large (> 252 bytes, typical packet size)
    assert len(command_bytes) > 252, (
        f"Message size {len(command_bytes)} should be > 252"
    )
    assert len(command_bytes) > 10000, (
        f"Message size {len(command_bytes)} should be > 10kB"
    )

    # In real scenario, packet_manager would fragment this message
    # For this test, we simulate that the complete message is reassembled
    # and returned by packet_manager.listen()
    mock_packet_manager.listen.return_value = command_bytes

    # Flight software receives and processes the large message
    with patch("time.sleep"):
        flight_software_cdh.listen_for_commands(timeout=30)

    # Verify HMAC authentication succeeded despite large message size
    mock_packet_manager.send_acknowledgement.assert_called_once()

    # Verify counter was updated in NVM
    mock_counter16.set.assert_called_once_with(gs_counter)

    # Verify the command was accepted and processed
    # (In this case, send_joke would be called with the large args)
    assert mock_packet_manager.send_acknowledgement.called
