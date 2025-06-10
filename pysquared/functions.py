"""
This is the class that contains all of the functions for our CubeSat.
We pass the cubesat object to it for the definitions and then it executes
our will.
Authors: Nicole Maggard, Michael Pham, and Rachel Sarmiento
"""

import random

from .cdh import CommandDataHandler
from .config.config import Config
from .logger import Logger
from .packet_manager import PacketManager
from .packet_sender import PacketSender
from .protos.imu import IMUProto
from .protos.magnetometer import MagnetometerProto
from .protos.radio import RadioProto
from .satellite import Satellite
from .sleep_helper import SleepHelper
from .watchdog import Watchdog


class functions:
    def __init__(
        self,
        cubesat: Satellite,
        logger: Logger,
        config: Config,
        sleep_helper: SleepHelper,
        radio: RadioProto,
        magnetometer: MagnetometerProto,
        imu: IMUProto,
        watchdog: Watchdog,
        cdh: CommandDataHandler,
    ) -> None:
        self.cubesat: Satellite = cubesat
        self.logger: Logger = logger
        self.config: Config = config
        self.sleep_helper = sleep_helper
        self.radio: RadioProto = radio
        self.magnetometer: MagnetometerProto = magnetometer
        self.imu: IMUProto = imu
        self.watchdog: Watchdog = watchdog
        self.cdh: CommandDataHandler = cdh

        self.logger.info("Initializing Functionalities")
        self.packet_manager: PacketManager = PacketManager(
            logger=self.logger, max_packet_size=128
        )
        self.packet_sender: PacketSender = PacketSender(
            self.logger, radio, self.packet_manager, max_retries=3
        )

        self.cubesat_name: str = config.cubesat_name
        self.jokes: list[str] = config.jokes
        # self.last_battery_temp: float = config.last_battery_temp
        self.sleep_duration: int = config.sleep_duration

    """
    Satellite Management Functions
    """

    def listen_loiter(self) -> None:
        self.logger.debug("Listening for 10 seconds")
        self.watchdog.pet()
        self.listen()
        self.watchdog.pet()

        self.logger.debug("Sleeping!", duration=self.sleep_duration)
        self.watchdog.pet()
        self.sleep_helper.safe_sleep(self.sleep_duration)
        self.watchdog.pet()

    """
    Radio Functions
    """

    def beacon(self) -> None:
        """Calls the radio to send a beacon."""

        try:
            lora_beacon: str = (
                f"{self.config.radio.license} Hello I am {self.cubesat_name}! I am: "
                + str(self.cubesat.power_mode)
                + f" UT:{self.cubesat.get_system_uptime} BN:{self.cubesat.boot_count.get()} EC:{self.logger.get_error_count()} "
                + f"IHBPFJASTMNE! {self.config.radio.license}"
            )
        except Exception as e:
            self.logger.error("Error with obtaining power data: ", e)

            lora_beacon: str = (
                f"{self.config.radio.license} Hello I am Yearling^2! I am in: "
                + "an unidentified"
                + " power mode. V_Batt = "
                + "Unknown"
                + f". IHBPFJASTMNE! {self.config.radio.license}"
            )

        self.radio.send(lora_beacon)

    def joke(self) -> None:
        self.radio.send(random.choice(self.jokes))

    def listen(self) -> bool:
        # This just passes the message through. Maybe add more functionality later.
        try:
            self.logger.debug("Listening")
            received: bytes | None = self.radio.receive()
        except Exception as e:
            self.logger.error("An Error has occured while listening: ", e)
            received = None

        try:
            if received is not None:
                self.logger.debug("Received Packet", packet=received)
                self.cdh.message_handler(self.cubesat, received)
                return True
        except Exception as e:
            self.logger.error("An Error has occured while handling a command: ", e)

        return False
