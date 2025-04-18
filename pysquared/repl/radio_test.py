import time

from ..logger import Logger
from ..protos.radio import RadioProto


class RadioTest:
    test_message = "Hello There!"

    def __init__(
        self,
        logger: Logger,
        radio: RadioProto,
    ):
        self._log = logger
        self._log.colorized = True
        self._radio = radio

    def device_under_test(self):
        self._log.debug("Device Under Test Selected")
        self._log.debug("Sending Ping...")

        self._radio.send(self.test_message)

        self._log.debug("Ping Sent")
        self._log.debug("Awaiting Response...")

        heard_something = self._radio.receive(timeout=10)

        if heard_something:
            self._log.info("Received Ping!", msg=heard_something)
            self.handle_ping()
        else:
            self._log.debug("No Response Received")

    def receiver(self):
        self._log.debug("Receiver Selected")
        self._log.debug("Awaiting Ping...")

        heard_something = self._radio.receive(timeout=10)

        if heard_something:
            self._log.info("Received Ping!", msg=heard_something)
            self.handle_ping()

        else:
            self._radio.send("No Response Received")

    def client(self, passcode):
        self._log.debug("Client Selected")
        self._log.debug("Setting up radio")

        print(
            """
        =============== /\\ ===============
        = Please select command  :)      =
        ==================================
        1 - noop                         |
        2 - hreset                       |
        3 - shutdown                     |
        4 - query                        |
        5 - exec_cmd                     |
        6 - joke_reply                   |
        7 - FSK                          |
        8 - Repeat Code                  |
        ==================================
        """
        )

        chosen_command = input("Select cmd pls: ")

        packet = b""

        if chosen_command == "1":
            packet = b"\x00\x00\x00\x00" + passcode.encode() + b"\x8eb"
        elif chosen_command == "2":
            packet = b"\x00\x00\x00\x00" + passcode.encode() + b"\xd4\x9f"
        elif chosen_command == "3":
            packet = (
                b"\x00\x00\x00\x00" + passcode.encode() + b"\x12\x06" + b"\x0b\xfdI\xec"
            )
        elif chosen_command == "4":
            packet = b"\x00\x00\x00\x00" + passcode.encode() + b"8\x93" + input()
        elif chosen_command == "5":
            packet = (
                b"\x00\x00\x00\x00"
                + passcode.encode()
                + b"\x96\xa2"
                + input("Command: ")
            )
        elif chosen_command == "6":
            packet = b"\x00\x00\x00\x00" + passcode.encode() + b"\xa5\xb4"
        elif chosen_command == "7":
            packet = b"\x00\x00\x00\x00" + passcode.encode() + b"\x56\xc4"
        elif chosen_command == "8":
            packet = (
                b"\x00\x00\x00\x00"
                + passcode.encode()
                + b"RP"
                + input("Message to Repeat: ")
            )
        else:
            self._log.warning(
                "Command is not valid or not implemented open radio_test.py and add them yourself!"
            )

        tries = 0
        while True:
            msg = self._radio.receive()

            if msg is not None:
                msg_string = "".join([chr(b) for b in msg])
                self._log.debug(f"Message Received {msg_string}")

                time.sleep(0.1)
                tries += 1
                if tries > 5:
                    self._log.warning(
                        "We tried 5 times! And there was no response. Quitting."
                    )
                    break
                success = self._radio.send_with_ack(packet)
                self._log.debug("Success " + str(success))
                if success is True:
                    self._log.debug("Sending response")
                    response = self._radio.receive(keep_listening=True)
                    time.sleep(0.5)

                    if response is not None:
                        self._log.debug("Response Received", msg=response)
                        break
                    else:
                        self._log.debug(
                            "No response, trying again (" + str(tries) + ")"
                        )

    def handle_ping(self):
        response = self._radio.receive(keep_listening=True)

        if response is not None:
            self._log.debug("Ping Received", msg=response)

            self._radio.send("Ping Received!")
            self._log.debug("Echo Sent")
        else:
            self._log.debug("No Ping Received")

            self._radio.send("Nothing Received")
            self._log.debug("Echo Sent")

    def run(self):
        options = ["a", "b", "c"]

        print(
            """
        =======================================
        |                                     |
        |              WELCOME!               |
        |       Radio Test Version 1.0        |
        |                                     |
        =======================================
        |       Please Select Your Node       |
        | 'A': Device Under Test              |
        | 'B': Receiver                       |
        ================ OR ===================
        |      Act as a client                |
        | 'C': for an active satalite         |
        =======================================
        """
        )

        device_selection = input().lower()

        if device_selection not in options:
            self._log.warning(
                "Invalid Selection. Please refresh the device and try again."
            )

        print(
            """
        =======================================
        |                                     |
        |        Beginning Radio Test         |
        |       Radio Test Version 1.0        |
        |                                     |
        =======================================
        """
        )

        while True:
            if device_selection == "a":
                self.device_under_test()
            elif device_selection == "b":
                self.receiver()
            elif device_selection == "c":
                passcode = input("What's the passcode (in plain text): ")
                self.client(passcode)

            time.sleep(1)
