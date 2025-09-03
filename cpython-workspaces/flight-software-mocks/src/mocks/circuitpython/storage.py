"""Mock for the CircuitPython storage module.

This module provides a mock implementation of the CircuitPython storage module
for testing purposes. It allows for simulating the behavior of the storage
module without the need for actual hardware.
"""


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
