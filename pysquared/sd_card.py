"""This module provides a SD Card class to manipulate the sd card filesystem"""

import os

import sdcardio
import storage

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
        mounted: bool = False,
        log_size: int = 50000,  # 50 kb
        log_rotate: int = 10,
    ) -> None:
        self.mounted = mounted
        self.log_size = log_size
        self.log_rotate = log_rotate

        try:
            sd = sdcardio.SDCard(spi_bus, chip_select, baudrate)
            vfs = storage.VfsFat(sd)
            storage.mount(vfs, mount_path)
        except (OSError, ValueError) as e:
            print("error mounting sd card", e)
        else:
            self.mounted = True

        if "logs" not in os.listdir("/sd"):
            print("/sd/logs does not exist, creating...")
            os.mkdir("/sd/logs")
