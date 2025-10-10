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
from circuitpython_hmac import HMAC

from .config.config import Config
from .config.jokes_config import JokesConfig
from .hardware.radio.packetizer.packet_manager import PacketManager
from .hmac_auth import HMACAuthenticator
from .logger import Logger
from .nvm.counter import Counter16

try:
    from typing import Callable, Optional
except Exception:
    pass


class CommandDataHandler:
    """Handles command parsing, validation, and execution for the satellite."""

    command_reset: str = "reset"
    command_change_radio_modulation: str = "change_radio_modulation"
    command_send_joke: str = "send_joke"
    command_get_counter: str = "get_counter"

    oscar_password: str = "Hello World!"  # Default password for OSCAR commands

    def __init__(
        self,
        logger: Logger,
        config: Config,
        packet_manager: PacketManager,
        jokes_config: JokesConfig,
        last_command_counter: Optional[Counter16] = None,
        send_delay: float = 0.2,
        hmac_class: Callable = HMAC,
    ) -> None:
        """Initializes the CommandDataHandler.

        Args:
            logger: The logger to use.
            config: The configuration to use.
            packet_manager: The packet manager to use for sending and receiving data.
            last_command_counter: NVM counter tracking the last valid command counter (16-bit).
            send_delay: The delay between sending an acknowledgement and the response.
        """
        self._log: Logger = logger
        self._config: Config = config
        self._jokes_config: JokesConfig = jokes_config
        self._packet_manager: PacketManager = packet_manager
        self._send_delay: float = send_delay
        self._hmac_authenticator: HMACAuthenticator = HMACAuthenticator(
            config.hmac_secret, hmac_class=hmac_class
        )
        if last_command_counter is not None:
            self._last_command_counter: Counter16 = last_command_counter
        else:
            self._last_command_counter = Counter16(1)

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

            # Check for OSCAR password first (legacy authentication)
            if msg.get("password") == self.oscar_password:
                self._log.debug("OSCAR command received", msg=msg)
                cmd = msg.get("command")
                if cmd is None:
                    self._log.warning("No OSCAR command found in message", msg=msg)
                    self._packet_manager.send(
                        f"No OSCAR command found in message: {msg}".encode("utf-8")
                    )
                    return

                args: list[str] = []
                raw_args = msg.get("args")
                if isinstance(raw_args, list):
                    args: list[str] = raw_args

                # Delay to give the ground station time to switch to listening mode
                time.sleep(self._send_delay)
                self._packet_manager.send_acknowledgement()

                self.oscar_command(cmd, args)
                return

            # If message has command field, get the command
            cmd = msg.get("command")

            if cmd is not None and cmd == self.command_get_counter:
                self.send_counter()
                return

            # HMAC-based authentication (required for non-OSCAR commands)
            hmac_value = str(msg.get("hmac"))
            counter_raw = msg.get("counter")

            # Require HMAC authentication
            if hmac_value is None or counter_raw is None:
                self._log.debug(
                    "Missing HMAC or counter in message",
                    msg=msg,
                )
                return

            # Use HMAC authentication
            # Convert counter to int
            try:
                counter: int = int(counter_raw)
            except (ValueError, TypeError):
                self._log.debug(
                    "Invalid counter in message",
                    counter=counter_raw,
                )
                return

            # Validate counter is within 16-bit range
            if counter < 0 or counter > 0xFFFF:
                self._log.debug(
                    "Counter out of range",
                    counter=counter,
                )
                return

            # Extract message without HMAC for verification
            msg_without_hmac = {k: v for k, v in msg.items() if k != "hmac"}
            message_str = json.dumps(msg_without_hmac, separators=(",", ":"))

            # Verify HMAC
            if not self._hmac_authenticator.verify_hmac(
                message_str, counter, hmac_value
            ):
                self._log.debug(
                    "Invalid HMAC in message",
                    msg=msg,
                )
                return

            # Prevent replay attacks with wraparound handling
            last_valid = self._last_command_counter.get()

            # Check if counter is valid considering 16-bit wraparound
            # Accept if counter is greater, or if wraparound occurred
            # (counter is much smaller, indicating it wrapped around)
            counter_diff = (counter - last_valid) & 0xFFFF

            # Valid if counter is within forward window (1 to 32768)
            # This allows for wraparound while preventing replay attacks
            if counter_diff == 0 or counter_diff > 0x8000:
                self._log.debug(
                    "Replay attack detected - invalid counter",
                    counter=counter,
                    last_valid=last_valid,
                    diff=counter_diff,
                )
                return

            # Update last valid counter in NVM
            self._last_command_counter.set(counter)

            # Verify satellite name
            if msg.get("name") != self._config.cubesat_name:
                self._log.debug(
                    "Satellite name mismatch in message",
                    msg=msg,
                )
                return

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
        joke = random.choice(self._jokes_config.jokes)
        self._log.info("Sending joke", joke=joke)
        self._packet_manager.send(joke.encode("utf-8"))

    def send_counter(self):
        """Send the counter down so the ground station knows how to authenticate"""
        counter = str(self._last_command_counter)
        self._log.info("Sending Counter", counter=counter)
        self._packet_manager.send(counter.encode("utf-8"))

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

    def oscar_command(self, command: str, args: list[str]) -> None:
        """Handles OSCAR commands.

        Args:
            command: The OSCAR command to execute.
            args: A list of arguments for the command.
        """
        if command == "ping":
            self._log.info("OSCAR ping command received. Sending pong response.")
            self._packet_manager.send(
                f"Pong! {self._packet_manager.get_last_rssi()}".encode("utf-8")
            )

        elif command == "repeat":
            if len(args) < 1:
                self._log.warning("No message specified for repeat command")
                self._packet_manager.send(
                    "No message specified for repeat command.".encode("utf-8")
                )
                return
            repeat_message = " ".join(args)
            self._log.info("OSCAR repeat command received. Repeating message.")
            self._packet_manager.send(repeat_message.encode("utf-8"))

        else:
            self._log.warning("Unknown OSCAR command received", command=command)
            self._packet_manager.send(
                f"Unknown OSCAR command received: {command}".encode("utf-8")
            )
