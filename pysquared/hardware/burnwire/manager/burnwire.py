import time

from digitalio import DigitalInOut

from ....logger import Logger
from ....protos.burnwire import BurnwireProto


class BurnwireManager(BurnwireProto):
    """Class for managing burnwire ports."""

    def __init__(
        self,
        logger: Logger,
        enable_logic: bool,
        enable_burn: DigitalInOut,
        fire_burn: DigitalInOut,
    ) -> None:
        """
        Initializes the burnwire manager class.

        :param Logger logger: Logger instance for logging messages.
        :param bool enable_logic: Boolean defining whether the burnwire load switches are enabled when True or False
        :param Digitalio enable_burn: A pin used for enabling the initial stage of a burnwire circuit.
        :param Digitalio fire_burn: A pin used for enabling a specific burnwire port.
        """
        self._log = logger
        self._enable = enable_logic
        self._enable_burn = enable_burn
        self._fire_burn = fire_burn

    def burn(self, duration=5.0):
        """ """

        self._enable_burn.value = self._enable
        time.sleep(duration)

        return True

    def smart_burn(self, max_retries, timeout_duration):
        return True
