"""This module defines the available radio modulation types.

This module provides a set of classes that represent the different radio
modulation types that can be used by the radio hardware. These classes are used to
configure the radio and to identify the current modulation type.
"""


class RadioModulation:
    """Base class for radio modulation modes."""

    pass


class FSK(RadioModulation):
    """Represents the FSK modulation mode."""

    pass


class LoRa(RadioModulation):
    """Represents the LoRa modulation mode."""

    pass
