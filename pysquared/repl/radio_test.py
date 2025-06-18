import json
import time

from ..cdh import CommandDataHandler
from ..config.config import Config
from ..hardware.radio.packetizer.packet_manager import PacketManager
from ..logger import Logger


class RadioTest:
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
        try:
            while True:
                b = self._packet_manager.listen(3)
                if b is not None:
                    self._log.info(
                        "Received message",
                        header=self._packet_manager._get_header(b),
                        payload=self._packet_manager._get_payload(b),
                        length=len(b),
                    )
        except KeyboardInterrupt:
            self._log.debug("Keyboard interrupt received, exiting listen mode.")

    def send_receive(self):
        try:
            cmd_selection = input(
                """
            ====================================================
            | Select command to send                           |
            | 1: Reset                                         |
            | 2: Change radio modulation                       |
            | 3: Send joke                                     |
            ====================================================
            """
            )
            if cmd_selection not in ["1", "2", "3"]:
                self._log.warning("Invalid command selection. Please try again.")
                return

            message = {
                "password": self._config.super_secret_code,
            }

            if cmd_selection == "1":
                message["command"] = self._cdh.command_reset
            elif cmd_selection == "2":
                message["command"] = self._cdh.command_change_radio_modulation
                modulation = input("Enter new radio modulation [FSK | LoRa]: ")
                message["args"] = f"[{modulation}]"
            elif cmd_selection == "3":
                message["command"] = self._cdh.command_send_joke

            while True:
                # Turn on the radio so that it captures any received packets to buffer
                self._packet_manager.listen(0)

                # Send the message
                self._packet_manager.send(json.dumps(message).encode("utf-8"))

                # Listen for ACK response
                response = self._packet_manager.listen(1)
                if response is not None and response.startswith(b"ACK"):
                    self._log.info("Received ACK")
                    break
                else:
                    self._log.warning("No ACK response received, retrying...")

            self.listen()
        except KeyboardInterrupt:
            self._log.debug("Keyboard interrupt received, exiting send mode.")

    def run(self):
        while True:
            print(
                """
            ====================================================
            |                                                  |
            | WELCOME!                                         |
            | Pysquared Radio Test                             |
            |                                                  |
            ====================================================
            | Please Select Your Mode                          |
            | 'A': Listen only                                 |
            | 'B': Send/Listen                                 |
            ====================================================
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
