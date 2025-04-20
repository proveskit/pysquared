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
from .protos.imu import IMUProto
from .protos.magnetometer import MagnetometerProto
from .protos.radio import RadioProto
from .satellite import Satellite
from .sleep_helper import SleepHelper
from .watchdog import Watchdog

try:
    from typing import OrderedDict
except Exception:
    pass


class functions:
    facestring: list[list[float]]

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
        self.last_battery_temp: float = config.last_battery_temp
        self.sleep_duration: int = config.sleep_duration

    """
    Satellite Management Functions
    """

    def listen_loiter(self) -> None:
        self.logger.debug("Listening for 10 seconds")
        self.watchdog.pet()
        self.listen()
        self.watchdog.pet()

        self.logger.debug("Sleeping for 20 seconds")
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

    def format_state_of_health(self, hardware: OrderedDict[str, bool]) -> str:
        to_return: str = ""
        for key, value in hardware.items():
            to_return = to_return + key + "="
            if value:
                to_return += "1"
            else:
                to_return += "0"

            if len(to_return) > 245:
                return to_return

        return to_return

    def state_of_health(self) -> None:
        self.state_list: list = []
        # list of state information
        try:
            self.state_list: list[str] = [
                f"PM:{self.cubesat.power_mode}",
                f"VB:{self.cubesat.battery_voltage}",
                f"ID:{self.cubesat.current_draw}",
                f"IC:{self.cubesat.charge_current}",
                f"UT:{self.cubesat.get_system_uptime}",
                f"BN:{self.cubesat.boot_count.get()}",
                f"MT:{microcontroller.cpu.temperature}",
                f"RT:{self.radio.get_temperature()}",
                f"AT:{self.imu.get_temperature()}",
                f"BT:{self.last_battery_temp}",
                f"EC:{self.logger.get_error_count()}",
                f"AB:{int(self.cubesat.f_burned.get())}",
                f"BO:{int(self.cubesat.f_brownout.get())}",
                f"FK:{self.radio.get_modulation()}",
            ]
        except Exception as e:
            self.logger.error("Couldn't aquire data for the state of health: ", e)

        self.radio.send("State of Health " + str(self.state_list))

    def send_face(self) -> None:
        """Calls the data transmit function from the radio manager class"""

        self.logger.debug("Sending Face Data")
        self.radio.send(
            f"{self.config.radio.license} Y-: {self.facestring[0]} Y+: {self.facestring[1]} X-: {self.facestring[2]} X+: {self.facestring[3]}  Z-: {self.facestring[4]} {self.config.radio.license}"
        )

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

    def listen_joke(self) -> bool:
        try:
            self.logger.debug("Listening")
            received: bytes | None = self.radio.receive()
            return received is not None and b"HAHAHAHAHA!" in received

        except Exception as e:
            self.logger.error("An Error has occured while listening for a joke", e)
            return False
