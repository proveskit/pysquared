"""This module provides a SD Card class to manipulate the sd card filesystem"""

# import os

# try:
#     import mocks.circuitpython.sdcardio as sdcardio
#     import mocks.circuitpython.storage as storage
# except ImportError:
#     import sdcardio
#     import storage
# out loud
# I can create a mock for sdcardio so that it adhears to mainstream python blockdevice
# but typechecker will know that in at least one codepath the real sdcardio is not a block device.
# I can also create mocks for both sdcardio and storage using the circuitpython blockdevice protocol
# but I have the same issue that the typechecker will not know that in at least one codepath
# the real sdcardio is not a block device.
# Instead I need a method to tell the typechecker that we are not using mainstream python's
# blockdevice definition or sdcardio or storage
import sdcardio
import storage
from busio import SPI
from microcontroller import Pin

from .hardware.exception import HardwareInitializationError


# import sdcardio
class SDCardManager:
    """Class providing various functionalities related to USB and SD card operations."""

    """Initializing class, remounting storage, and initializing SD card"""

    def __init__(
        self,
        spi_bus: SPI,
        chip_select: Pin,
        baudrate: int = 400000,
        mount_path: str = "/sd",
    ) -> None:
        try:
            sd = sdcardio.SDCard(spi_bus, chip_select, baudrate)
            vfs = storage.VfsFat(sd)  # type: ignore # Issue: https://github.com/adafruit/Adafruit_CircuitPython_Typing/issues/51
            storage.mount(vfs, mount_path)
        except (OSError, ValueError) as e:
            raise HardwareInitializationError("Failed to initialize SD Card") from e
