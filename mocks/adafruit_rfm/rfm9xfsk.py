"""
Mock for Adafruit RFM9xFSK
https://github.com/adafruit/Adafruit_CircuitPython_RFM/blob/8a55e345501e038996b2aa89e71d4e5e3ddbdebe/adafruit_rfm/rfm9xfsk.py
"""


class RFM9xFSK:
    def __init__(self, spi, cs, reset, frequency) -> None:
        self.modulation_type = None
