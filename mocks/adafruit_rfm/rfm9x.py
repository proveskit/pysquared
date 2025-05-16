"""
Mock for Adafruit RFM9x
https://github.com/adafruit/Adafruit_CircuitPython_RFM/blob/8a55e345501e038996b2aa89e71d4e5e3ddbdebe/adafruit_rfm/rfm9x.py
"""

from .rfm_common import RFMSPI

# Type hinting only
try:
    from typing import Literal
except ImportError:
    pass


class RFM9x(RFMSPI):
    ack_delay: float | None = None
    enable_crc: bool
    spreading_factor: Literal[6, 7, 8, 9, 10, 11, 12]
    tx_power: int
    preamble_length: int
    low_datarate_optimize: int

    def __init__(self, spi, cs, reset, frequency) -> None: ...
