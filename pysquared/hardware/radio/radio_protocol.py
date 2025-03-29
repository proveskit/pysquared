"""
This module defines a protocol for radio transceiver hardware.
This allows for flexibility in the design of the system,
enabling the use of different radio implementations without changing the code that uses them.

CircuitPython does not support Protocols directly, but this class can still be used to define an interface
for type checking and ensuring structural compatibility.

https://docs.python.org/3/library/typing.html#typing.Protocol
"""

# Type hinting only
try:
    from typing import Any

    from .modulation import RadioModulation
except ImportError:
    pass


class RadioProto:
    """Protocol defining the interface for a radio transceiver."""

    def send(self, data: Any) -> bool:
        """Send data over the radio.

        :param Any data: The data to send.
        :return: True if the send was successful (e.g., ACK received if applicable), False otherwise.
        :rtype: bool
        """
        ...

    def set_modulation(self, modulation: RadioModulation) -> None:
        """Request a change in the radio modulation mode.
        This change might take effect immediately or after a reset, depending on implementation.

        :param RadioModulation modulation: The desired modulation mode.
        """
        ...

    def get_modulation(self) -> RadioModulation:
        """Get the currently configured or active radio modulation mode.

        :return: The current modulation mode.
        :rtype: RadioModulation
        """
        ...

    def get_temperature(self) -> float:
        """Get the temperature reading from the radio sensor, if available.

        :return: The temperature in degrees Celsius.
        :rtype: float
        """
        ...
