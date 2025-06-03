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

    def burn(self, timeout_duration: float = 5.0, max_retries: int = 1) -> bool:
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
            if max_retries == 1:
                try:
                    self._attempt_burn(timeout_duration)
                    return True
                except RuntimeError as e:
                    self._log.critical(
                        f"BURN Attempt {self.number_of_attempts} Failed! Not Retrying",
                        e,
                    )
                    return False

            elif max_retries < 1:
                self._log.warning("burnwire max_retries cannot be 0 or negative!")
                raise ValueError

            else:
                self._log.warning(
                    "Multiple Retries with base burnwire not recommended! Consider using smart_burnwire..."
                )

                for _ in range(max_retries):
                    try:
                        self._attempt_burn(timeout_duration)
                        self._log.info(
                            f"BURN Attempt {self.number_of_attempts} Completed"
                        )
                        time.sleep(1)
                    except RuntimeError:
                        return False

                return True

        except ValueError as e:
            self._log.critical("Burnwire configuration incorrect!", e)
            return False

    def _attempt_burn(self, duration: float = 5.0) -> None:
        """Private function for actuating the burnwire ports for a set period of time.

        :param float duration: Defines how long the burnwire will remain on for. Defaults to 5s.

        :return: None
        :rtype: None

        :raises RuntimeError: If there is an error toggling the burnwire pins.
        """
        error = None
        try:
            self.number_of_attempts += 1

            # Attempt to set enable_burn, this may raise an exception
            try:
                self._enable_burn.value = self._enable
            except Exception as e:
                error = RuntimeError("Failed to set enable_burn pin")
                raise error from e

            time.sleep(0.1)  # Short pause to stabilize load switches

            # Burnwire becomes active
            try:
                self._fire_burn.value = self._enable
            except Exception as e:
                error = RuntimeError("Failed to set fire_burn pin")
                raise error from e

            time.sleep(duration)

        finally:
            # Burnwire cleanup in the finally block to ensure it always happens
            try:
                self._fire_burn.value = self._disable
                self._enable_burn.value = self._disable
                self._log.info("Burnwire Safed")
            except Exception as e:
                # Only log critical if this wasn't caused by the original error
                if error is None:
                    self._log.critical("Failed to safe burnwire pins!", e)

            # Re-raise the original error if there was one
            if error is not None:
                raise error
