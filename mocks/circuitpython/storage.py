"""Mock for the CircuitPython storage module.

This module provides a mock implementation of the CircuitPython storage module
for testing purposes. It allows for simulating the behavior of the storage
module without the need for actual hardware.
"""

from __future__ import annotations

from circuitpython_typing import BlockDevice


def mount(filesystem: VfsFat, mount_path: str, *, readonly: bool = False) -> None:
    """A mock function to mount the filesystem.

    Args:
        filesystem: The filesystem to mount.
        mount_path: Where to mount the filesystem.
        readonly: True when the filesystem should be readonly to CircuitPython.
    """
    pass


def disable_usb_drive() -> None:
    """A mock function to disable the USB drive."""
    pass


def enable_usb_drive() -> None:
    """A mock function to enable the USB drive."""
    pass


def remount(path: str, readonly: bool) -> None:
    """A mock function to remount the filesystem.

    Args:
        path: The path to remount.
        readonly: Whether to mount as read-only.
    """
    pass


class VfsFat:
    """A mock class representing a VfsFat filesystem."""

    def __init__(self, block_device: BlockDevice) -> None:
        """Initializes the mock VfsFat filesystem."""
        pass
