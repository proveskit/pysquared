import time

from ..config.radio import RadioConfig
from ..logger import Logger
from ..protos.radio import RadioProto


class RadioTest:
    test_message = "Hello There!"

    def __init__(
        self,
        logger: Logger,
        radio: RadioProto,
        radio_config: RadioConfig,
    ):
        self._log = logger
        self._log.colorized = True
        self._radio = radio
        self._radio_config = radio_config

    def device_under_test(self):
        try:
            self._log.debug("Device Under Test Selected")

            results = {}

            for i in range(5):
                i += 1
                self._radio.send(f"|PING: {i} {self.test_message}|")
                self._log.debug("Sending Ping...")

                response = self._radio.receive(timeout=5)
                if response:
                    response = response.decode("utf-8")
                    self._log.debug(response)

                    header = response.split(" ", 1)[0]

                    if response == f"{header} PONG: {i} {self.test_message} {header}":
                        rssi = self._radio.get_rssi()
                        self._log.debug("Received pong.", attempts=i, rssi=rssi)
                        results[str(i)] = {
                            "received": True,
                            "rssi": rssi,
                        }
                else:
                    self._log.debug("Didn't receive pong.", attempts=i, rssi=None)
                    results[str(i)] = {
                        "received": False,
                        "rssi": None,
                    }

                time.sleep(1)

            self._log.debug("Radio test results: ", results=results)
        except KeyboardInterrupt:
            self._log.debug("Keyboard interrupt received, exiting device test.")

    def receiver(self):
        # Run receiver test forever to make it easier to test other boards.
        try:
            # Swap sender and receiver IDs to test receiver functionality
            self._radio.modify_config("receiver_id", self._radio_config.sender_id)
            self._radio.modify_config("sender_id", self._radio_config.receiver_id)

            while True:
                self._log.debug("Receiver Selected")
                self._log.debug("Awaiting Ping...")

                heard_something = self._radio.receive(timeout=10)

                if heard_something:
                    heard_something = heard_something.decode("utf-8")
                    self._log.debug(heard_something)

                    split_message = heard_something.split("|")

                    if split_message[1][0:4] == "PING":
                        self._log.info("Received Ping!", ping=heard_something)
                        self._radio.send(f"PONG{split_message[1][4:]}")
                    else:
                        self._log.info(
                            "Received unknown message, discarding", ping=heard_something
                        )

                else:
                    self._log.debug("No Response Received")
        except KeyboardInterrupt:
            self._log.debug("Keyboard interrupt received, exiting receiver test.")
        finally:
            self._radio.modify_config("receiver_id", self._radio_config.receiver_id)
            self._radio.modify_config("sender_id", self._radio_config.sender_id)

    # This mode is for interacting with an active board to send packets to cdh.py
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
                success = self._radio.send(packet)
                self._log.debug("Success " + str(success))
                if success is True:
                    self._log.debug("Sending response")
                    response = self._radio.receive()
                    time.sleep(0.5)

                    if response is not None:
                        self._log.debug("Response Received", msg=response)
                        break
                    else:
                        self._log.debug(
                            "No response, trying again (" + str(tries) + ")"
                        )

    def handle_ping(self):
        response = self._radio.receive()

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

        while True:
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
                self._log.warning("Invalid Selection. Please try again.")
                continue

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

            if device_selection == "a":
                self.device_under_test()
            elif device_selection == "b":
                self.receiver()
            elif device_selection == "c":
                passcode = input("What's the passcode (in plain text): ")
                self.client(passcode)

            time.sleep(1)
