"""Load switch manager protocol for generic components."""


class LoadSwitchManagerProto:
    """Protocol for load switch management in generic systems.
    This protocol defines the interface for managing load switches that control
    power to components. Load switches can be enabled, disabled,
    and reset with momentary power cycling.
    """

    def enable_load(self) -> None:
        """Enable the load switch to provide power to the component.
        :raises RuntimeError: If the load switch cannot be enabled due to hardware issues
        """
        ...

    def disable_load(self) -> None:
        """Disable the load switch to cut power to the component.
        :raises RuntimeError: If the load switch cannot be disabled due to hardware issues
        """
        ...

    def reset_load(self) -> None:
        """Reset the load switch by momentarily disabling then re-enabling it.
        This method performs a momentary power cycle (0.1s) to reset the load switch
        and any connected components. Errors from underlying drivers are reraised.
        :raises RuntimeError: If the load switch cannot be reset due to hardware issues
        """
        ...

    @property
    def is_enabled(self) -> bool:
        """Check if the load switch is currently enabled.
        :raises RuntimeError: If the load switch state cannot be read due to hardware issues
        :return: True if the load switch is enabled, False otherwise
        """
        ...
