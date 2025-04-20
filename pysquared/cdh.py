import random
import time

import alarm
import microcontroller
from alarm import time as alarmTime

from .config.config import Config
from .hardware.radio.modulation import FSK
from .logger import Logger
from .protos.radio import RadioProto
from .satellite import Satellite

try:
    pass
except Exception:
    pass


class CommandDataHandler:
    """
    Constructor
    """

    def __init__(
        self,
        config: Config,
        logger: Logger,
        radio: RadioProto,
    ) -> None:
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
        self._log.info(
            "The satellite has a super secret code!",
            super_secret_code=str(self._super_secret_code),
        )

    ############### message handler ###############
    def message_handler(self, cubesat: Satellite, msg: bytes) -> None:
        cmd: bytes | None = None
        cmd_args: bytes | None = None
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

    ########### commands without arguments ###########
    def noop(self) -> None:
        self._log.info("no-op")

    def hreset(self, cubesat: Satellite) -> None:
        self._log.info("Resetting")
        try:
            self._radio.send(data=b"resetting")
            microcontroller.on_next_reset(microcontroller.RunMode.NORMAL)
            microcontroller.reset()
        except Exception:
            pass

    def fsk(self) -> None:
        self._radio.set_modulation(FSK)

    def joke_reply(self, cubesat: Satellite) -> None:
        joke: str = random.choice(self._joke_reply)
        self._log.info("Sending joke reply", joke=joke)
        self._radio.send(joke)

    ########### commands with arguments ###########

    def shutdown(self, cubesat: Satellite, args: bytes) -> None:
        # make shutdown require yet another pass-code
        if args != b"\x0b\xfdI\xec":
            return

        # This means args does = b"\x0b\xfdI\xec"
        self._log.info("valid shutdown command received")
        # set shutdown NVM bit flag
        cubesat.f_shtdwn.toggle(True)

        """
        Exercise for the user:
            Implement a means of waking up from shutdown
            See beep-sat guide for more details
            https://pycubed.org/resources
        """

        # deep sleep + listen
        # TODO config radio
        # What was "st" in cubesat.radio_cfg?
        # Maybe "sleep time"?
        # self._radio.receive()
        # if "st" in cubesat.radio_cfg:
        #     _t: float = cubesat.radio_cfg["st"]
        # else:
        #     _t = 5

        _t = 5
        time_alarm: alarmTime.TimeAlarm = alarmTime.TimeAlarm(
            monotonic_time=time.monotonic() + eval("1e" + str(_t))
        )  # default 1 day
        alarm.exit_and_deep_sleep_until_alarms(time_alarm)

    def query(self, cubesat: Satellite, args: str) -> None:
        self._log.info("Sending query with args", args=args)

        self._radio.send(data=str(eval(args)))

    def exec_cmd(self, cubesat: Satellite, args: str) -> None:
        self._log.info("Executing command", args=args)
        exec(args)
