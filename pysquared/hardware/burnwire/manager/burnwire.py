import time

from digitalio import DigitalInOut

from ....logger import Logger
from ....protos.burnwire import BurnwireProto

"""
Usage Example:

from lib.pysquared.hardware.burnwire.manager.burnwire import BurnwireManager
...

antenna_deployment = BurnwireManger(logger, board.FIRE_DEPLOY1A, board.FIRE_DEPLOY1B, enable_logic = False)

antenna_deployment.burn()
"""


class BurnwireManager(BurnwireProto):
    """Class for managing burnwire ports."""

    def __init__(
        self,
        logger: Logger,
        enable_burn: DigitalInOut,
        fire_burn: DigitalInOut,
        enable_logic: bool = True,
        deployment_sensor=None,
    ) -> None:
        """
        Initializes the burnwire manager class.

        :param Logger logger: Logger instance for logging messages.
        :param Digitalio enable_burn: A pin used for enabling the initial stage of a burnwire circuit.
        :param Digitalio fire_burn: A pin used for enabling a specific burnwire port.
        :param bool enable_logic: Boolean defining whether the burnwire load switches are enabled when True or False. Defaults to `True`.
        :param deployment_sensor: Generic input for a sensor object that will act as the deployment sensor for smart_burn(). Defaults to 'False'.
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

    def burn(self, timeout_duration: float = 5.0, max_retries: int = 1):
        """Fires the burnwire for a specified ammount of time

        :param float timeout_duration: The max ammount of time to keep the burnwire on for.
        :param int max_retries: The maximum number of times the burnwire is allowed to retry before exitng.

        :return: A Boolean indicating whether the burn occured sucessfully
        :rtype: bool

        :raises Exception: If there is an error toggling the burnwire pins.
        """
        self._log.info(
            f"BURN Attempt {self.number_of_attempts} Started with Duration {timeout_duration}s"
        )
        try:
            if max_retries > 1:
                self._log.warning(
                    "Multiple Retries with base burnwire not recommended! Consider using smart_burnwire..."
                )

            elif max_retries < 1:
                self._log.warning("burnwire max_retries cannot be 0 or negative!")
                raise ValueError

            for _ in range(max_retries):
                self._attempt_burn(timeout_duration)

        except RuntimeError as e:
            self._log.critical(
                f"BURN Attempt {self.number_of_attempts} Failed! Not Retrying", e
            )
            return False

        except ValueError as e:
            self._log.critical("Burnwire configuration incorrect!", e)
            return False

        self._log.info(f"BURN Attempt {self.number_of_attempts} Completed")
        return True

    def _attempt_burn(self, duration: float = 5.0) -> None:
        """Private function for actuating the burnwire ports for a set period of time.

        :param float duration: Defines how long the burnwire will remain on for. Defaults to 5s.

        :return: None
        :rtype: None
        """
        try:
            self.number_of_attempts += 1
            self._enable_burn.value = self._enable
            time.sleep(0.1)  # Short pause to stabilize load switches

            # Burnwire becomes active
            self._fire_burn.value = self._enable
            time.sleep(duration)

        except Exception as e:
            raise RuntimeError from e

        finally:
            # Burnwire cleanup in the finally block to ensure it always happens
            self._fire_burn.value = self._disable
            self._enable_burn.value = self._disable
            self._log.info("Burnwire Safed")

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
