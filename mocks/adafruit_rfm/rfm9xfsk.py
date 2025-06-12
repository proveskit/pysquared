"""
Mock for Adafruit RFM9xFSK
https://github.com/adafruit/Adafruit_CircuitPython_RFM/blob/8a55e345501e038996b2aa89e71d4e5e3ddbdebe/adafruit_rfm/rfm9xfsk.py
"""

from .rfm_common import RFMSPI


class RFM9xFSK(RFMSPI):
    modulation_type: int
    fsk_broadcast_address: int
    fsk_node_address: int
    max_packet_length: int
    last_rssi: float
    tx_power: int

    def __init__(self, spi, cs, reset, frequency) -> None: ...
