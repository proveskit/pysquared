# Getting Started with PySquared

## Introduction
PySquared is a flight software library designed for building and deploying satellite systems using CircuitPython. The library is hardware agnostic, meaning it can be used with various CircuitPython-compatible boards but is designed to run on [PROVES](https://docs.proveskit.space/en/latest/) hardware. Like the PROVES hardware, PySquared is an education first software project. We're here to help you learn to develop and launch satellites so be sure to ask questions!

This guide will help you set up your development environment and get you started with building a satellite using the PySquared Flight Software.

## Setting Up Your Computer
Set up your development environment by following the instructions in your OS specific guide.

??? note "Linux Guide"

    Update your package list and install the necessary packages:
    ```sh
    sudo apt update && sudo apt install make screen zip
    ```

??? note "MacOS Guide"

    1. **Install Xcode Command Line Tools**: These tools are necessary for compiling and building software.
        ```sh
        xcode-select --install
        ```
    1. **Install Homebrew**: Homebrew is a package manager for MacOS. Follow the instructions on [brew.sh](https://brew.sh/) to install it.
    1. **Install Required Packages**: Open a terminal and run the following command to install required packages:
        ```sh
        brew install screen
        ```

??? note "Windows Guide"

    1. **Install Git**: Download and install Git from [git-scm.com](https://git-scm.com/downloads). Make sure to also install the Git Bash terminal during the setup process.
    1. **Install Putty**: Download and install Putty from [putty.org](https://putty.org/).
    1. **Install Chocolatey**: Chocolatey is a package manager for Windows. Follow the instructions on [chocolatey.org](https://chocolatey.org/install) to install it.
    1. **Install Required Packages**: Open a command prompt or Git Bash terminal and run the following command to install required packages:
        ```sh
        choco install make rsync zip
        ```

    Keep in mind that the rest of this guide expects that you are using Git Bash.

??? note "WSL Guide"
    Follow the steps in the Linux Guide

## Cloning Your Repository

Let's start by creating your own repository to host your satellite's software. You can use one of the PySquared template repositories to get started quickly. Find your board version below, visit the repository, and click "Fork" to create your own copy of the repository.

| Board Version | Proves Repo |
|---------------|-------------|
| v4            | [proveskit/CircuitPython_RP2040_v4](https://github.com/proveskit/CircuitPython_RP2040_v4) |
| v5            | [proveskit/CircuitPython_RP2040_v5](https://github.com/proveskit/CircuitPython_RP2040_v5) |
| v5a           | [proveskit/CircuitPython_RP2350_v5a](https://github.com/proveskit/CircuitPython_RP2350_v5a) |
| v5b           | [proveskit/CircuitPython_RP2350_v5b](https://github.com/proveskit/CircuitPython_RP2350_v5b) |

Then you can clone your repository to your local machine using the following command:

```sh
git clone https://github.com/your-username/your-repository.git
```

??? tip "Learn how to use the git command line"
    <iframe width="560" height="315" src="https://www.youtube-nocookie.com/embed/HVsySz-h9r4?si=FK8cPwJk1IJ_huGd" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

Next, <u>c</u>hange <u>d</u>irectory (`cd`) into the repo directory:

```sh
cd your-repository
```

You are now in your repo directory. This is where you'll write code that makes its way onto your satellite!

## Installing CircuitPython

??? note "CircuitPython May Already Be Installed"
    If you already have CircuitPython installed on your board, you can skip this section. You can check if CircuitPython is installed by plugging in your board and [trying to access the serial console](#accessing-the-serial-console).

Next, we need to install the latest CircuitPython firmware on your board. CircuitPython is a Python runtime for microcontrollers like the one on your board.

First you must find your board's TTY port. You can find the TTY port by plugging in your board and running the following command:

```sh
make list-tty
```

Example output:
```sh
TTY ports:
/dev/cu.usbmodem3101
```

In this example, the TTY port is `/dev/cu.usbmodem3101`. This is the port you will use to communicate with your board.

??? note "Seeing more than one TTY port?"
    If you see more than one TTY port listed, you may need to unplug your board and run the command again to see which one is created when you plug it in. The new port is likely the one you want.

Now you can install CircuitPython by running the following command:

```sh
make install-circuit-python BOARD_TTY_PORT=<tty_port>
```

## Installing PySquared

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
    On Mac, you can find the location of your mount by looking for a mount named `PYSQUARED`, `PROVESKIT` or `CIRCUITPYTHON` in your `/Volumes` directory
    ```sh
    ls -lah /Volumes
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

Remember the TTY port you found earlier? You will use that to connect to the board's serial console. The serial console allows you to interact with the board and see output from your code. If you don't remember the TTY port, you can run the `make list-tty` command again to find it.

??? note "Linux & MacOS Guide"
    You can then connect to the board using the `screen` command:
    ```sh
    screen /dev/cu.usbmodem3101
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
Now that you have your development environment set up, you can start [exploring the PySquared library](api.md) and building on the repo you forked and cloned earlier in this guide.

Here are some additional resources to help you get started:

<!-- - Want to test the radios? Check out the [Radio Testing Guide]() COMING SOON. -->
- Are you interested in contributing to PySquared? Check out our [Contributing Guide](contributing.md).
- Learn more about PROVES hardware with the [PROVES Kit documentation](https://docs.proveskit.space/en/latest/).
- Learn more about CircuitPython with the [Welcome to CircuitPython guide](https://learn.adafruit.com/welcome-to-circuitpython/overview).
