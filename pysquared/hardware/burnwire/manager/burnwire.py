import time

from digitalio import DigitalInOut

from ....logger import Logger
from ....protos.burnwire import BurnwireProto


class BurnwireManager(BurnwireProto):
    """Class for managing burnwire ports."""

    def __init__(
        self,
        logger: Logger,
        enable_burn: DigitalInOut,
        fire_burn: DigitalInOut,
        enable_logic: bool = True,
    ) -> None:
        """
        Initializes the burnwire manager class.

        :param Logger logger: Logger instance for logging messages.
        :param Digitalio enable_burn: A pin used for enabling the initial stage of a burnwire circuit.
        :param Digitalio fire_burn: A pin used for enabling a specific burnwire port.
        :param bool enable_logic: Boolean defining whether the burnwire load switches are enabled when True or False. Defaults to `True`.
        """
        self._log: Logger = logger
        self._enable: bool = enable_logic

        if enable_logic:
            self._disable: bool = False
        else:
            self._disable: bool = True

        self._enable_burn: DigitalInOut = enable_burn
        self._fire_burn: DigitalInOut = fire_burn

        self.number_of_attempts: int = 0

    def burn(self, duration: float = 5.0):
        """
        Fires the burnwire for a specified ammount of time

        :param float duration: The ammount of time to keep the burnwire on for. Defaults to 5s.

        :return: A Boolean indicating whether the burn occured sucessfully
        :rtype: bool

        :raises Exception: If there is an error toggling the burnwire pins.
        """
        self._log.info(
            f"BURN Attempt {self.number_of_attempts} Started with Duration {duration}s"
        )
        try:
            self._enable_burn.value = self._enable
            time.sleep(0.1)  # Short pause to stabilize load switches

            # Burnwire becomes active
            self._fire_burn.value = self._enable
            time.sleep(duration)

        except Exception as e:
            self._log.critical(f"BURN Attempt {self.number_of_attempts} Failed!", e)
            return False

        finally:
            # Burnwire cleanup in the finally block to ensure it always happens
            self._fire_burn.value = self._disable
            self._enable_burn.value = self._disable

        self._log.info(f"BURN Attempt {self.number_of_attempts} Completed")
        return True

    def smart_burn(self, max_retries: int = 3, timeout_duration: float = 5.0):
        """Fires the burnwire and uses a deployment sensor

        :param int max_retries: The maximum number of times the burnwire is allowed to retry before exitng.
        :param float timeout_duration: The max time to keep the burnwire on for if the deployment sensor doesn't detect deployment.

        :return: A Boolean indicating whether the burn occured sucessfully
        :rtype: bool

        :raises Exception: If there is an error toggling the burnwire pins.
        """

        self._log.debug(
            "smart_burn() has not been implemented yet. Use burn() for now..."
        )
        raise NotImplementedError
