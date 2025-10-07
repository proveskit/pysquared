"""
PySquared Ground Station
"""

import json
import time

import supervisor
from pysquared.cdh import CommandDataHandler
from pysquared.config.config import Config
from pysquared.hardware.radio.packetizer.packet_manager import PacketManager
from pysquared.hmac_auth import HMACAuthenticator
from pysquared.logger import Logger


class GroundStation:
    """Ground Station class to manage communication with the satellite."""

    def __init__(
        self,
        logger: Logger,
        config: Config,
        packet_manager: PacketManager,
        cdh: CommandDataHandler,
        starting_counter: int = 0,
    ):
        self._log = logger
        self._log.colorized = True
        self._config = config
        self._packet_manager = packet_manager
        self._cdh = cdh
        self._hmac_authenticator = HMACAuthenticator(config.hmac_secret)
        self._command_counter = starting_counter  # Counter for replay attack prevention

    def listen(self):
        """Listen for incoming packets from the satellite."""

        try:
            while True:
                if supervisor.runtime.serial_bytes_available:
                    typed = input().strip()
                    if typed:
                        self.handle_input(typed)

                b = self._packet_manager.listen(1)
                if b is not None:
                    self._log.info(
                        message="Received response", response=b.decode("utf-8")
                    )

        except KeyboardInterrupt:
            self._log.debug("Keyboard interrupt received, exiting listen mode.")

    def send_receive(self):
        """Send commands to the satellite and wait for responses."""

        try:
            cmd_selection = input(
                """
            ===============================
            | Select command to send      |
            | 1: Reset                    |
            | 2: Change radio modulation  |
            | 3: Send joke                |
            | 4: OSCAR commands           |
            ===============================
            """
            )

            self.handle_input(cmd_selection)

        except KeyboardInterrupt:
            self._log.debug("Keyboard interrupt received, exiting send mode.")

    def handle_input(self, cmd_selection):
        """
        Handle user input commands.

        Args:
            cmd_selection: The command selection input by the user.
        """
        if cmd_selection not in ["1", "2", "3", "4"]:
            self._log.warning("Invalid command selection. Please try again.")
            return

        # Handle OSCAR commands separately
        if cmd_selection == "4":
            self.handle_oscar_commands()
            return

        message: dict[str, object] = {
            "name": self._config.cubesat_name,
        }

        if cmd_selection == "1":
            message["command"] = self._cdh.command_reset
        elif cmd_selection == "2":
            message["command"] = self._cdh.command_change_radio_modulation
            modulation = input("Enter new radio modulation [FSK | LoRa]: ")
            message["args"] = [modulation]
        elif cmd_selection == "3":
            message["command"] = self._cdh.command_send_joke

        # Increment counter for replay attack prevention
        self._command_counter += 1
        message["counter"] = self._command_counter

        # Generate HMAC for the message
        message_str = json.dumps(message, separators=(",", ":"))
        hmac_value = self._hmac_authenticator.generate_hmac(
            message_str, self._command_counter
        )
        message["hmac"] = hmac_value

        while True:
            # Turn on the radio so that it captures any received packets to buffer
            self._packet_manager.listen(1)

            # Send the message
            self._log.info(
                "Sending command",
                cmd=message["command"],
                args=message.get("args", []),
                counter=self._command_counter,
            )
            self._packet_manager.send(json.dumps(message).encode("utf-8"))

            # Listen for ACK response
            b = self._packet_manager.listen(1)
            if b is None:
                self._log.info("No response received, retrying...")
                continue

            if b != b"ACK":
                self._log.info(
                    "No ACK response received, retrying...",
                    response=b.decode("utf-8"),
                )
                continue

            self._log.info("Received ACK")

            # Now listen for the actual response
            b = self._packet_manager.listen(1)
            if b is None:
                self._log.info("No response received, retrying...")
                continue

            self._log.info("Received response", response=b.decode("utf-8"))
            break

    def handle_oscar_commands(self):
        """
        Handle OSCAR command selection and sending.
        """
        try:
            oscar_selection = input(
                """
            ===============================
            | Select OSCAR command        |
            | 1: Ping                     |
            | 2: Repeat message           |
            ===============================
            """
            )

            if oscar_selection not in ["1", "2"]:
                self._log.warning("Invalid OSCAR command selection. Please try again.")
                return

            message: dict[str, object] = {
                "password": self._cdh.oscar_password,
            }

            if oscar_selection == "1":
                message["command"] = "ping"
                message["args"] = []
            elif oscar_selection == "2":
                repeat_message = input("Enter message to repeat: ")
                if not repeat_message.strip():
                    self._log.warning("Empty message provided. Please try again.")
                    return
                message["command"] = "repeat"
                message["args"] = repeat_message.split()

            while True:
                # Turn on the radio so that it captures any received packets to buffer
                self._packet_manager.listen(1)

                # Send the OSCAR message
                self._log.info(
                    "Sending OSCAR command",
                    cmd=message["command"],
                    args=message.get("args", []),
                )
                self._packet_manager.send(json.dumps(message).encode("utf-8"))

                # Listen for ACK response
                b = self._packet_manager.listen(1)
                if b is None:
                    self._log.info("No response received, retrying...")
                    continue

                if b != b"ACK":
                    self._log.info(
                        "No ACK response received, retrying...",
                        response=b.decode("utf-8"),
                    )
                    continue

                self._log.info("Received ACK")

                # Now listen for the actual response
                b = self._packet_manager.listen(1)
                if b is None:
                    self._log.info("No response received, retrying...")
                    continue

                self._log.info("Received OSCAR response", response=b.decode("utf-8"))
                break

        except KeyboardInterrupt:
            self._log.debug("Keyboard interrupt received, exiting OSCAR mode.")

    def run(self):
        """Run the ground station interface."""
        # Prompt for starting counter value
        while True:
            try:
                counter_input = input(
                    "Enter starting counter value (0-65535, press Enter for 0): "
                ).strip()
                if counter_input == "":
                    self._command_counter = 0
                    break
                counter_value = int(counter_input)
                if 0 <= counter_value <= 65535:
                    self._command_counter = counter_value
                    self._log.info(f"Starting counter set to: {self._command_counter}")
                    break
                else:
                    print("Counter must be between 0 and 65535. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        while True:
            print(
                """
            =============================
            |                           |
            | WELCOME!                  |
            | PROVESKIT Ground Station  |
            |                           |
            =============================
            | Please Select Your Mode   |
            | 'A': Listen               |
            | 'B': Send                 |
            =============================
            """
            )

            device_selection = input().lower()

            if device_selection not in ["a", "b"]:
                self._log.warning("Invalid Selection. Please try again.")
                continue

            if device_selection == "a":
                self.listen()
            elif device_selection == "b":
                self.send_receive()

            time.sleep(1)
