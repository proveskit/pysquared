import time

from digitalio import DigitalInOut

from ....logger import Logger
from ....protos.burnwire import BurnwireProto

"""
Usage Example:

from pysquared.hardware.burnwire.manager.burnwire import BurnwireManager
from pysquared.hardware.digitalio import initialize_pin

# Initialize pins
enable_pin = initialize_pin(logger, board.FIRE_DEPLOY1A, Direction.OUTPUT, False)
fire_pin = initialize_pin(logger, board.FIRE_DEPLOY1B, Direction.OUTPUT, False)

# Create burnwire manager
antenna_deployment = BurnwireManager(logger, enable_pin, fire_pin, enable_logic=False)

# Fire the burnwire with error handling
try:
    success = antenna_deployment.burn(timeout_duration=5.0)
    if success:
        logger.info("Burnwire fired successfully")
    else:
        logger.error("Burnwire failed to fire")
except RuntimeError as e:
    logger.error("Hardware error during burnwire operation", err=e)
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
        """
        self._log: Logger = logger
        self._enable_logic: bool = enable_logic

        self._enable_burn: DigitalInOut = enable_burn
        self._fire_burn: DigitalInOut = fire_burn

        self.number_of_attempts: int = 0

    def burn(self, timeout_duration: float = 5.0) -> bool:
        """Fires the burnwire for a specified amount of time

        :param float timeout_duration: The max amount of time to keep the burnwire on for.

        :return: A Boolean indicating whether the burn occurred successfully
        :rtype: bool

        :raises Exception: If there is an error toggling the burnwire pins.
        """
        _start_time = time.monotonic()

        self._log.debug(
            f"BURN Attempt {self.number_of_attempts} Started with Duration {timeout_duration}s"
        )
        try:
            self._attempt_burn(timeout_duration)
            return True

        except KeyboardInterrupt:
            self._log.debug(
                f"Burn Attempt Interupted after {time.monotonic() - _start_time:.2f} seconds"
            )
            return False

        except RuntimeError as e:
            self._log.critical(
                f"BURN Attempt {self.number_of_attempts} Failed!",
                e,
            )
            return False

    def _enable(self):
        """
        Activates the burnwire mechanism by enabling the control pins.

        This method sets the `_enable_burn` and `_fire_burn` pins to the logic level specified by `_enable_logic`.
        It first enables the burnwire circuit, waits briefly to allow load switches to stabilize, and then fires the burnwire.
        Raises a RuntimeError if setting either pin fails.

        Raises:
            RuntimeError: If unable to set the enable or fire pins due to hardware or communication errors.
        """
        try:
            self._enable_burn.value = self._enable_logic
        except Exception as e:
            raise RuntimeError("Failed to set enable_burn pin") from e

        time.sleep(0.1)  # Short pause to stabilize load switches

        # Burnwire becomes active
        try:
            self._fire_burn.value = self._enable_logic
        except Exception as e:
            raise RuntimeError("Failed to set fire_burn pin") from e

    def _disable(self):
        """
        Safes the burnwire by disabling the fire and enable pins.

        Sets the `_fire_burn` and `_enable_burn` pin values to the logical opposite of `_enable_logic`,
        effectively disabling the burnwire mechanism. Logs the action for traceability.
        Raises a RuntimeError if the operation fails.

        Raises:
            RuntimeError: If unable to set the burnwire pins to the safe state.
        """
        try:
            self._fire_burn.value = not self._enable_logic
            self._enable_burn.value = not self._enable_logic
            self._log.debug("Burnwire safed")
        except Exception as e:
            raise RuntimeError("Failed to safe burnwire pins") from e

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

            # Burnwire becomes active
            try:
                self._enable()
            except Exception as e:
                error = RuntimeError("Failed to set fire_burn pin")
                raise error from e

            time.sleep(duration)

        except RuntimeError as e:
            # Log the error if it occurs during the burn process
            self._log.critical(
                f"Burnwire failed on attempt {self.number_of_attempts}!", e
            )
            raise e

        except KeyboardInterrupt as exc:
            self._log.warning(f"BURN Attempt {self.number_of_attempts} Interrupted!")
            raise KeyboardInterrupt("Burnwire operation interrupted by user") from exc

        finally:
            # Burnwire cleanup in the finally block to ensure it always happens
            try:
                self._disable()
                self._log.debug("Burnwire Safed")
            except Exception as e:
                # Only log critical if this wasn't caused by the original error
                if error is None:
                    self._log.critical("Failed to safe burnwire pins!", e)

            # Re-raise the original error if there was one
            if error is not None:
                raise error
