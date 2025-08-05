"""This module provides a SD Card class to manipulate the sd card filesystem

PLACEHOLDER

**Usage:**
```python
PLACEHOLDER
```
"""

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

        if "sd" not in os.listdir("/"):
            print("/sd directory does not exist, creating...")
            os.mkdir("/sd/logs")

        try:
            sd = sdcardio.SDCard(spi_bus, chip_select, baudrate)
            vfs = storage.VfsFat(sd)
            storage.mount(vfs, mount_path)
        except (OSError, ValueError) as e:
            print("error mounting sd card", e)
        else:
            self.mounted = True

    # def sd_log(self, json_output):
    #     """
    #     Outputs log to sd card at /sd/logs/log while handling log
    #     rotation based off of file size and log rotate

    #     Args:
    #         json_output (str): The log output.
    #     """
    #     if "logs" not in os.listdir("/sd"):
    #         current_dir = os.getcwd()
    #         os.chdir("/sd")
    #         os.mkdir("logs")
    #         os.chdir(current_dir)

    #     full_path = "/sd/logs/log"
    #     next_log = str(len(os.listdir("/sd/logs")) + 1)

    #     try:
    #         with open(full_path, "r"):
    #             pass
    #     except OSError:
    #         with open(full_path, "w"):
    #             pass

    #     stats = os.stat(full_path)
    #     filesize = stats[6]
    #     output_size = len(json_output.encode())

    #     if filesize + output_size > self.log_size:
    #         rotated_str = "/sd/logs/log." + next_log
    #         os.rename(full_path, rotated_str)

    #     with open(full_path, "a") as f:
    #         f.write(json_output + "\n")

    #     print(f"Log saved to {full_path}")

    # def print_directory(self, path, tabs=0):
    #     """
    #     Prints directories of /sd and children with relevant metedata

    #     Args:
    #         path (str): Path to sd directory.
    #         tabs: amount of tabs to print the the directories in (i think)
    #     """

    #     for file in os.listdir(path):
    #         if file == "?":
    #             continue  # Issue noted in Learn
    #         stats = os.stat(path + "/" + file)
    #         filesize = stats[6]
    #         isdir = stats[0] & 0x4000

    #         if filesize < 1000:
    #             sizestr = str(filesize) + " by"
    #         elif filesize < 1000000:
    #             sizestr = "%0.1f KB" % (filesize / 1000)
    #         else:
    #             sizestr = "%0.1f MB" % (filesize / 1000000)

    #         prettyprintname = ""
    #         for _ in range(tabs):
    #             prettyprintname += "   "
    #         prettyprintname += file
    #         if isdir:
    #             prettyprintname += "/"
    #         print("{0:<40} Size: {1:>10}".format(prettyprintname, sizestr))

    #         # recursively print directory contents
    #         if isdir:
    #             self.print_directory(path + "/" + file, tabs + 1)
