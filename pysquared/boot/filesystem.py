"""File includes utilities for managing the filesystem during the boot process."""

import os
import time

try:
    import storage
except ImportError:
    import mocks.circuitpython.storage as storage


def mkdir(
    path: str,
    storage_action_delay: float = 0.02,
) -> None:
    """
    Create directories on internal storage during boot.

    In CircuitPython the internal storage is not writable by default. In order to mount
    any external storage (such as an SD Card) the drive must be remounted in read/write mode.
    This function handles the necessary steps to safely create a directory on the internal
    storage during boot.

    Args:
        mount_point: Path to mount point
        storage_action_delay: Delay after storage actions to ensure stability

    Usage:
        ```python
        from pysquared.boot.filesystem import mkdir
        mkdir("/sd")
        ```
    """
    try:
        storage.disable_usb_drive()
        time.sleep(seconds=storage_action_delay)
        print("Disabled USB drive")

        storage.remount("/", False)
        time.sleep(storage_action_delay)
        print("Remounted root filesystem")

        try:
            os.mkdir(path)
            print(f"Mount point {path} created.")
        except OSError:
            print(f"Mount point {path} already exists.")

    finally:
        storage.enable_usb_drive()
        time.sleep(storage_action_delay)
        print("Enabled USB drive")
