"""This module provides a SD Card class to manipulate the sd card filesystem"""

from busio import SPI
from microcontroller import Pin

try:
    import sdcardio
    import storage
except ImportError:
    import mocks.circuitpython.sdcardio as sdcardio
    import mocks.circuitpython.storage as storage

from .hardware.exception import HardwareInitializationError


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
        except Exception as e:
            raise HardwareInitializationError("Failed to initialize SD Card") from e
