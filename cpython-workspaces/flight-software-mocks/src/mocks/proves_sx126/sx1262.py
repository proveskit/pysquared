"""Mock for the PROVES SX1262 radio module.

This module provides a mock implementation of the PROVES SX1262 radio module for
testing purposes. It allows for simulating the behavior of the SX1262 without the
need for actual hardware.
"""

from busio import SPI
from digitalio import DigitalInOut

from .sx126x import (
    SX126X_GFSK_ADDRESS_FILT_OFF,
    SX126X_GFSK_PREAMBLE_DETECT_16,
    SX126X_SYNC_WORD_PRIVATE,
)

try:
    from typing import Literal
except ImportError:
    pass


class SX1262:
    """A mock SX1262 radio module."""

    radio_modulation: str = "FSK"

    def __init__(
        self,
        spi: SPI,
        cs: DigitalInOut,
        irq: DigitalInOut,
        rst: DigitalInOut,
        gpio: DigitalInOut,
    ) -> None:
        """Initializes the mock SX1262.

        Args:
            spi: The SPI bus to use.
            cs: The chip select pin.
            irq: The interrupt request pin.
            rst: The reset pin.
            gpio: The GPIO pin.
        """
        ...

    def begin(
        self,
        freq=434.0,
        bw=125.0,
        sf=9,
        cr=7,
        syncWord=SX126X_SYNC_WORD_PRIVATE,
        power=14,
        currentLimit=60.0,
        preambleLength=8,
        implicit=False,
        implicitLen=0xFF,
        crcOn=True,
        txIq=False,
        rxIq=False,
        tcxoVoltage=1.6,
        useRegulatorLDO=False,
        blocking=True,
    ):
        """Initializes the radio in LoRa mode."""
        ...

    def beginFSK(
        self,
        freq=434.0,
        br=48.0,
        freqDev=50.0,
        rxBw=156.2,
        power=14,
        currentLimit=60.0,
        preambleLength=16,
        dataShaping=0.5,
        syncWord=[0x2D, 0x01],
        syncBitsLength=16,
        addrFilter=SX126X_GFSK_ADDRESS_FILT_OFF,
        addr=0x00,
        crcLength=2,
        crcInitial=0x1D0F,
        crcPolynomial=0x1021,
        crcInverted=True,
        whiteningOn=True,
        whiteningInitial=0x0100,
        fixedPacketLength=False,
        packetLength=0xFF,
        preambleDetectorLength=SX126X_GFSK_PREAMBLE_DETECT_16,
        tcxoVoltage=1.6,
        useRegulatorLDO=False,
        blocking=True,
    ):
        """Initializes the radio in FSK mode."""
        ...

    def send(self, data) -> tuple[Literal[0], int] | tuple[int, int]:
        """Sends data over the radio."""
        ...

    def recv(
        self, len=0, timeout_en=False, timeout_ms=0
    ) -> tuple[bytes, int] | tuple[Literal[b""], int]:
        """Receives data from the radio."""
        ...
