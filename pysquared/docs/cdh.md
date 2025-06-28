# Command and Data Handling

### cdh Module
This module provides the `CommandDataHandler` class for managing and processing commands received by the satellite, including command parsing, execution, and radio communication handling.

#### Imports
```py title="cdh.py"
import random
import time

import alarm
import microcontroller
from alarm import time as alarmTime

from .config.config import Config
from .logger import Logger
from .protos.radio import RadioProto
from .satellite import Satellite
```

### CommandDataHandler Class
Handles command parsing, validation, and execution for the satellite.

#### Attributes
- **_log** (Logger): Logger instance for logging events and errors.
- **_radio** (RadioProto): Radio interface for communication.
- **_commands** (dict[bytes, str]): Mapping of command codes to handler method names.
- **_joke_reply** (list[str]): List of joke replies for the joke_reply command.
- **_super_secret_code** (bytes): Passcode required for command execution.
- **_repeat_code** (bytes): Passcode for repeating the last message.
- **config** (Config): Configuration object.

### Initialization of CommandDataHandler Instance

#### Arguments
- **config** (Config): Configuration object with command settings.
- **logger** (Logger): Logger instance for logging events and errors.
- **radio** (RadioProto): Radio interface for communication.

```py title="cdh.py"
def __init__(self, config: Config, logger: Logger, radio: RadioProto) -> None:
    self._log: Logger = logger
    self._radio: RadioProto = radio
    self._commands: dict[bytes, str] = {
        b"\x8eb": "noop",
        b"\xd4\x9f": "hreset",
        b"\x12\x06": "shutdown",
        b"8\x93": "query",
        b"\x96\xa2": "exec_cmd",
        b"\xa5\xb4": "joke_reply",
        b"\x56\xc4": "FSK",
    }
    self._joke_reply: list[str] = config.joke_reply
    self._super_secret_code: bytes = config.super_secret_code.encode("utf-8")
    self._repeat_code: bytes = config.repeat_code.encode("utf-8")
    self.config = config
    self._log.info(
        "The satellite has a super secret code!",
        super_secret_code=str(self._super_secret_code),
    )
```

### Handling Incoming Messages

#### Arguments
- **cubesat** (Satellite): The satellite instance.
- **msg** (bytearray): The received message.

```py title="cdh.py"
def message_handler(self, cubesat: Satellite, msg: bytearray) -> None:
    multi_msg: bool = False
        if len(msg) >= 10:  # [RH header 4 bytes] [pass-code(4 bytes)] [cmd 2 bytes]
            if bytes(msg[4:8]) == self._super_secret_code:
                # check if multi-message flag is set
                if msg[3] & 0x08:
                    multi_msg = True
                # strip off RH header
                msg = bytes(msg[4:])
                cmd = msg[4:6]  # [pass-code(4 bytes)] [cmd 2 bytes] [args]
                cmd_args: bytes | None = None
                if len(msg) > 6:
                    self._log.info("This is a command with args")
                try:
                    cmd_args = msg[6:]  # arguments are everything after
                    self._log.info("Here are the command arguments", cmd_args=cmd_args)
                except Exception as e:
                    self._log.error("There was an error decoding the arguments", e)
            if cmd in self._commands:
                try:
                    if cmd_args is None:
                        self._log.info(
                            "There are no args provided", command=self._commands[cmd]
                        )
                        # eval a string turns it into a func name
                        eval(self._commands[cmd])(cubesat)
                    else:
                        self._log.info(
                            "running command with args",
                            command=self._commands[cmd],
                            cmd_args=cmd_args,
                        )
                    eval(self._commands[cmd])(cubesat, cmd_args)
                except Exception as e:
                    self._log.error("something went wrong!", e)
                    self._radio.send(str(e).encode())
            else:
                self._log.info("invalid command!")
                self._radio.send(b"invalid cmd" + msg[4:])
                # check for multi-message mode
                if multi_msg:
                    # TODO check for optional radio config
                    self._log.info("multi-message mode enabled")
                response = self._radio.receive()
                if response is not None:
                    self.message_handler(cubesat, response)
        elif bytes(msg[4:6]) == self._repeat_code:
            self._log.info("Repeating last message!")
            try:
                self._radio.send(msg[6:])
            except Exception as e:
                self._log.error("There was an error repeating the message!", e)
        else:
            self._log.info("bad code?")
```

### Command Methods

#### No-Operation Command

```py title="cdh.py"
def noop(self) -> None:
    self.logger.info("no-op")
```

#### Hardware Reset Command

##### Arguments
- **cubesat** (Satellite): The satellite instance.

```py title="cdh.py"
def hreset(self, cubesat: Satellite) -> None:
    self.logger.info("Resetting")
    try:
        self._radio.send(data=b"resetting")
        microcontroller.on_next_reset(microcontroller.RunMode.NORMAL)
        microcontroller.reset()
    except Exception:
        pass
```

#### Joke Reply Command

##### Arguments
- **cubesat** (Satellite): The satellite instance.

```py title="cdh.py"
def joke_reply(self, cubesat: Satellite) -> None:
    joke: str = random.choice(self._joke_reply)
    self._log.info("Sending joke reply", joke=joke)
    self._radio.send(joke)
```

#### Shutdown Command

##### Arguments
- **cubesat** (Satellite): The satellite instance.
- **args** (bytes): Arguments for the shutdown command.

```py title="cdh.py"
def shutdown(self, cubesat: Satellite, args: bytes) -> None:
    if args != b"\x0b\xfdI\xec":
        return

    self._log.info("valid shutdown command received")
    cubesat.f_shtdwn.toggle(True)

    # Exercise for the user:
    #     Implement a means of waking up from shutdown
    #     See beep-sat guide for more details
    #     https://pycubed.org/resources

    _t = 5
    time_alarm: alarmTime.TimeAlarm = alarmTime.TimeAlarm(
        monotonic_time=time.monotonic() + eval("1e" + str(_t))
    )  # default 1 day
    alarm.exit_and_deep_sleep_until_alarms(time_alarm)
```

#### Query Command

##### Arguments
- **cubesat** (Satellite): The satellite instance.
- **args** (str): Arguments to be evaluated and sent.

```py title="cdh.py"
def query(self, cubesat: Satellite, args: str) -> None:
    self._log.info("Sending query with args", args=args)
    self._radio.send(data=str(eval(args)))
```

#### Execute Command

##### Arguments
- **cubesat** (Satellite): The satellite instance.
- **args** (str): Command to execute.

```py title="cdh.py"
def exec_cmd(self, cubesat: Satellite, args: str) -> None:
    self.logger.info("Executing command", args=args)
    exec(args)
```

#### Update Config Command

##### Arguments
- **cubesat** (Satellite): The satellite instance.
- **args** (str): Configuration update arguments.

```py title="cdh.py"
def update_config(self, cubesat: Satellite, args: str) -> None:
    temporary: bool = False
    key: str = ""
    value = ""

    try:
        self.config.update_config(key, value, temporary)
        self._log.info("Updated config value successfully")
    except KeyError as e:
        self._log.error("Value not in config or immutable", e)
    except TypeError as e:
        self._log.error("Value type incorrect", e)
    except ValueError as e:
        self._log.error("Value not in acceptable range", e)
```
