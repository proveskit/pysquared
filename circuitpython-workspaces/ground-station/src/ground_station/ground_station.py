"""
PySquared Ground Station
"""

import json
import time

import supervisor
from pysquared.cdh import CommandDataHandler
from pysquared.config.config import Config
from pysquared.hardware.radio.packetizer.packet_manager import PacketManager
from pysquared.logger import Logger


class GroundStation:
    """Ground Station class to manage communication with the satellite."""

    def __init__(
        self,
        logger: Logger,
        config: Config,
        packet_manager: PacketManager,
        cdh: CommandDataHandler,
    ):
        self._log = logger
        self._log.colorized = True
        self._config = config
        self._packet_manager = packet_manager
        self._cdh = cdh

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
        if cmd_selection not in ["1", "2", "3"]:
            self._log.warning("Invalid command selection. Please try again.")
            return

        message: dict[str, object] = {
            "name": self._config.cubesat_name,
            "password": self._config.super_secret_code,
        }

        if cmd_selection == "1":
            message["command"] = self._cdh.command_reset
        elif cmd_selection == "2":
            message["command"] = self._cdh.command_change_radio_modulation
            modulation = input("Enter new radio modulation [FSK | LoRa]: ")
            message["args"] = [modulation]
        elif cmd_selection == "3":
            message["command"] = self._cdh.command_send_joke

        while True:
            # Turn on the radio so that it captures any received packets to buffer
            self._packet_manager.listen(1)

            # Send the message
            self._log.info(
                "Sending command",
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

            self._log.info("Received response", response=b.decode("utf-8"))
            break

    def run(self):
        """Run the ground station interface."""
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
