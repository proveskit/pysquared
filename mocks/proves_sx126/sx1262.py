"""
Mock for PROVES SX126
https://github.com/proveskit/micropySX126X/blob/master/proves_sx126/sx1262.py
"""

from .sx126x import (
    SX126X_GFSK_ADDRESS_FILT_OFF,
    SX126X_GFSK_PREAMBLE_DETECT_16,
    SX126X_SYNC_WORD_PRIVATE,
)

# type-hinting only
try:
    from busio import SPI
    from digitalio import DigitalInOut
except ImportError:
    pass


class SX1262:
    def __init__(
        self,
        spi: SPI,
        cs: DigitalInOut,
        irq: DigitalInOut,
        rst: DigitalInOut,
        gpio: DigitalInOut,
    ) -> None: ...

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
    ): ...

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
    ): ...
