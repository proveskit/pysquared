# Contributing Guide for Windows
Welcome to the Windows Contributing Guide for our project! This guide will help you set up your development environment on a Windows machine and get you started with contributing to the repository.

Follow the instructions below for either a native Windows setup or using the Windows Subsystem for Linux (WSL).

## Native Windows Setup (Recommended)

To set up your development environment on Windows, follow these steps:

1. **Install Git**: Download and install Git from [git-scm.com](https://git-scm.com/downloads). Make sure to also install the Git Bash terminal during the setup process.
1. **Install Putty**: Download and install Putty from [putty.org](https://putty.org/).
1. **Install Chocolatey**: Chocolatey is a package manager for Windows. Follow the instructions on [chocolatey.org](https://chocolatey.org/install) to install it.
1. **Install Required Packages**: Open a command prompt or Git Bash terminal and run the following command to install required packages:
    ```sh
    choco install make rsync zip
    ```

Using the Git Bash terminal, you should now be able to run the `make` command in the root of the repo to get started.

### A note on `make install`

`make install` is a command that can be used to quickly install the code you're working on onto the board. In Git Bash your mount point will be the letter of the drive location in windows. For example, if the board is mounted at `D:\` then your install command will look like:
```sh
make install BOARD_MOUNT_POINT=/d/
```

## WSL Setup
Windows Subsystem for Linux (WSL) is a nice way to have a POSIX compatible workspace on your machine, the downside is a cumbersome USB [connecting][connect-usb] and [mounting][mount-disk] process that needs to be performed every time you reconnect the Satellite hardware to your computer.

1. Download Ubuntu for WSL:
    ```sh
    wsl --install
    ```
1. Run WSL:
    ```sh
    wsl
    ```
1. If you have Satellite hardware, [connect][connect-usb] and [mount][mount-disk] it in WSL.
1. Continue with our [Linux Development Guide](dev-guide-linux.md).

### A note on `make install`

`make install` is a command that can be used to quickly install the code you're working on onto the board. In WSL your mount point will be the letter of the drive location in windows. For example, if the board is mounted at `D:\` then you must first mount the disk in WSL:
```sh
mkdir /mnt/d
sudo mount -t drvfs D: /mnt/d
```

And your install command will look like:
```sh
make install BOARD_MOUNT_POINT=/mnt/d/
```

## Accessing the Serial Console
To see streaming logs and use the on-board repl you must access the Circuit Python serial console. For information on how to access the serial console, visit the [Circuit Python Serial Console documentation](https://learn.adafruit.com/welcome-to-circuitpython/advanced-serial-console-on-windows).

[connect-usb]: https://learn.microsoft.com/en-us/windows/wsl/connect-usb "How to Connect USB to WSL"
[mount-disk]: https://learn.microsoft.com/en-us/windows/wsl/wsl2-mount-disk "How to Mount a Disk to WSL"
