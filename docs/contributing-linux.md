# Contributing Guide for Linux

## Setup

To set up your development environment on Linux, follow these steps:

1. Update your package list and install the necessary packages:
    ```sh
    sudo apt update && sudo apt install make screen zip
    ```

You should now be able to run the `make` command in the root of the repo to get started.

### A note on `make install-flight-software`
`make install-flight-software` is a command that can be used to quickly install the code you're working on onto the board. On linux you can use the `findmnt` command to locate your board's mount point.
```sh
findmnt
...
├─/media/username/SOME-VALUE /dev/sdb1 vfat rw,nosuid,nodev,relatime 0 0
```

For example, if the board is mounted at `/media/username/SOME-VALUE` then your install command will look like:
```sh
make install-flight-software BOARD_MOUNT_POINT=/media/username/SOME-VALUE/
```

## Accessing the Serial Console
To see streaming logs and use the on-board repl you must access the Circuit Python serial console. Accessing the serial console starts with finding the tty port for the board. The easiest way to do that is by plugging in your board and running:
```sh
ls -lah /dev
```
Look for the file that was created around the same time that you plugged in the board. For Linux users the port typically looks like `/dev/ttyACM0`. You can then connect to the board using the `screen` command:
```sh
screen /dev/ttyACM0
```

For more information visit the [Circuit Python Serial Console documentation](https://learn.adafruit.com/welcome-to-circuitpython/advanced-serial-console-on-linux).
