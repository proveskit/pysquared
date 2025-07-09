# Getting Started with PySquared

## Introduction
PySquared is a flight software library designed for building and deploying satellite systems using CircuitPython. The library is hardware agnostic, meaning it can be used with various CircuitPython-compatible boards but is designed to run on [PROVES](https://docs.proveskit.space/en/latest/) hardware. Like the PROVES hardware, PySquared is an education first software project. We're here to help you learn to develop and launch satellites so be sure to ask questions!

This guide will help you set up your development environment and get you started with building a satellite using the PySquared Flight Software.

## CircuitPython
If this is your first time using CircuitPython, it is highly recommended that you check out Adafruit's [Welcome to CircuitPython](https://learn.adafruit.com/welcome-to-circuitpython/overview) to help you get started!

## Installing CircuitPython
// TODO(nateinaction): Make this more complete...
Once you have a CircuitPython-compatible board, you can start using PySquared. The first step is to install the latest CircuitPython firmware on your board. If you have a PROVES Kit, use [these instructions](https://docs.proveskit.space/en/latest/quick_start/proves_quick_start/#flashing-firmware) to install the firmware.

## Installing PySquared
Now that you have CircuitPython installed, you are ready to create your own repository to host your satellite's software. You can use one of the PySquared template repositories to get started quickly. Find your board version below, visit the repository, and click "Fork" to create your own copy of the repository.

| Board Version | Proves Repo                          |
|---------------|--------------------------------------|
| v4            | [proveskit/CircuitPython_RP2040_v4](https://github.com/proveskit/CircuitPython_RP2040_v4) |
| v5            | [proveskit/CircuitPython_RP2040_v5](https://github.com/proveskit/CircuitPython_RP2040_v5) |
| v5a           | [proveskit/CircuitPython_RP2350_v5a](https://github.com/proveskit/CircuitPython_RP2350_v5a) |
| v5b           | [proveskit/CircuitPython_RP2350_v5b](https://github.com/proveskit/CircuitPython_RP2350_v5b) |

### Cloning Your Repository

Then you can clone your repository to your local machine using the following command:

```sh
git clone https://github.com/your-username/your-repository.git
```

### Finding Your Board's Mount Point

Next, make sure your PROVES flight control board is plugged in and we'll find its mount point. The mount point is the location on your computer where the board's filesystem is accessible. This varies by operating system, so follow the guide for your OS below to find it.

??? note "Linux Guide"
    On linux you can use the `findmnt` command to locate your board's mount point.
    ```sh
    findmnt
    ...
    ├─/media/username/SOME-VALUE /dev/sdb1 vfat rw,nosuid,nodev,relatime 0 0
    ```

    In this example, the mount point is `/dev/sdb1`. Another common mount point for linux systems is `/media/username/<board_name>`.


??? note "MacOS Guide"
    On Mac, you can find the location of your mount by looking for a mount named `PYSQUARED` in your `/Volumes` directory
    ```sh
    ls -lah /Volumes | grep PYSQUARED
    ...
    drwx------@  1 nate  staff    16K Jan  9 08:09 PYSQUARED/
    ```

    In this example, the mount point is `/Volumes/PYSQUARED/`.

??? note "Windows Guide"
    In Git Bash your mount point will be the letter of the drive location in windows. For example, if the board is mounted at `D:\` then your drive location for commands in Git Bash will be `/d/`.

??? note "WSL Guide"
    First you must follow the guides to [connect][wsl-connect-usb] and [mount][wsl-mount-disk] your board in WSL.

    After following those guides, your mount point will probably be the letter of the drive location in Windows with `/mnt/` prepended. For example, if the board is mounted at `D:\` then your mount point in WSL will likely be `/mnt/d/`. If you are unsure, you can check the available mount points by running `ls /mnt/` in your terminal.

### Running the Install Command

With the repository cloned and your boards mount point in hand you can now install the flight software to the board. Navigate to the root of your board specific repository and run:

```sh
make install-flight-software BOARD_MOUNT_POINT=<path_to_your_board>
```
Replace `<path_to_your_board>` with the mount point discovered in the previous section.

## Accessing the Serial Console
To see streaming logs and use the on-board repl you must access the Circuit Python serial console.

??? note "Linux Guide"
    Accessing the serial console starts with finding the tty port for the board. The easiest way to do that is by plugging in your board and running:
    ```sh
    ls -lah /dev
    ```

    Look for the file that was created around the same time that you plugged in the board. For Linux users the port typically looks like `/dev/ttyACM0`. You can then connect to the board using the `screen` command:
    ```sh
    screen /dev/ttyACM0
    ```

    For more information visit the [Circuit Python Serial Console documentation](https://learn.adafruit.com/welcome-to-circuitpython/advanced-serial-console-on-linux).

??? note "MacOS Guide"
    Accessing the serial console starts with finding the tty port for the board. The easiest way to do that is by plugging in your board and running:
    ```sh
    ls -lah /dev
    ```

    Look for the file that was created around the same time that you plugged in the board. For Mac users the port typically looks like `/dev/tty.usbmodem101`. You can then connect to the board using the `screen` command:
    ```sh
    screen /dev/tty.usbmodem101
    ```

    For more information visit the [Circuit Python Serial Console documentation](https://learn.adafruit.com/welcome-to-circuitpython/advanced-serial-console-on-mac-and-linux).

??? note "Windows Guide"
    For information on how to access the serial console, visit the [Circuit Python Serial Console documentation](https://learn.adafruit.com/welcome-to-circuitpython/advanced-serial-console-on-windows).


!!! WARNING
    If all you see is a blank screen when you connect to the serial console, try pressing `CTRL+C` to see if you can get a prompt. If that doesn't work, try pressing `CTRL+D` to reset the board.

[wsl-connect-usb]: https://learn.microsoft.com/en-us/windows/wsl/connect-usb "How to Connect USB to WSL"
[wsl-mount-disk]: https://learn.microsoft.com/en-us/windows/wsl/wsl2-mount-disk "How to Mount a Disk to WSL"

## Congratulations!
You have successfully installed PySquared and have started a serial console session to view the output from your flight control board! Now you can start your journey of building and launching satellites using CircuitPython and PySquared.

## Next Steps
Now that you have your development environment set up, you can start [exploring the PySquared library](api.md) and building on the repo you cloned earlier in this guide.

// TODO(nateinaction): Finish this documentation
Here are some resources to help you get started:
- Setting up your code editor: [Code Editor Setup](code-editor-setup.md) // maybe use a dev container?
- PySquared API documentation: [PySquared API](api.md)
