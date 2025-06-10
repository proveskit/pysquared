from ....config.radio import RadioConfig
from ....logger import Logger
from ....protos.radio import RadioProto
from ...decorators import with_retries
from ...exception import HardwareInitializationError
from ..modulation import FSK, LoRa, RadioModulation

# Type hinting only
try:
    from typing import Optional, Type
except ImportError:
    pass


class BaseRadioManager(RadioProto):
    """Base class for radio managers (CircuitPython compatible)."""

    @with_retries(max_attempts=3, initial_delay=1)
    def __init__(
        self,
        logger: Logger,
        radio_config: RadioConfig,
        **kwargs: object,
    ) -> None:
        """Initialize the base manager class.

        :param Logger logger: Logger instance for logging messages.
        :param RadioConfig radio_config: Radio configuration object.
        :param Flag use_fsk: Flag to determine whether to use FSK or LoRa mode.
        :param Any kwargs: Hardware-specific arguments (e.g., spi, cs, rst).

        :raises HardwareInitializationError: If the radio fails to initialize after retries.
        """
        self._log = logger
        self._radio_config = radio_config
        self._receive_timeout: int = 10  # Default receive timeout in seconds

        # Simply default to LoRa if "LoRa" or an invalid modulation is passed in
        initial_modulation = FSK if self._radio_config.modulation == "FSK" else LoRa

        self._log.debug(
            "Initializing radio",
            radio_type=self.__class__.__name__,
            modulation=initial_modulation,
        )

        try:
            self._initialize_radio(initial_modulation)
        except Exception as e:
            raise HardwareInitializationError(
                f"Failed to initialize radio with modulation {initial_modulation}"
            ) from e

    def send(self, data: object) -> bool:
        """Send data over the radio."""
        try:
            if self._radio_config.license == "":
                self._log.warning("Radio send attempt failed: Not licensed.")
                return False

            # Convert data to bytes if it's not already
            if isinstance(data, str):
                payload = bytes(data, "UTF-8")
            elif isinstance(data, bytes):
                payload = data
            else:
                # Attempt to convert other types, log warning if ambiguous
                self._log.warning(
                    f"Attempting to send non-bytes/str data type: {type(data)}"
                )
                payload = bytes(str(data), "UTF-8")

            license_bytes = bytes(self._radio_config.license, "UTF-8")
            payload = b" ".join([license_bytes, payload, license_bytes])

            sent = self._send_internal(payload)

            if not sent:
                self._log.warning("Radio send failed")
                return False

            self._log.info("Radio message sent")
            return True
        except Exception as e:
            self._log.error("Error sending radio message", e)
            return False

    def receive(self, timeout: Optional[int] = None) -> bytes | None:
        """Receive data from the radio.

        Must be implemented by subclasses.

        :param int | None timeout: Optional receive timeout in seconds.If None, use the default timeout.
        :return: The received data as bytes, or None if no data was received.

        :raises NotImplementedError: If not implemented by subclass.
        :raises Exception: If receiving fails unexpectedly.
        """
        raise NotImplementedError

    def get_modulation(self) -> Type[RadioModulation]:
        """Get the modulation mode from the initialized radio hardware.

        :return: The current modulation mode of the hardware.

        :raises NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError

    def modify_config(self, key: str, value) -> None:
        """Modify a specific radio configuration parameter.

        Must be implemented by subclasses.

        :param str key: The configuration parameter key to modify.
        :param value: The new value to set for the parameter.
        :raises NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError

    # Methods to be overridden by subclasses
    def _initialize_radio(self, modulation: Type[RadioModulation]) -> None:
        """Initialize the specific radio hardware.

        Must be implemented by subclasses.

        :param RadioModulation modulation: The modulation mode to initialize with.
        :param Any kwargs: Hardware-specific arguments passed from __init__.
        :return: The initialized radio hardware object.
        :raises NotImplementedError: If not implemented by subclass.
        :raises Exception: If initialization fails.
        """
        raise NotImplementedError

    def _send_internal(self, payload: bytes) -> bool:
        """Send data using the specific radio hardware's method.

        Must be implemented by subclasses.

        :param bytes payload: The data to send.
        :return: True if sending was successful, False otherwise.
        :raises NotImplementedError: If not implemented by subclass.
        :raises Exception: If sending fails unexpectedly.
        """
        raise NotImplementedError

    def get_rssi(self) -> float:
        """Get the RSSI of the last received packet.

        :return: The RSSI of the last received packet.
        :raises NotImplementedError: If not implemented by subclass.
        :raises Exception: If querying the hardware fails.
        """
        raise NotImplementedError
