# SPDX-FileCopyrightText: 2024 Jerry Needell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_rfm.rfm9x`
====================================================

CircuitPython module for the RFM95/6/7/8 LoRa 433/915mhz radio modules.

* Author(s): Jerry Needell
"""

import time

from micropython import const

from adafruit_rfm.rfm_common import RFMSPI

try:
    import busio
    import digitalio
    from circuitpython_typing import ReadableBuffer

    try:
        from typing import Literal, Optional
    except ImportError:
        from typing_extensions import Literal

except ImportError:
    pass

__version__ = "1.0.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_RFM.git"

# pylint: disable=duplicate-code

# Internal constants:
# Register names (FSK Mode even though we use LoRa instead, from table 85)
_RF95_REG_00_FIFO = const(0x00)
_RF95_REG_01_OP_MODE = const(0x01)
_RF95_REG_06_FRF_MSB = const(0x06)
_RF95_REG_07_FRF_MID = const(0x07)
_RF95_REG_08_FRF_LSB = const(0x08)
_RF95_REG_09_PA_CONFIG = const(0x09)
_RF95_REG_0A_PA_RAMP = const(0x0A)
_RF95_REG_0B_OCP = const(0x0B)
_RF95_REG_0C_LNA = const(0x0C)
_RF95_REG_0D_FIFO_ADDR_PTR = const(0x0D)
_RF95_REG_0E_FIFO_TX_BASE_ADDR = const(0x0E)
_RF95_REG_0F_FIFO_RX_BASE_ADDR = const(0x0F)
_RF95_REG_10_FIFO_RX_CURRENT_ADDR = const(0x10)
_RF95_REG_11_IRQ_FLAGS_MASK = const(0x11)
_RF95_REG_12_IRQ_FLAGS = const(0x12)
_RF95_REG_13_RX_NB_BYTES = const(0x13)
_RF95_REG_14_RX_HEADER_CNT_VALUE_MSB = const(0x14)
_RF95_REG_15_RX_HEADER_CNT_VALUE_LSB = const(0x15)
_RF95_REG_16_RX_PACKET_CNT_VALUE_MSB = const(0x16)
_RF95_REG_17_RX_PACKET_CNT_VALUE_LSB = const(0x17)
_RF95_REG_18_MODEM_STAT = const(0x18)
_RF95_REG_19_PKT_SNR_VALUE = const(0x19)
_RF95_REG_1A_PKT_RSSI_VALUE = const(0x1A)
_RF95_REG_1B_RSSI_VALUE = const(0x1B)
_RF95_REG_1C_HOP_CHANNEL = const(0x1C)
_RF95_REG_1D_MODEM_CONFIG1 = const(0x1D)
_RF95_REG_1E_MODEM_CONFIG2 = const(0x1E)
_RF95_REG_1F_SYMB_TIMEOUT_LSB = const(0x1F)
_RF95_REG_20_PREAMBLE_MSB = const(0x20)
_RF95_REG_21_PREAMBLE_LSB = const(0x21)
_RF95_REG_22_PAYLOAD_LENGTH = const(0x22)
_RF95_REG_23_MAX_PAYLOAD_LENGTH = const(0x23)
_RF95_REG_24_HOP_PERIOD = const(0x24)
_RF95_REG_25_FIFO_RX_BYTE_ADDR = const(0x25)
_RF95_REG_26_MODEM_CONFIG3 = const(0x26)

_RF95_REG_40_DIO_MAPPING1 = const(0x40)
_RF95_REG_41_DIO_MAPPING2 = const(0x41)
_RF95_REG_42_VERSION = const(0x42)

_RF95_REG_4B_TCXO = const(0x4B)
_RF95_REG_4D_PA_DAC = const(0x4D)
_RF95_REG_5B_FORMER_TEMP = const(0x5B)
_RF95_REG_61_AGC_REF = const(0x61)
_RF95_REG_62_AGC_THRESH1 = const(0x62)
_RF95_REG_63_AGC_THRESH2 = const(0x63)
_RF95_REG_64_AGC_THRESH3 = const(0x64)

_RF95_DETECTION_OPTIMIZE = const(0x31)
_RF95_DETECTION_THRESHOLD = const(0x37)

_RF95_PA_DAC_DISABLE = const(0x04)
_RF95_PA_DAC_ENABLE = const(0x07)

# The crystal oscillator frequency of the module
_RF95_FXOSC = 32000000.0

# The Frequency Synthesizer step = RH_RF95_FXOSC / 2^^19
_RF95_FSTEP = _RF95_FXOSC / 524288

# RadioHead specific compatibility constants.
_RH_BROADCAST_ADDRESS = const(0xFF)

# The acknowledgement bit in the FLAGS
# The top 4 bits of the flags are reserved for RadioHead. The lower 4 bits are reserved
# for application layer use.
_RH_FLAGS_ACK = const(0x80)
_RH_FLAGS_RETRY = const(0x40)

# User facing constants:
SLEEP_MODE = 0b000
STANDBY_MODE = 0b001
FS_TX_MODE = 0b010
TX_MODE = 0b011
FS_RX_MODE = 0b100
RX_MODE = 0b101


# pylint: disable=too-many-instance-attributes
class RFM9x(RFMSPI):
    """Interface to a RFM95/6/7/8 LoRa radio module.  Allows sending and
    receiving bytes of data in long range LoRa mode at a support board frequency
    (433/915mhz).

    You must specify the following parameters:
    - spi: The SPI bus connected to the radio.
    - cs: The CS pin DigitalInOut connected to the radio.
    - reset: The reset/RST pin DigialInOut connected to the radio.
    - frequency: The frequency (in mhz) of the radio module (433/915mhz typically).

    You can optionally specify:
    - preamble_length: The length in bytes of the packet preamble (default 8).
    - high_power: Boolean to indicate a high power board (RFM95, etc.).  Default
    is True for high power.
    - baudrate: Baud rate of the SPI connection, default is 5mhz but you might
    choose to lower to 1mhz if using long wires or a breadboard.
    - agc: Boolean to Enable/Disable Automatic Gain Control - Default=False (AGC off)
    - crc: Boolean to Enable/Disable Cyclic Redundancy Check - Default=True (CRC Enabled)
    Remember this library makes a best effort at receiving packets with pure
    Python code.  Trying to receive packets too quickly will result in lost data
    so limit yourself to simple scenarios of sending and receiving single
    packets at a time.

    Also note this library tries to be compatible with raw RadioHead Arduino
    library communication. This means the library sets up the radio modulation
    to match RadioHead's defaults.
    Advanced RadioHead features like address/node specific packets
    or "reliable datagram" delivery are supported however due to the
    limitations noted, "reliable datagram" is still subject to missed packets.
    """

    operation_mode = RFMSPI.RegisterBits(_RF95_REG_01_OP_MODE, bits=3)

    low_frequency_mode = RFMSPI.RegisterBits(_RF95_REG_01_OP_MODE, offset=3, bits=1)

    modulation_type = RFMSPI.RegisterBits(_RF95_REG_01_OP_MODE, offset=5, bits=2)

    # Long range/LoRa mode can only be set in sleep mode!
    long_range_mode = RFMSPI.RegisterBits(_RF95_REG_01_OP_MODE, offset=7, bits=1)

    output_power = RFMSPI.RegisterBits(_RF95_REG_09_PA_CONFIG, bits=4)

    max_power = RFMSPI.RegisterBits(_RF95_REG_09_PA_CONFIG, offset=4, bits=3)

    pa_select = RFMSPI.RegisterBits(_RF95_REG_09_PA_CONFIG, offset=7, bits=1)

    pa_dac = RFMSPI.RegisterBits(_RF95_REG_4D_PA_DAC, bits=3)

    dio0_mapping = RFMSPI.RegisterBits(_RF95_REG_40_DIO_MAPPING1, offset=6, bits=2)

    auto_agc = RFMSPI.RegisterBits(_RF95_REG_26_MODEM_CONFIG3, offset=2, bits=1)

    low_datarate_optimize = RFMSPI.RegisterBits(_RF95_REG_26_MODEM_CONFIG3, offset=3, bits=1)

    lna_boost_hf = RFMSPI.RegisterBits(_RF95_REG_0C_LNA, offset=0, bits=2)

    auto_ifon = RFMSPI.RegisterBits(_RF95_DETECTION_OPTIMIZE, offset=7, bits=1)

    detection_optimize = RFMSPI.RegisterBits(_RF95_DETECTION_OPTIMIZE, offset=0, bits=3)

    bw_bins = (7800, 10400, 15600, 20800, 31250, 41700, 62500, 125000, 250000)

    def __init__(  # noqa: PLR0913
        self,
        spi: busio.SPI,
        cs: digitalio.DigitalInOut,  # pylint: disable=invalid-name
        rst: digitalio.DigitalInOut,
        frequency: int,
        *,
        preamble_length: int = 8,
        high_power: bool = True,
        baudrate: int = 5000000,
        agc: bool = False,
        crc: bool = True,
    ) -> None:
        super().__init__(spi, cs, baudrate=baudrate)
        self.module = "RFM9X"
        self.max_packet_length = 252
        self.high_power = high_power
        # Device support SPI mode 0 (polarity & phase = 0) up to a max of 10mhz.
        # Set Default Baudrate to 5MHz to avoid problems
        # self._device = spidev.SPIDevice(spi, cs, baudrate=baudrate, polarity=0, phase=0)
        # Setup reset as a digital output - initially High
        # This line is pulled low as an output quickly to trigger a reset.
        self._rst = rst
        # initialize Reset High
        self._rst.switch_to_output(value=True)
        self.reset()
        # No device type check!  Catch an error from the very first request and
        # throw a nicer message to indicate possible wiring problems.
        version = self.read_u8(address=_RF95_REG_42_VERSION)
        if version != 18:
            raise RuntimeError(
                "Failed to find rfm9x with expected version -- check wiring. Version found:",
                hex(version),
            )

        # Set sleep mode, wait 10s and confirm in sleep mode (basic device check).
        # Also set long range mode (LoRa mode) as it can only be done in sleep.
        self.sleep()
        time.sleep(0.01)
        self.long_range_mode = True
        if self.operation_mode != SLEEP_MODE or not self.long_range_mode:
            raise RuntimeError("Failed to configure radio for LoRa mode, check wiring!")
        # clear default setting for access to LF registers if frequency > 525MHz
        if frequency > 525:
            self.low_frequency_mode = 0
        # Setup entire 256 byte FIFO
        self.write_u8(_RF95_REG_0E_FIFO_TX_BASE_ADDR, 0x00)
        self.write_u8(_RF95_REG_0F_FIFO_RX_BASE_ADDR, 0x00)
        # Set mode idle
        self.idle()
        # Set frequency
        self.frequency_mhz = frequency
        # Set preamble length (default 8 bytes to match radiohead).
        self.preamble_length = preamble_length
        # Defaults set modem config to RadioHead compatible Bw125Cr45Sf128 mode.
        self.signal_bandwidth = 125000
        self.coding_rate = 5
        self.spreading_factor = 7
        # Default to enable CRC checking on incoming packets.
        self.enable_crc = crc
        """CRC Enable state"""
        # set AGC - Default = False
        self.auto_agc = agc
        """Automatic Gain Control state"""
        # Set transmit power to 13 dBm, a safe value any module supports.
        self.tx_power = 13

    def reset(self) -> None:
        """Perform a reset of the chip."""
        # See section 7.2.2 of the datasheet for reset description.
        self._rst.value = False  # Set Reset Low
        time.sleep(0.0001)  # 100 us
        self._rst.value = True  # set Reset High
        time.sleep(0.005)  # 5 ms

    def idle(self) -> None:
        """Enter idle standby mode."""
        self.operation_mode = STANDBY_MODE

    def sleep(self) -> None:
        """Enter sleep mode."""
        self.operation_mode = SLEEP_MODE

    def listen(self) -> None:
        """Listen for packets to be received by the chip.  Use :py:func:`receive`
        to listen, wait and retrieve packets as they're available.
        """
        self.operation_mode = RX_MODE
        self.dio0_mapping = 0b00  # Interrupt on rx done.

    def transmit(self) -> None:
        """Transmit a packet which is queued in the FIFO.  This is a low level
        function for entering transmit mode and more.  For generating and
        transmitting a packet of data use :py:func:`send` instead.
        """
        self.operation_mode = TX_MODE
        self.dio0_mapping = 0b01  # Interrupt on tx done.

    @property
    def preamble_length(self) -> int:
        """The length of the preamble for sent and received packets, an unsigned
        16-bit value.  Received packets must match this length or they are
        ignored! Set to 8 to match the RadioHead RFM95 library.
        """
        msb = self.read_u8(_RF95_REG_20_PREAMBLE_MSB)
        lsb = self.read_u8(_RF95_REG_21_PREAMBLE_LSB)
        return ((msb << 8) | lsb) & 0xFFFF

    @preamble_length.setter
    def preamble_length(self, val: int) -> None:
        assert 0 <= val <= 65535
        self.write_u8(_RF95_REG_20_PREAMBLE_MSB, (val >> 8) & 0xFF)
        self.write_u8(_RF95_REG_21_PREAMBLE_LSB, val & 0xFF)

    @property
    def frequency_mhz(self) -> Literal[433.0, 915.0]:
        """The frequency of the radio in Megahertz. Only the allowed values for
        your radio must be specified (i.e. 433 vs. 915 mhz)!
        """
        msb = self.read_u8(_RF95_REG_06_FRF_MSB)
        mid = self.read_u8(_RF95_REG_07_FRF_MID)
        lsb = self.read_u8(_RF95_REG_08_FRF_LSB)
        frf = ((msb << 16) | (mid << 8) | lsb) & 0xFFFFFF
        frequency = (frf * _RF95_FSTEP) / 1000000.0
        return frequency

    @frequency_mhz.setter
    def frequency_mhz(self, val: Literal[433.0, 915.0]) -> None:
        if val < 240 or val > 960:
            raise RuntimeError("frequency_mhz must be between 240 and 960")
        # Calculate FRF register 24-bit value.
        frf = int((val * 1000000.0) / _RF95_FSTEP) & 0xFFFFFF
        # Extract byte values and update registers.
        msb = frf >> 16
        mid = (frf >> 8) & 0xFF
        lsb = frf & 0xFF
        self.write_u8(_RF95_REG_06_FRF_MSB, msb)
        self.write_u8(_RF95_REG_07_FRF_MID, mid)
        self.write_u8(_RF95_REG_08_FRF_LSB, lsb)

    @property
    def tx_power(self) -> int:
        """The transmit power in dBm. Can be set to a value from 5 to 23 for
        high power devices (RFM95/96/97/98, high_power=True) or -1 to 14 for low
        power devices. Only integer power levels are actually set (i.e. 12.5
        will result in a value of 12 dBm).
        The actual maximum setting for high_power=True is 20dBm but for values > 20
        the PA_BOOST will be enabled resulting in an additional gain of 3dBm.
        The actual setting is reduced by 3dBm.
        The reported value will reflect the reduced setting.
        """
        if self.high_power:
            return self.output_power + 5
        return self.output_power - 1

    @tx_power.setter
    def tx_power(self, val: int) -> None:
        val = int(val)
        if self.high_power:
            if val < 5 or val > 23:
                raise RuntimeError("tx_power must be between 5 and 23")
            # Enable power amp DAC if power is above 20 dB.
            # Lower setting by 3db when PA_BOOST enabled - see Data Sheet  Section 6.4
            if val > 20:
                self.pa_dac = _RF95_PA_DAC_ENABLE
                val -= 3
            else:
                self.pa_dac = _RF95_PA_DAC_DISABLE
            self.pa_select = True
            self.output_power = (val - 5) & 0x0F
        else:
            assert -1 <= val <= 14
            self.pa_select = False
            self.max_power = 0b111  # Allow max power output.
            self.output_power = (val + 1) & 0x0F

    @property
    def rssi(self) -> float:
        """The received strength indicator (in dBm) of the last received message."""
        # Read RSSI register and convert to value using formula in datasheet.
        # Remember in LoRa mode the payload register changes function to RSSI!
        raw_rssi = self.read_u8(_RF95_REG_1A_PKT_RSSI_VALUE)
        if self.low_frequency_mode:
            raw_rssi -= 157
        else:
            raw_rssi -= 164
        return float(raw_rssi)

    @property
    def snr(self) -> float:
        """The SNR (in dB) of the last received message."""
        # Read SNR 0x19 register and convert to value using formula in datasheet.
        # SNR(dB) = PacketSnr [twos complement] / 4
        snr_byte = self.read_u8(_RF95_REG_19_PKT_SNR_VALUE)
        if snr_byte > 127:
            snr_byte = (256 - snr_byte) * -1
        return snr_byte / 4

    @property
    def signal_bandwidth(self) -> int:
        """The signal bandwidth used by the radio (try setting to a higher
        value to increase throughput or to a lower value to increase the
        likelihood of successfully received payloads).  Valid values are
        listed in RFM9x.bw_bins."""
        bw_id = (self.read_u8(_RF95_REG_1D_MODEM_CONFIG1) & 0xF0) >> 4
        if bw_id >= len(self.bw_bins):
            current_bandwidth = 500000
        else:
            current_bandwidth = self.bw_bins[bw_id]
        return current_bandwidth

    @signal_bandwidth.setter
    def signal_bandwidth(self, val: int) -> None:
        # Set signal bandwidth (set to 125000 to match RadioHead Bw125).
        for bw_id, cutoff in enumerate(self.bw_bins):
            if val <= cutoff:
                break
        else:
            bw_id = 9
        self.write_u8(
            _RF95_REG_1D_MODEM_CONFIG1,
            (self.read_u8(_RF95_REG_1D_MODEM_CONFIG1) & 0x0F) | (bw_id << 4),
        )
        if val >= 500000:
            # see Semtech SX1276 errata note 2.3
            self.auto_ifon = True
            # see Semtech SX1276 errata note 2.1
            if self.low_frequency_mode:
                self.write_u8(0x36, 0x02)
                self.write_u8(0x3A, 0x7F)
            else:
                self.write_u8(0x36, 0x02)
                self.write_u8(0x3A, 0x64)
        else:
            # see Semtech SX1276 errata note 2.3
            self.auto_ifon = False
            self.write_u8(0x36, 0x03)
            if val == 7800:
                self.write_u8(0x2F, 0x48)
            elif val >= 62500:
                # see Semtech SX1276 errata note 2.3
                self.write_u8(0x2F, 0x40)
            else:
                self.write_u8(0x2F, 0x44)
            self.write_u8(0x30, 0)

    @property
    def coding_rate(self) -> Literal[5, 6, 7, 8]:
        """The coding rate used by the radio to control forward error
        correction (try setting to a higher value to increase tolerance of
        short bursts of interference or to a lower value to increase bit
        rate).  Valid values are limited to 5, 6, 7, or 8."""
        cr_id = (self.read_u8(_RF95_REG_1D_MODEM_CONFIG1) & 0x0E) >> 1
        denominator = cr_id + 4
        return denominator

    @coding_rate.setter
    def coding_rate(self, val: Literal[5, 6, 7, 8]) -> None:
        # Set coding rate (set to 5 to match RadioHead Cr45).
        denominator = min(max(val, 5), 8)
        cr_id = denominator - 4
        self.write_u8(
            _RF95_REG_1D_MODEM_CONFIG1,
            (self.read_u8(_RF95_REG_1D_MODEM_CONFIG1) & 0xF1) | (cr_id << 1),
        )

    @property
    def spreading_factor(self) -> Literal[6, 7, 8, 9, 10, 11, 12]:
        """The spreading factor used by the radio (try setting to a higher
        value to increase the receiver's ability to distinguish signal from
        noise or to a lower value to increase the data transmission rate).
        Valid values are limited to 6, 7, 8, 9, 10, 11, or 12."""
        sf_id = (self.read_u8(_RF95_REG_1E_MODEM_CONFIG2) & 0xF0) >> 4
        return sf_id

    @spreading_factor.setter
    def spreading_factor(self, val: Literal[6, 7, 8, 9, 10, 11, 12]) -> None:
        # Set spreading factor (set to 7 to match RadioHead Sf128).
        val = min(max(val, 6), 12)

        if val == 6:
            self.detection_optimize = 0x5
        else:
            self.detection_optimize = 0x3

        self.write_u8(_RF95_DETECTION_THRESHOLD, 0x0C if val == 6 else 0x0A)
        self.write_u8(
            _RF95_REG_1E_MODEM_CONFIG2,
            ((self.read_u8(_RF95_REG_1E_MODEM_CONFIG2) & 0x0F) | ((val << 4) & 0xF0)),
        )

    @property
    def enable_crc(self) -> bool:
        """Set to True to enable hardware CRC checking of incoming packets.
        Incoming packets that fail the CRC check are not processed.  Set to
        False to disable CRC checking and process all incoming packets."""
        return (self.read_u8(_RF95_REG_1E_MODEM_CONFIG2) & 0x04) == 0x04

    @enable_crc.setter
    def enable_crc(self, val: bool) -> None:
        # Optionally enable CRC checking on incoming packets.
        if val:
            self.write_u8(
                _RF95_REG_1E_MODEM_CONFIG2,
                self.read_u8(_RF95_REG_1E_MODEM_CONFIG2) | 0x04,
            )
        else:
            self.write_u8(
                _RF95_REG_1E_MODEM_CONFIG2,
                self.read_u8(_RF95_REG_1E_MODEM_CONFIG2) & 0xFB,
            )

    @property
    def crc_error(self) -> bool:
        """crc status"""
        return (self.read_u8(_RF95_REG_12_IRQ_FLAGS) & 0x20) >> 5

    def packet_sent(self) -> bool:
        """Transmit status"""
        return (self.read_u8(_RF95_REG_12_IRQ_FLAGS) & 0x8) >> 3

    def payload_ready(self) -> bool:
        """Receive status"""
        return (self.read_u8(_RF95_REG_12_IRQ_FLAGS) & 0x40) >> 6

    def clear_interrupt(self) -> None:
        """Clear Interrupt flags"""
        self.write_u8(_RF95_REG_12_IRQ_FLAGS, 0xFF)

    def fill_fifo(self, payload: ReadableBuffer) -> None:
        """len_data is not used but is here for compatibility with rfm69
        Fill the FIFO with a packet to send"""
        self.write_u8(_RF95_REG_0D_FIFO_ADDR_PTR, 0x00)  # FIFO starts at 0.
        # Write payload.
        self.write_from(_RF95_REG_00_FIFO, payload)
        # Write payload and header length.
        self.write_u8(_RF95_REG_22_PAYLOAD_LENGTH, len(payload))

    def read_fifo(self) -> Optional[bytearray]:
        """Read the data from the FIFO."""
        # Read the length of the FIFO.
        fifo_length = self.read_u8(_RF95_REG_13_RX_NB_BYTES)
        packet = None  # return None if FIFO empty
        if fifo_length > 0:  # read and clear the FIFO if anything in it
            packet = bytearray(fifo_length)
            current_addr = self.read_u8(_RF95_REG_10_FIFO_RX_CURRENT_ADDR)
            self.write_u8(_RF95_REG_0D_FIFO_ADDR_PTR, current_addr)
            # read the packet
            self.read_into(_RF95_REG_00_FIFO, packet)

            # clear interrupt
            self.write_u8(_RF95_REG_12_IRQ_FLAGS, 0xFF)
        return packet
