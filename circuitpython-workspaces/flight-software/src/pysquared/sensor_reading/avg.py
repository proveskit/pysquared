"""File with helper for averaging sensor readings."""

from .current import Current
from .voltage import Voltage

try:
    from typing import Callable
except ImportError:
    pass


def avg_readings(
    func: Callable[..., Current | Voltage], num_readings: int = 50
) -> float:
    """Gets the average of the readings from a function.

    Args:
        func: The function to call.
        num_readings: The number of readings to take.

    Returns:
        The average of the readings, or None if the readings could not be taken.

    Raises:
        RuntimeError: If there is an error retrieving the reading from the function.
    """
    readings: float = 0
    for _ in range(num_readings):
        try:
            reading = func()
        except Exception as e:
            raise RuntimeError(f"Error retrieving reading from {func.__name__}") from e

        readings += reading.value
    return readings / num_readings
