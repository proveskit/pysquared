"""
Mock for Adafruit RFM SPI
https://github.com/adafruit/Adafruit_CircuitPython_RFM/blob/8a55e345501e038996b2aa89e71d4e5e3ddbdebe/adafruit_rfm/rfm_common.py
"""

from typing import Optional

from circuitpython_typing import ReadableBuffer


class RFMSPI:
    node: int
    destination: int

    def send(
        self,
        data: ReadableBuffer,
        *,
        keep_listening: bool = False,
        destination: Optional[int] = None,
        node: Optional[int] = None,
        identifier: Optional[int] = None,
        flags: Optional[int] = None,
    ) -> bool: ...

    def read_u8(self, address: int) -> int: ...

    def receive(
        self,
        *,
        keep_listening: bool = True,
        with_header: bool = False,
        timeout: Optional[float] = None,
    ) -> Optional[bytearray]: ...
