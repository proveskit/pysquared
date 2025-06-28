# Satellite Operations Functions

### functions Module
This module provides the `functions` class, which contains all operational functions for the CubeSat. It manages radio communication, state of health, face data, detumbling, and other satellite operations.

#### Imports
```py title="functions.py"
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
```

### functions Class
Provides operational functions for the CubeSat, including radio communication, state of health reporting, face data management, and detumbling.

#### Attributes
- **cubesat** (Satellite): The main satellite object.
- **logger** (Logger): Logger instance for logging events and errors.
- **config** (Config): Configuration object.
- **sleep_helper** (SleepHelper): Helper for safe sleep operations.
- **radio** (RadioProto): Radio interface for communication.
- **magnetometer** (MagnetometerProto): Magnetometer interface.
- **imu** (IMUProto): IMU interface.
- **watchdog** (Watchdog): Watchdog instance for system safety.
- **cdh** (CommandDataHandler): Command handler for incoming messages.
- **packet_manager** (PacketManager): Handles packet creation and management.
- **packet_sender** (PacketSender): Handles sending packets with retries.
- **cubesat_name** (str): Name of the CubeSat.
- **jokes** (list[str]): List of jokes for transmission.
- **sleep_duration** (int): Default sleep duration.

### Initialization of functions Instance

#### Arguments
- **cubesat** (Satellite): The main satellite object.
- **logger** (Logger): Logger instance for logging events and errors.
- **config** (Config): Configuration object.
- **sleep_helper** (SleepHelper): Helper for safe sleep operations.
- **radio** (RadioProto): Radio interface for communication.
- **magnetometer** (MagnetometerProto): Magnetometer interface.
- **imu** (IMUProto): IMU interface.
- **watchdog** (Watchdog): Watchdog instance for system safety.
- **cdh** (CommandDataHandler): Command handler for incoming messages.

```py title="functions.py"
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
    ...
```

### Satellite Management Functions

#### Function: `listen_loiter`
Listens for incoming messages for a set duration, then sleeps.

```py title="functions.py"
def listen_loiter(self) -> None:
    self.logger.debug("Listening for 10 seconds")
    self.watchdog.pet()
    self.listen()
    self.watchdog.pet()
    self.logger.debug("Sleeping!", duration=self.sleep_duration)
    self.watchdog.pet()
    self.sleep_helper.safe_sleep(self.sleep_duration)
    self.watchdog.pet()
```

### Radio Functions

#### Function: `beacon`
Sends a beacon message with CubeSat status and telemetry.

```py title="functions.py"
def beacon(self) -> None:
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
```

#### Function: `joke`
Sends a random joke over the radio.

```py title="functions.py"
def joke(self) -> None:
    self.radio.send(random.choice(self.jokes))
```

#### Function: `format_state_of_health`
Formats the hardware state dictionary into a string for transmission.

##### Arguments
- **hardware** (OrderedDict[str, bool]): Hardware state dictionary.

##### Returns
- **str**: Formatted state string.

```py title="functions.py"
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
```

#### Function: `state_of_health`
Collects and sends state of health (SOH) data over the radio.

```py title="functions.py"
def state_of_health(self) -> None:
    self.state_list: list = []
    try:
        self.state_list: list[str] = [
            f"PM:{self.cubesat.power_mode}",
            f"IC:{self.cubesat.charge_current}",
            f"UT:{self.cubesat.get_system_uptime}",
            f"BN:{self.cubesat.boot_count.get()}",
            f"MT:{microcontroller.cpu.temperature}",
            f"RT:{self.radio.get_temperature()}",
            f"AT:{self.imu.get_temperature()}",
            f"EC:{self.logger.get_error_count()}",
            f"AB:{int(self.cubesat.f_burned.get())}",
            f"BO:{int(self.cubesat.f_brownout.get())}",
            f"FK:{self.radio.get_modulation()}",
        ]
    except Exception as e:
        self.logger.error("Couldn't aquire data for the state of health: ", e)
    self.radio.send("State of Health " + str(self.state_list))
```

#### Function: `listen`
Listens for incoming radio messages and passes them to the command handler.

##### Returns
- **bool**: True if a message was received and handled, False otherwise.

```py title="functions.py"
def listen(self) -> bool:
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
```
