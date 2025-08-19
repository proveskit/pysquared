"""Module that provides function relevant on boot"""

import os
import time

import storage


def set_mount_points(
    mount_points=[
        "/sd",
    ],
    wait_time=0.02,
    max_attempt=5,
) -> None:
    """
    Mounts the specified mount points.

    Args:
        mount_points ([String]): List of mount points
        wait_time (float): Time to wait between mount attempts
        max_attempts (int): Amount of attempts before failure
    """
    mount_points = [
        "/sd",
    ]

    wait_time = 0.02

    storage.disable_usb_drive()
    print("Disabling USB drive")
    time.sleep(wait_time)

    storage.mount("/", False)
    print("Remounting root filesystem")
    time.sleep(wait_time)

    attempts = 0
    while attempts < max_attempt:
        attempts += 1
        try:
            for path in mount_points:
                try:
                    os.mkdir(path)
                    print(f"Mount point {path} created.")
                except OSError:
                    print(f"Mount point {path} already exists.")
        except Exception as e:
            print(f"Error creating mount point {path}: {e}")
            time.sleep(wait_time)
            continue

        break

    storage.enable_usb_drive()
    print("Enabling USB drive")
