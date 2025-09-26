# PySquared Radio Test Documentation

When receiving a PROVES device, most teams want to set up a radio test to ensure that the radio is functioning correctly. This document provides a guide on how to set up and run a radio test using the PySquared framework. You will need two boards for this test: one to send data and one to receive data.

!!! warning "Radio License Required"
    Before running the radio test, ensure that you have the appropriate license to operate the radio frequencies used by the PROVES Kit. Failure to comply with local regulations may result in interference with other devices or legal issues.

## Setting Up the Radio Test

Just like in the [Getting Started Guide](getting-started.md), you will need to clone your board specific repository and make sure that [CircuitPython is installed](getting-started.md#installing-circuitpython) on both boards.

### Setting Up the Configuration

In the root of your board specific repository, you will find a `config.json`. Change the `radio.license` to your callsign or the callsign of the licensed individual you are operating under. This is important for compliance with radio regulations.

```json
{
  "radio": {
    "license": "YOUR_CALLSIGN"
  }
}
```

Next, you will need to install the flight control software on one board and the ground station software on the other. To do this, you'll need to [know your board's mount point](getting-started.md#finding-your-boards-mount-point).

### Flight Control Software Installation

On the first board, install the flight control software by running the following command:

```sh
make install-flight-software BOARD_MOUNT_POINT=<path_to_your_board>
```

### Ground Station Software Installation

On the second board, install the ground station software by running the following command:

```sh
make install-ground-station BOARD_MOUNT_POINT=<path_to_your_board>
```

### Running the Radio Test

Now, [open the serial console](getting-started.md#accessing-the-serial-console) for both boards. On the ground station board, use the console to send or receive messages to verify communication with the flight control board.
