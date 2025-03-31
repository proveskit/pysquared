from ....config.radio import RadioConfig
from ....logger import Logger
from ....nvm.flag import Flag
from ....protos.radio import RadioProto
from ...decorators import with_retries
from ...exception import HardwareInitializationError
from ..modulation import RadioModulation

# Type hinting only
try:
    from typing import Any
except ImportError:
    pass


class BaseRadioManager(RadioProto):
    """Base class for radio managers (CircuitPython compatible)."""

    @with_retries(max_attempts=3, initial_delay=1)
    def __init__(
        self,
        logger: Logger,
        radio_config: RadioConfig,
        use_fsk: Flag,
        **kwargs: Any,
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
        self._use_fsk = use_fsk
        self._radio: Any | None = None  # Placeholder for the specific radio instance

        initial_modulation = self.get_modulation()
        self._log.debug(
            "Initializing radio",
            radio_type=self.__class__.__name__,
            modulation=initial_modulation,
        )

        try:
            self._radio = self._initialize_radio(initial_modulation, **kwargs)
        except Exception as e:
            raise HardwareInitializationError(
                f"Failed to initialize radio with modulation {initial_modulation}"
            ) from e

    def send(self, data: Any) -> bool:
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

            sent = self._send_internal(payload)
            self._log.info(
                "Radio message sent",
                success=bool(sent),
                len=len(payload),
            )
            return bool(sent)
        except Exception as e:
            self._log.error("Error sending radio message", e)
            return False

    def set_modulation(self, req_modulation: RadioModulation) -> None:
        """Request a change in the radio modulation mode (takes effect on next init)."""
        current_modulation = self.get_modulation()
        if current_modulation != req_modulation:
            self._use_fsk.toggle(req_modulation == RadioModulation.FSK)
            self._log.info(
                "Radio modulation change requested for next init",
                requested=req_modulation,
                current=current_modulation,
            )

    def get_modulation(self) -> RadioModulation:
        """Get the currently configured radio modulation mode."""
        if self._radio is None:
            # If radio not initialized yet, rely on the flag
            return RadioModulation.FSK if self._use_fsk.get() else RadioModulation.LORA
        else:
            # Ask the initialized radio instance
            return self._get_current_modulation()

    # Methods to be overridden by subclasses
    def _initialize_radio(self, modulation: RadioModulation, **kwargs: Any) -> Any:
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

    def _get_current_modulation(self) -> RadioModulation:
        """Get the modulation mode from the initialized radio hardware.

        Must be implemented by subclasses.

        :return: The current modulation mode of the hardware.
        :raises NotImplementedError: If not implemented by subclass.
        :raises Exception: If querying the hardware fails.
        """
        raise NotImplementedError
