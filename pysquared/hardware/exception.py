class HardwareInitializationError(Exception):
    pass


class NotPowered(Exception):
    """Raised when a device is not powered and cannot perform operations."""

    pass
