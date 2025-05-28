import random
import time

from .config.config import Config
from .hardware.rfm9x.manager import RFM9xManager
from .hardware.rfm9x.modulation import RFM9xModulation
from .logger import Logger
from .pysquared import Satellite

try:
    from typing import Any, Union

    import circuitpython_typing
except Exception:
    pass

'''
cdh Module
==========

This module provides the CommandDataHandler class for managing and processing
commands received by the satellite, including command parsing, execution,
and radio communication handling.
'''

class CommandDataHandler:
    '''
    Handles command parsing, validation, and execution for the satellite.

    Attributes:
        logger (Logger): Logger instance for logging events and errors.
        _commands (dict[bytes, str]): Mapping of command codes to handler method names.
        _joke_reply (list[str]): List of joke replies for the joke_reply command.
        _super_secret_code (bytes): Passcode required for command execution.
        _repeat_code (bytes): Passcode for repeating the last message.
        radio_manager (RFM9xManager): Radio manager for communication.
    '''

    def __init__(
        self,
        config: Config,
        logger: Logger,
        radio_manager: RFM9xManager,
    ) -> None:
        '''
        Initializes a CommandDataHandler instance.

        Args:
            config (Config): Configuration object with command settings.
            logger (Logger): Logger instance for logging events and errors.
            radio_manager (RFM9xManager): Radio manager for communication.
        '''
        self.logger: Logger = logger
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
        self.logger.info(
            "The satellite has a super secret code!",
            super_secret_code=self._super_secret_code,
        )

        self.radio_manager = radio_manager

    ############### hot start helper ###############
    def hotstart_handler(self, cubesat: Satellite, msg: Any) -> None:
        '''
        Handles hot start messages, sending ACK and processing the message if addressed to this node.

        Args:
            cubesat (Satellite): The satellite instance.
            msg (Any): The received message.
        '''
        # check that message is for me
        if msg[0] == self.radio_manager.radio.node:
            # TODO check for optional radio config

            # manually send ACK
            self.radio_manager.radio.send("!", identifier=msg[2], flags=0x80)
            # TODO remove this delay. for testing only!
            time.sleep(0.5)
            self.message_handler(cubesat, msg)
        else:
            self.logger.info(
                "Message not for me?",
                target_id=hex(msg[0]),
                my_id=hex(self.radio_manager.radio.node),
            )

    ############### message handler ###############
    def message_handler(self, cubesat: Satellite, msg: bytearray) -> None:
        '''
        Parses and handles incoming messages, executing commands if valid.

        Args:
            cubesat (Satellite): The satellite instance.
            msg (bytearray): The received message.
        '''
        multi_msg: bool = False
        if len(msg) >= 10:  # [RH header 4 bytes] [pass-code(4 bytes)] [cmd 2 bytes]
            if bytes(msg[4:8]) == self._super_secret_code:
                # check if multi-message flag is set
                if msg[3] & 0x08:
                    multi_msg = True
                # strip off RH header
                msg: bytes = bytes(msg[4:])
                cmd: bytes = msg[4:6]  # [pass-code(4 bytes)] [cmd 2 bytes] [args]
                cmd_args: Union[bytes, None] = None
                if len(msg) > 6:
                    self.logger.info("This is a command with args")
                try:
                    cmd_args = msg[6:]  # arguments are everything after
                    self.logger.info(
                        "Here are the command arguments", cmd_args=cmd_args
                    )
                except Exception as e:
                    self.logger.error("There was an error decoding the arguments", e)
            if cmd in self._commands:
                try:
                    if cmd_args is None:
                        self.logger.info(
                            "There are no args provided", command=self._commands[cmd]
                        )
                        # eval a string turns it into a func name
                        eval(self._commands[cmd])(cubesat)
                    else:
                        self.logger.info(
                            "running command with args",
                            command=self._commands[cmd],
                            cmd_args=cmd_args,
                        )
                    eval(self._commands[cmd])(cubesat, cmd_args)
                except Exception as e:
                    self.logger.error("something went wrong!", e)
                    self.radio_manager.radio.send(str(e).encode())
            else:
                self.logger.info("invalid command!")
                self.radio_manager.radio.send(b"invalid cmd" + msg[4:])
                # check for multi-message mode
                if multi_msg:
                    # TODO check for optional radio config
                    self.logger.info("multi-message mode enabled")
                response = self.radio_manager.radio.receive(
                    keep_listening=True,
                    with_ack=True,
                    with_header=True,
                    view=True,
                    timeout=10,
                )
                if response is not None:
                    cubesat.c_gs_resp += 1
                    self.message_handler(cubesat, response)
        elif bytes(msg[4:6]) == self._repeat_code:
            self.logger.info("Repeating last message!")
            try:
                self.radio_manager.radio.send(msg[6:])
            except Exception as e:
                self.logger.error("There was an error repeating the message!", e)
        else:
            self.logger.info("bad code?")

    ########### commands without arguments ###########
    def noop(self) -> None:
        '''
        No-operation command. Logs a no-op event.
        '''
        self.logger.info("no-op")

    def hreset(self, cubesat: Satellite) -> None:
        '''
        Handles hardware reset command, sending a reset message and triggering a reset.

        Args:
            cubesat (Satellite): The satellite instance.
        '''
        self.logger.info("Resetting")
        try:
            self.radio_manager.radio.send(data=b"resetting")
            cubesat.micro.on_next_reset(cubesat.micro.RunMode.NORMAL)
            cubesat.micro.reset()
        except Exception:
            pass

    def fsk(self) -> None:
        '''
        Sets the radio modulation to FSK.
        '''
        self.radio_manager.set_modulation(RFM9xModulation.FSK)

    def joke_reply(self, cubesat: Satellite) -> None:
        '''
        Sends a random joke reply over the radio.

        Args:
            cubesat (Satellite): The satellite instance.
        '''
        joke: str = random.choice(self._joke_reply)
        self.logger.info("Sending joke reply", joke=joke)
        self.radio_manager.radio.send(joke)

    ########### commands with arguments ###########

    def shutdown(self, cubesat: Satellite, args: bytes) -> None:
        '''
        Handles the shutdown command, requiring a secondary pass-code and entering deep sleep.

        Args:
            cubesat (Satellite): The satellite instance.
            args (bytes): Arguments for the shutdown command.
        '''
        # make shutdown require yet another pass-code
        if args != b"\x0b\xfdI\xec":
            return

        # This means args does = b"\x0b\xfdI\xec"
        self.logger.info("valid shutdown command received")
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
        self.radio_manager.radio.listen()
        if "st" in cubesat.radio_cfg:
            _t: float = cubesat.radio_cfg["st"]
        else:
            _t = 5
        import alarm

        time_alarm: circuitpython_typing.Alarm = alarm.time.TimeAlarm(
            monotonic_time=time.monotonic() + eval("1e" + str(_t))
        )  # default 1 day
        # set hot start flag right before sleeping
        cubesat.f_hotstrt.toggle(True)
        alarm.exit_and_deep_sleep_until_alarms(time_alarm)

    def query(self, cubesat: Satellite, args: str) -> None:
        '''
        Handles the query command, evaluating and sending the result.

        Args:
            cubesat (Satellite): The satellite instance.
            args (str): Arguments to be evaluated and sent.
        '''
        self.logger.info("Sending query with args", args=args)

        self.radio_manager.radio.send(data=str(eval(args)))

    def exec_cmd(self, cubesat: Satellite, args: str) -> None:
        '''
        Executes a command provided in the arguments.

        Args:
            cubesat (Satellite): The satellite instance.
            args (str): Command to execute.
        '''
        self.logger.info("Executing command", args=args)
        exec(args)
