"""Mock for the CircuitPython supervisor module.

This module provides a mock implementation of the CircuitPython supervisor module
for testing purposes. It allows for simulating the behavior of the supervisor
module without the need for actual CircuitPython hardware.
"""


def set_next_code_file(filename: str) -> None:
    """Mock implementation of supervisor.set_next_code_file.

    Args:
        filename: The name of the code file to execute on next reset.
    """
    pass
