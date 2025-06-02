# Development Guide
Welcome to the development guide for our project! This guide will help you set up your development environment and get you started with contributing to the repository.

#### CircuitPython
If this is your first time using CircuitPython, it is highly recommended that you check out Adafruit's [Welcome to CircuitPython](https://learn.adafruit.com/welcome-to-circuitpython/overview) to help you get started!

## OS Specific Guides
We suggest you get started with the development guide for your operating system:

- [Windows](/docs/dev-guide-windows.md)
- [MacOS](/docs/dev-guide-macos.md)
- [Linux](/docs/dev-guide-linux.md)

Once you have your development environment set up, you should be able to run the following command to finish the setup:
```sh
make
```

## Manually testing code on a board
We are working on improving our automated testing but right now the best way to test your code is to run it on the board.

Your board must be connected to your computer, the correct board repository cloned, and you must have installed the latest CircuitPython Firmware.

Firmware can be installed by placing the board in Bootloader mode (by pressing both of the buttons simultaneously) and running the following command:
```sh
make install-firmware
```

In the board repository, you can run the following command to install code on the board:
```sh
make install BOARD_MOUNT_POINT=/PATH_TO_YOUR_BOARD
```

If you need to install a specific version of the `pysquared` library, you can do so by running:
```sh
PYSQUARED_VERSION=VERSION/BRANCH make install BOARD_MOUNT_POINT=/PATH_TO_YOUR_BOARD
```

There is more information in the OS specific guides on how to find your board's mount point.

To see the output of your code you can connect to the board using the serial console. You can find more information on how to do that in the OS specific guides.

### Notes on Serial Console
If all you see is a blank screen when you connect to the serial console, try pressing `CTRL+C` to see if you can get a prompt. If that doesn't work, try pressing `CTRL+D` to reset the board.

## Continuous Integration (CI)
This repo has a continuous integration system using Github Actions. Anytime you push code to the repo, it will run a series of tests. If you see a failure in the CI, you can click on the details to see what went wrong.

### Common Build Failures
Here are some common build failures you might see and how to fix them:

#### Lint Failure
Everytime you make a change in git, it's called a commit. We have a tool called a pre-commit hook that will run before you make each commit to ensure your code is safe and formatted correctly. If you experience a lint failure you can run the following to fix it for you or tell you what's wrong.
```sh
make fmt
```

#### Test Failure
To ensure our code works as we expect we use automated testing. If you're seeing a testing failure in your build, you can see what's wrong by running those tests yourself with:
```sh
make test
```
