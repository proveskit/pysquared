# Contributing Guide for MacOS

## Setup

To get started with development on MacOS, follow these steps:

1. **Install Xcode Command Line Tools**: These tools are necessary for compiling and building software.
    ```sh
    xcode-select --install
    ```
1. **Install Homebrew**: Homebrew is a package manager for MacOS. Follow the instructions on [brew.sh](https://brew.sh/) to install it.
1. **Install Required Packages**: Open a terminal and run the following command to install required packages:
    ```sh
    brew install screen
    ```

You should now be able to run the `make` command in the root of the repo to get started.

### A note on `make install-flight-software`
`make install-flight-software` is a command that can be used to quickly install the code you're working on onto the board. On Mac, you can find the location of your mount by looking for a mount named `PYSQUARED` in your `/Volumes` directory
```sh
ls -lah /Volumes | grep PYSQUARED
...
drwx------@  1 nate  staff    16K Jan  9 08:09 PYSQUARED/
```

For example, if the board is mounted at `/Volumes/PYSQUARED/` then your install command will look like:
```sh
make install-flight-software BOARD_MOUNT_POINT=/Volumes/PYSQUARED/
```

## Accessing the Serial Console
To see streaming logs and use the on-board repl you must access the Circuit Python serial console. Accessing the serial console starts with finding the tty port for the board. The easiest way to do that is by plugging in your board and running:
```sh
ls -lah /dev
```
Look for the file that was created around the same time that you plugged in the board. For Mac users the port typically looks like `/dev/tty.usbmodem101`. You can then connect to the board using the `screen` command:
```sh
screen /dev/tty.usbmodem101
```

For more information visit the [Circuit Python Serial Console documentation](https://learn.adafruit.com/welcome-to-circuitpython/advanced-serial-console-on-mac-and-linux).
