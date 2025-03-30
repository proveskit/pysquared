"""
This is the class that contains all of the functions for our CubeSat.
We pass the cubesat object to it for the definitions and then it executes
our will.
Authors: Nicole Maggard, Michael Pham, and Rachel Sarmiento
"""

import gc
import random
import time

from .config.config import Config
from .logger import Logger
from .packet_manager import PacketManager
from .packet_sender import PacketSender
from .protos.imu import IMUProto
from .protos.magnetometer import MagnetometerProto
from .protos.radio import RadioProto
from .satellite import Satellite
from .sleep_helper import SleepHelper

try:
    from typing import List, OrderedDict, Union
except Exception:
    pass


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
    ) -> None:
        self.cubesat: Satellite = cubesat
        self.logger: Logger = logger
        self.config: Config = config
        self.sleep_helper = sleep_helper
        self.radio: RadioProto = radio
        self.magnetometer: MagnetometerProto = magnetometer
        self.imu: IMUProto = imu

        self.logger.info("Initializing Functionalities")
        self.packet_manager: PacketManager = PacketManager(
            logger=self.logger, max_packet_size=128
        )
        self.packet_sender: PacketSender = PacketSender(
            self.logger, radio, self.packet_manager, max_retries=3
        )

        self.cubesat_name: str = config.cubesat_name
        self.facestring: list = [None, None, None, None, None]
        self.jokes: list[str] = config.jokes
        self.last_battery_temp: float = config.last_battery_temp
        self.sleep_duration: int = config.sleep_duration
        self.callsign: str = config.callsign
        self.state_of_health_part1: bool = False

    """
    Satellite Management Functions
    """

    def listen_loiter(self) -> None:
        self.logger.debug("Listening for 10 seconds")
        self.cubesat.watchdog_pet()
        self.radio.radio.receive_timeout = 10
        self.listen()
        self.cubesat.watchdog_pet()

        self.logger.debug("Sleeping for 20 seconds")
        self.cubesat.watchdog_pet()
        self.sleep_helper.safe_sleep(self.sleep_duration)
        self.cubesat.watchdog_pet()

    """
    Radio Functions
    """

    def send(self, msg: Union[str, bytearray]) -> None:
        """Calls the RFM9x to send a message. Currently only sends with default settings.

        Args:
            msg (String,Byte Array): Pass the String or Byte Array to be sent.
        """
        message: str = f"{self.callsign} " + str(msg) + f" {self.callsign}"
        self.radio.send(message)
        if self.cubesat.is_licensed:
            self.logger.debug("Sent Packet", packet_message=message)
        else:
            self.logger.warning("Failed to send packet")

    def send_packets(self, data: Union[str, bytearray]) -> None:
        """Sends packets of data over the radio with delay between packets.

        Args:
            data (String, Byte Array): Pass the data to be sent.
            delay (float): Delay in seconds between packets
        """
        self.packet_sender.send_data(data)

    def beacon(self) -> None:
        """Calls the RFM9x to send a beacon."""

        try:
            lora_beacon: str = (
                f"{self.callsign} Hello I am {self.cubesat_name}! I am: "
                + str(self.cubesat.power_mode)
                + f" UT:{self.cubesat.get_system_uptime} BN:{self.cubesat.boot_count.get()} EC:{self.logger.get_error_count()} "
                + f"IHBPFJASTMNE! {self.callsign}"
            )
        except Exception as e:
            self.logger.error("Error with obtaining power data: ", e)

            lora_beacon: str = (
                f"{self.callsign} Hello I am Yearling^2! I am in: "
                + "an unidentified"
                + " power mode. V_Batt = "
                + "Unknown"
                + f". IHBPFJASTMNE! {self.callsign}"
            )

        self.radio.send(lora_beacon)

    def joke(self) -> None:
        self.send(random.choice(self.jokes))

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
                f"MT:{self.cubesat.micro.cpu.temperature}",
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

        message: str = ""
        if not self.state_of_health_part1:
            message = (
                f"{self.callsign} Yearling^2 State of Health 1/2"
                + str(self.state_list)
                + f"{self.callsign}"
            )
            self.state_of_health_part1: bool = True
        else:
            message = (
                f"{self.callsign} YSOH 2/2"
                + self.format_state_of_health(self.cubesat.hardware)
                + f"{self.callsign}"
            )
            self.state_of_health_part1: bool = False

        self.radio.send(message)

    def send_face(self) -> None:
        """Calls the data transmit function from the radio manager class"""

        self.logger.debug("Sending Face Data")
        self.radio.send(
            f"{self.callsign} Y-: {self.facestring[0]} Y+: {self.facestring[1]} X-: {self.facestring[2]} X+: {self.facestring[3]}  Z-: {self.facestring[4]} {self.callsign}"
        )

    def listen(self) -> bool:
        # need to instanciate cdh to feed it the config var
        # assigned from the Config object
        from pysquared.cdh import CommandDataHandler

        cdh = CommandDataHandler(self.config, self.logger, self.radio)

        # This just passes the message through. Maybe add more functionality later.
        try:
            self.logger.debug("Listening")
            self.radio.radio.receive_timeout = 10
            received: bytearray = self.radio.radio.receive_with_ack(keep_listening=True)
        except Exception as e:
            self.logger.error("An Error has occured while listening: ", e)
            received = None

        try:
            if received is not None:
                self.logger.debug("Received Packet", packet=received)
                cdh.message_handler(self.cubesat, received)
                return True
        except Exception as e:
            self.logger.error("An Error has occured while handling a command: ", e)
        finally:
            del cdh

        return False

    def listen_joke(self) -> bool:
        try:
            self.logger.debug("Listening")
            self.radio.radio.receive_timeout = 10
            received: bytearray = self.radio.radio.receive(keep_listening=True)
            return received is not None and "HAHAHAHAHA!" in received

        except Exception as e:
            self.logger.error("An Error has occured while listening for a joke", e)
            return False

    """
    Big_Data Face Functions
    change to remove fet values, move to pysquared
    """

    def all_face_data(self) -> list:
        # self.cubesat.all_faces_on()
        gc.collect()
        self.logger.debug(
            "Free Memory Stat at beginning of all_face_data function",
            bytes_free=gc.mem_free(),
        )

        try:
            import pysquared.Big_Data as Big_Data

            self.logger.debug(
                "Free Memory Stat after importing Big_data library",
                bytes_free=gc.mem_free(),
            )

            gc.collect()
            a: Big_Data.AllFaces = Big_Data.AllFaces(self.cubesat.tca, self.logger)
            self.logger.debug(
                "Free Memory Stat after initializing All Faces object",
                bytes_free=gc.mem_free(),
            )

            self.facestring: list[list[float]] = a.face_test_all()

            del a
            del Big_Data
            gc.collect()

        except Exception as e:
            self.logger.error("Big_Data error", e)

        return self.facestring

    def get_imu_data(
        self,
    ) -> List[
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ]:
        try:
            data: List[
                tuple[float, float, float],
                tuple[float, float, float],
                tuple[float, float, float],
            ] = []
            data.append(self.imu.get_acceleration())
            data.append(self.imu.get_gyro_data())
            data.append(self.magnetometer.get_vector())
        except Exception as e:
            self.logger.error("Error retrieving IMU data", e)

        return data

    """
    Misc Functions
    """

    # Goal for torque is to make a control system
    # that will adjust position towards Earth based on Gyro data
    def detumble(self, dur: int = 7) -> None:
        self.logger.debug("Detumbling")

        try:
            import pysquared.Big_Data as Big_Data

            a: Big_Data.AllFaces = Big_Data.AllFaces(self.cubesat.tca, self.logger)
        except Exception as e:
            self.logger.error("Error Importing Big Data", e)

        try:
            a.sequence = 52
        except Exception as e:
            self.logger.error("Error setting motor driver sequences", e)

        def actuate(dipole: list[float], duration) -> None:
            # TODO figure out if there is a way to reverse direction of sequence
            if abs(dipole[0]) > 1:
                a.Face2.drive = 52
                a.drvx_actuate(duration)
            if abs(dipole[1]) > 1:
                a.Face0.drive = 52
                a.drvy_actuate(duration)
            if abs(dipole[2]) > 1:
                a.Face4.drive = 52
                a.drvz_actuate(duration)

        def do_detumble() -> None:
            try:
                import pysquared.detumble as detumble

                for _ in range(3):
                    # Hmmm cubesat.IMU.Gyroscope and cubesat.IMU.Magnetometer don't exist
                    data = [self.cubesat.IMU.Gyroscope, self.cubesat.IMU.Magnetometer]
                    data[0] = list(data[0])
                    for x in range(3):
                        if data[0][x] < 0.01:
                            data[0][x] = 0.0
                    data[0] = tuple(data[0])
                    dipole = detumble.magnetorquer_dipole(data[1], data[0])
                    self.logger.debug("Detumbling", dipole=dipole)
                    self.send("Detumbling! Gyro, Mag: " + str(data))
                    time.sleep(1)
                    actuate(dipole, dur)
            except Exception as e:
                self.logger.error("Detumble error", e)

        try:
            self.logger.debug("Attempting")
            do_detumble()
        except Exception as e:
            self.logger.error("Detumble error", e)
