"""This module provides a SD Card class to manipulate the sd card filesystem"""

# import os

import sdcardio
import storage

from .hardware.exception import HardwareInitializationError

try:
    from busio import SPI
    from microcontroller import Pin
except ImportError:
    pass


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
        self.mounted = False
        self.mount_path = mount_path

        try:
            sd = sdcardio.SDCard(spi_bus, chip_select, baudrate)
            vfs = storage.VfsFat(sd)
            storage.mount(vfs, self.mount_path)
            self.mounted = True
        except (OSError, ValueError) as e:
            raise HardwareInitializationError("Failed to initialize SD Card") from e
