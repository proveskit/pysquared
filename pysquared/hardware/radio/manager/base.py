"""This module provides a base class for radio managers.

This module defines the `BaseRadioManager` class, which serves as an abstract base
class for all radio managers in the system. It provides common functionality and
ensures that all radio managers adhere to a consistent interface.
"""

from ....config.radio import RadioConfig
from ....logger import Logger
from ....protos.radio import RadioProto
from ...exception import HardwareInitializationError
from ..modulation import FSK, LoRa, RadioModulation

# Type hinting only
try:
    from typing import Optional, Type
except ImportError:
    pass


class BaseRadioManager(RadioProto):
    """Base class for radio managers (CircuitPython compatible)."""

    def __init__(
        self,
        logger: Logger,
        radio_config: RadioConfig,
        **kwargs: object,
    ) -> None:
        """Initializes the base manager class.

        Args:
            logger: Logger instance for logging messages.
            radio_config: Radio configuration object.
            **kwargs: Hardware-specific arguments (e.g., spi, cs, rst).

        Raises:
            HardwareInitializationError: If the radio fails to initialize after retries.
        """
        self._log = logger
        self._radio_config = radio_config
        self._receive_timeout: int = 10  # Default receive timeout in seconds

        # Simply default to LoRa if "LoRa" or an invalid modulation is passed in
        initial_modulation = FSK if self._radio_config.modulation == "FSK" else LoRa

        self._log.debug(
            "Initializing radio",
            radio_type=self.__class__.__name__,
            modulation=initial_modulation.__name__,
        )

        try:
            self._initialize_radio(initial_modulation)
        except Exception as e:
            raise HardwareInitializationError(
                f"Failed to initialize radio with modulation {initial_modulation}"
            ) from e

    def send(self, data: bytes) -> bool:
        """Sends data over the radio.

        This method must be implemented by subclasses.

        Args:
            data: The data to send.

        Returns:
            True if the data was sent successfully, False otherwise.
        """
        try:
            if self._radio_config.license == "":
                self._log.warning("Radio send attempt failed: Not licensed.")
                return False

            sent = self._send_internal(data)

            if not sent:
                self._log.warning("Radio send failed")
                return False

            return True
        except Exception as e:
            self._log.error("Error sending radio message", e)
            return False

    def receive(self, timeout: Optional[int] = None) -> bytes | None:
        """Receives data from the radio.

        This method must be implemented by subclasses.

        Args:
            timeout: Optional receive timeout in seconds. If None, use the default timeout.

        Returns:
            The received data as bytes, or None if no data was received.

        Raises:
            NotImplementedError: If not implemented by subclass.
            Exception: If receiving fails unexpectedly.
        """
        raise NotImplementedError

    def get_modulation(self) -> Type[RadioModulation]:
        """Gets the modulation mode from the initialized radio hardware.

        Returns:
            The current modulation mode of the hardware.

        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError

    def modify_config(self, key: str, value) -> None:
        """Modifies a specific radio configuration parameter.

        This method must be implemented by subclasses.

        Args:
            key: The configuration parameter key to modify.
            value: The new value to set for the parameter.

        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError

    def _initialize_radio(self, modulation: Type[RadioModulation]) -> None:
        """Initializes the specific radio hardware.

        This method must be implemented by subclasses.

        Args:
            modulation: The modulation mode to initialize with.

        Raises:
            NotImplementedError: If not implemented by subclass.
            Exception: If initialization fails.
        """
        raise NotImplementedError

    def _send_internal(self, data: bytes) -> bool:
        """Sends data using the specific radio hardware's method.

        This method must be implemented by subclasses.

        Args:
            data: The data to send.

        Returns:
            True if sending was successful, False otherwise.

        Raises:
            NotImplementedError: If not implemented by subclass.
            Exception: If sending fails unexpectedly.
        """
        raise NotImplementedError

    def get_rssi(self) -> int:
        """Gets the RSSI of the last received packet.

        Returns:
            The RSSI of the last received packet.

        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError

    def get_max_packet_size(self) -> int:
        """Gets the maximum packet size supported by the radio.

        Returns:
            The maximum packet size in bytes.
        """
        return 128  # Placeholder value, should be overridden by subclasses
