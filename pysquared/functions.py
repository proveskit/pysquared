"""
This is the class that contains all of the functions for our CubeSat.
We pass the cubesat object to it for the definitions and then it executes
our will.
Authors: Nicole Maggard, Michael Pham, and Rachel Sarmiento
"""

import random

import microcontroller

from .cdh import CommandDataHandler
from .config.config import Config
from .logger import Logger
from .packet_manager import PacketManager
from .packet_sender import PacketSender
from .protos.radio import RadioProto
from .sleep_helper import SleepHelper
from .watchdog import Watchdog


class functions:
    def __init__(
        self,
        logger: Logger,
        config: Config,
        sleep_helper: SleepHelper,
        radio: RadioProto,
        watchdog: Watchdog,
        cdh: CommandDataHandler,
    ) -> None:
        self._log: Logger = logger
        self.sleep_helper = sleep_helper
        self.radio: RadioProto = radio
        self.watchdog: Watchdog = watchdog
        self.cdh: CommandDataHandler = cdh

        self._log.info("Initializing Functionalities")
        self.packet_manager: PacketManager = PacketManager(
            logger=self._log, max_packet_size=128
        )
        self.packet_sender: PacketSender = PacketSender(
            self._log, radio, self.packet_manager, max_retries=3
        )

        self.jokes: list[str] = config.jokes
        self.sleep_duration: int = config.sleep_duration

        """
        Set the CPU Clock Speed
        """
        cpu_freq: int = 125000000 if config.turbo_clock else 62500000
        for cpu in microcontroller.cpus:  # type: ignore # Needs fix in CircuitPython stubs
            cpu.frequency = cpu_freq

    """
    Satellite Management Functions
    """

    def listen_loiter(self) -> None:
        self._log.debug("Listening for 10 seconds")
        self.watchdog.pet()
        self.listen()
        self.watchdog.pet()

        self._log.debug("Sleeping for 20 seconds")
        self.watchdog.pet()
        self.sleep_helper.safe_sleep(self.sleep_duration)
        self.watchdog.pet()

    def joke(self) -> None:
        self.radio.send(random.choice(self.jokes))

    def listen(self) -> bool:
        # This just passes the message through. Maybe add more functionality later.
        try:
            self._log.debug("Listening")
            received: bytes | None = self.radio.receive()
        except Exception as e:
            self._log.error("An Error has occured while listening: ", e)
            received = None

        try:
            if received is not None:
                self._log.debug("Received Packet", packet=received)
                self.cdh.message_handler(received)
                return True
        except Exception as e:
            self._log.error("An Error has occured while handling a command: ", e)

        return False
