# PySquared

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![CI](https://github.com/proveskit/pysquared/actions/workflows/ci.yaml/badge.svg)

CircuitPython based Flight Software for the PROVES Kit.

If this is your first time using CircuitPython, it is highly recommended that you check out Adafruit's [Welcome to CircuitPython](https://learn.adafruit.com/welcome-to-circuitpython/overview?gad_source=1&gbraid=0AAAAADx9JvTRorSR2psQubn32WqebKusM&gclid=CjwKCAiA-Oi7BhA1EiwA2rIu28YArt-jNTE3W3uwE055Tp7hyH9c9pE_NsqIOOh1aopnW00qXGBedRoChysQAvD_BwE) to help you get started!

# Usage
If you have just received a clean PROVES Board, ensure you have loaded the latest firmware from that board's GitHub Repo. Currently the [latest FC Board firmware](https://github.com/proveskit/flight_controller_board/tree/main/Firmware) is `FC_FIRM_V2.uf2`.

# Development Getting Started
We welcome contributions, so please feel free to join us. If you have any questions about contributing please open an issue or a discussion.

You can find our Getting Started Guide [here](docs/dev-guide.md).

## Manually Updating CircuitPython Code on a PROVES Board
You can cleanly load new software by doing the following:
1. Clone the branch you wish to put on your board to your local machine.
2. Connect to the target board so it mounts as an external drive.
3. If many files have changed, connect to the target board using a serial terminal and run the following code in the REPL to erase all of the existing code:
  ```py
  import storage
  storage.erase_filesystem()
  ```
  > NOTE: If you have only changed one or two files, it is fine to just drag and drop them onto the external drive to overwrite the existing files.
4. The target board will now disappear and remount. Once remounted copy and paste the contents of the flight software folder for the target board from your GitHub repo.
5. When the new files are onboard you can verify that all the hardware on the board is working properly by opening a serial connection and entering the REPL after using `ctrl+c` to interupt the code that is currently running.

## General Structure:
- **boot.py** This is the code that runs on boot and initializes the stack limit
- **main.py** This code tasks all the functions the satellite should do in a semi-asynchronous manner utilizing the asyncio library
- **safemode.py** This code is unimplemented pending new firmware releases that allow the microconrtoller to perform a routine when in safemode
### pysquared lib
This software library contains all of the libraries required to operate the sensors, PySquared board, and radio module.
- **Big_Data.py** This is a class developed to obtain data from the sensors on the 5 solar faces. Since all the faces maintain the same sensors, this class handles the individual face sensors and returns them all to the main code.
- **flag.py** This is code that allows for some registers within the microcontroller to be written to and saved through power cycles
- **Field.py** This is code that implements the radio module for sending and listening
- **functions.py** This is a library of functions utilized by the satellite to obtain data, detumble, run the battery heater
- **pysquared.py** This is a library that initializes and maintains all the main functions for the pysquared architecture
- **adafruit_rfm.py** This is a library that implements all the radio hardware. This code is a modified version of the pycubed_rfm9x which is a modified version of the adafruit_rfm9x file.
- **cdh.py** This is the code that handles all the commands. A majority of this code is pulled from the cdh file developed by Max Holliday at Stanford.
- **detumble.py** This code implements the B-dot algorithm and returns outputs that allow the system to do a controlled detumble with the satellite's embedded magnetourquer coils
- **payload.py** This code implements any desired payload. On the Pleiades missions, the payload has been the BNO055 IMU. Since the use of a stemmaQT connector allows multiple devices on the same bus, a BNO IMU could be used in conjunction with several other sensors if desired.
- **logger.py** This class emulates the logging abilities of mainline Python and creates .json format logs for all of the satellite activities.
- **config.json** This file is used to configure the system variables for the satellite software.
## Adafruit Libraires
These are open source software libraries that are pull from Adafruit. They don't ship by default anymore in our repo, instead they are installed by our package manager when you run the `make` toolchain.
- **asyncio** This is the library responsible for scheduling tasks in the main code
- **adafruit_bno055.py** This is the library that is responsible for obtaining data from the BNO055 IMU
- **adafruit_drv2605.mpy** This is the pre-compiled library that is responsible for driving the magnetorquer coils using the drv2605 motor driver
- **adafruit_ina219.py** This is the library that is responsible for obtaining data from the INA219 Power Monitor
- **adafruit_mcp9808.mpy** This is the pre-compiled library that is responsible for obtaining data from the MCP9808 Temperature Sensor
- **adafruit_pca9685.py** This is the library that is responsible or driving the power to the satellite faces using the pca9685 LED driver
- **adafruit_tca9548a.mpy** This is the pre-compiled library that multiplexes the I2C line to each satellite face using the tca9548a I2C Multiplexer
- **adafruit_veml7700.py** This is the library that is responsible for obtaining data from the veml7700 Light Sensor
- **adafruit_vl6180.py** This is the library that is responsible for obtaining data from the vl6180 LiDAR sensor
## tests
This software is used for performing tests on the satellite. Currently this is seperated into `repl` (tests that are meant to be run from the REPL enviroment on the board) and `unit` (tests that can be run independently of the hardware).
- **radio_test.py** This is an omnibus radio testing script that will allow you to send, receive, and command boards running the PySquared library.

## Testing setup

1. Follow the steps to set up your venv and install packages in the linting setup
2. Run tests with `make test`
