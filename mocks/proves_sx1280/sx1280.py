"""
Mock for PROVES SX1280
https://github.com/proveskit/CircuitPython_SX1280/blob/6bcb9fc2922801d1eddbe6cec2b515448c0578ca/proves_sx1280/sx1280.py
"""

from busio import SPI
from digitalio import DigitalInOut


class SX1280:
    def __init__(
        self,
        spi: SPI,
        cs: DigitalInOut,
        reset: DigitalInOut,
        busy: DigitalInOut,
        frequency: float,
        *,
        debug: bool = False,
        txen: DigitalInOut | bool = False,
        rxen: DigitalInOut | bool = False,
    ) -> None: ...

    def send(
        self,
        data,
        pin=None,
        irq=False,
        header=True,
        ID=0,
        target=0,
        action=0,
        keep_listening=False,
    ): ...

    def receive(self, continuous=True, keep_listening=True) -> bytearray | None: ...
