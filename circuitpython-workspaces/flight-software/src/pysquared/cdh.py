"""This module provides the CommandDataHandler for managing and processing commands.

This module is responsible for handling commands received by the satellite. It
includes command parsing, validation, execution, and handling of radio
communications. The CommandDataHandler class is the main entry point for this
functionality.

**Usage:**
```python
logger = Logger()
config = Config("config.json")
packet_manager = PacketManager(logger, radio)
cdh = CommandDataHandler(logger, config, packet_manager)
cdh.listen_for_commands(timeout=60)
```
"""

import json
import random
import time
import traceback

import microcontroller

from .config.config import Config
from .hardware.radio.packetizer.packet_manager import PacketManager
from .logger import Logger


class CommandDataHandler:
    """Handles command parsing, validation, and execution for the satellite."""

    command_reset: str = "reset"
    command_change_radio_modulation: str = "change_radio_modulation"
    command_send_joke: str = "send_joke"

    def __init__(
        self,
        logger: Logger,
        config: Config,
        packet_manager: PacketManager,
        send_delay: float = 0.2,
    ) -> None:
        """Initializes the CommandDataHandler.

        Args:
            logger: The logger to use.
            config: The configuration to use.
            packet_manager: The packet manager to use for sending and receiving data.
            send_delay: The delay between sending an acknowledgement and the response.
        """
        self._log: Logger = logger
        self._config: Config = config
        self._packet_manager: PacketManager = packet_manager
        self._send_delay: float = send_delay

    def listen_for_commands(self, timeout: int) -> None:
        """Listens for commands from the radio and handles them.

        Args:
            timeout: The time in seconds to listen for commands.
        """
        self._log.debug("Listening for commands...", timeout=timeout)

        json_bytes = self._packet_manager.listen(timeout)
        if json_bytes is None:
            return

        try:
            json_str = json_bytes.decode("utf-8")

            msg: dict[str, str] = json.loads(json_str)

            # If message has password field, check it
            if msg.get("password") != self._config.super_secret_code:
                self._log.debug(
                    "Invalid password in message",
                    msg=msg,
                )
                return

            if msg.get("name") != self._config.cubesat_name:
                self._log.debug(
                    "Satellite name mismatch in message",
                    msg=msg,
                )
                return

            # If message has command field, execute the command
            cmd = msg.get("command")
            if cmd is None:
                self._log.warning("No command found in message", msg=msg)
                self._packet_manager.send(
                    f"No command found in message: {msg}".encode("utf-8")
                )
                return

            args: list[str] = []
            raw_args = msg.get("args")
            if isinstance(raw_args, list):
                args: list[str] = raw_args

            self._log.debug("Received command message", cmd=cmd, args=args)

            # Delay to give the ground station time to switch to listening mode
            time.sleep(self._send_delay)
            self._packet_manager.send_acknowledgement()

            if cmd == self.command_reset:
                self.reset()
            elif cmd == self.command_change_radio_modulation:
                self.change_radio_modulation(args)
            elif cmd == self.command_send_joke:
                self.send_joke()
            else:
                self._log.warning("Unknown command received", cmd=cmd)
                self._packet_manager.send(
                    f"Unknown command received: {cmd}".encode("utf-8")
                )

        except Exception as e:
            self._log.error("Failed to process command message", err=e)
            self._packet_manager.send(
                f"Failed to process command message: {traceback.format_exception(e)}".encode(
                    "utf-8"
                )
            )
            return

    def send_joke(self) -> None:
        """Sends a random joke from the config."""
        joke = random.choice(self._config.jokes)
        self._log.info("Sending joke", joke=joke)
        self._packet_manager.send(joke.encode("utf-8"))

    def change_radio_modulation(self, args: list[str]) -> None:
        """Changes the radio modulation.

        Args:
            args: A list of arguments, the first item must be the new modulation. All other items in the args list are ignored.
        """
        modulation = "UNSET"

        if len(args) < 1:
            self._log.warning("No modulation specified")
            self._packet_manager.send(
                "No modulation specified. Please provide a modulation type.".encode(
                    "utf-8"
                )
            )
            return

        modulation = args[0]

        try:
            self._config.update_config("modulation", modulation, temporary=False)
            self._log.info("Radio modulation changed", modulation=modulation)
            self._packet_manager.send(
                f"Radio modulation changed: {modulation}".encode("utf-8")
            )
        except ValueError as e:
            self._log.error("Failed to change radio modulation", err=e)
            self._packet_manager.send(
                f"Failed to change radio modulation: {e}".encode("utf-8")
            )

    def reset(self) -> None:
        """Resets the hardware."""
        self._log.info("Resetting satellite")
        self._packet_manager.send(data="Resetting satellite".encode("utf-8"))
        microcontroller.on_next_reset(microcontroller.RunMode.NORMAL)
        microcontroller.reset()
