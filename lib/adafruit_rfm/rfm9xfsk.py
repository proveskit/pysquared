# SPDX-FileCopyrightText: 2024 Jerry Needell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_rfm.rfm9xfsk`
====================================================

CircuitPython module for the RFM95/6/7/8 FSK 433/915mhz radio modules.

* Author(s): Jerry Needell
"""

import time

from micropython import const

from adafruit_rfm.rfm_common import RFMSPI

try:
    from typing import Optional

    import busio
    import digitalio
    from circuitpython_typing import ReadableBuffer

    try:
        from typing import Literal
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
_RF95_REG_02_BITRATE_MSB = const(0x02)
_RF95_REG_03_BITRATE_LSB = const(0x03)
_RF95_REG_04_FDEV_MSB = const(0x4)
_RF95_REG_05_FDEV_LSB = const(0x5)
_RF95_REG_06_FRF_MSB = const(0x06)
_RF95_REG_07_FRF_MID = const(0x07)
_RF95_REG_08_FRF_LSB = const(0x08)
_RF95_REG_09_PA_CONFIG = const(0x09)
_RF95_REG_0A_PA_RAMP = const(0x0A)
_RF95_REG_0B_OCP = const(0x0B)
_RF95_REG_0C_LNA = const(0x0C)
_RF95_REG_0D_RX_CFG = const(0x0D)
_RF95_REG_0E_RSSI_CFG = const(0x0E)
_RF95_REG_0F_RSSI_COLLISION = const(0x0F)
_RF95_REG_10_RSSI_THRESH = const(0x10)
_RF95_REG_11_RSSI_VALUE = const(0x11)
_RF95_REG_12_RX_BW = const(0x12)
_RF95_REG_13_AFC_BW = const(0x13)
_RF95_REG_14_OOK_PEAK = const(0x14)
_RF95_REG_15_OOK_FIX = const(0x15)
_RF95_REG_16_OOK_AVG = const(0x16)
_RF95_REG_1A_AFC_FEI_CTL = const(0x1A)
_RF95_REG_1B_AFC_MSB = const(0x1B)
_RF95_REG_1C_AFC_LSB = const(0x1C)
_RF95_REG_1D_FEI_MSB = const(0x1D)
_RF95_REG_1E_FEI_LSB = const(0x1E)
_RF95_REG_1F_PREAMBLE_DETECT = const(0x1F)
_RF95_REG_20_RX_TIMEOUT_1 = const(0x20)
_RF95_REG_21_RX_TIMEOUT_2 = const(0x21)
_RF95_REG_22_RX_TIMEOUT_3 = const(0x22)
_RF95_REG_23_RX_DELAY = const(0x23)
_RF95_REG_24_OSC = const(0x24)
_RF95_REG_25_PREAMBLE_MSB = const(0x25)
_RF95_REG_26_PREAMBLE_LSB = const(0x26)
_RF95_REG_27_SYNC_CONFIG = const(0x27)
_RF95_REG_28_SYNC_VALUE_1 = const(0x28)
_RF95_REG_29_SYNC_VALUE_2 = const(0x29)
_RF95_REG_2A_SYNC_VALUE_3 = const(0x2A)
_RF95_REG_2B_SYNC_VALUE_4 = const(0x2B)
_RF95_REG_2C_SYNC_VALUE_5 = const(0x2C)
_RF95_REG_2D_SYNC_VALUE_6 = const(0x2D)
_RF95_REG_2E_SYNC_VALUE_7 = const(0x2E)
_RF95_REG_2F_SYNC_VALUE_8 = const(0x2F)
_RF95_REG_30_PACKET_CONFIG_1 = const(0x30)
_RF95_REG_31_PACKET_CONFIG_2 = const(0x31)
_RF95_REG_32_PAYLOAD_LENGTH = const(0x32)
_RF95_REG_33_NODE_ADDR = const(0x33)
_RF95_REG_34_BROADCAST_ADDR = const(0x34)
_RF95_REG_35_FIFO_THRESH = const(0x35)
_RF95_REG_36_SEQ_CFG_1 = const(0x36)
_RF95_REG_37_SEQ_CFG_2 = const(0x37)
_RF95_REG_38_TIMER_RES = const(0x38)
_RF95_REG_39_TIMER1_COEF = const(0x39)
_RF95_REG_3A_TIMER2_COEF = const(0x3A)
_RF95_REG_3B_IMAGE_CAL = const(0x3B)
_RF95_REG_3C_TEMP = const(0x3C)
_RF95_REG_3D_LOW_BAT = const(0x3D)
_RF95_REG_3E_IRQ_FLAGS_1 = const(0x3E)
_RF95_REG_3F_IRQ_FLAGS_2 = const(0x3F)

_RF95_REG_40_DIO_MAPPING1 = const(0x40)
_RF95_REG_41_DIO_MAPPING2 = const(0x41)
_RF95_REG_42_VERSION = const(0x42)

_RF95_REG_44_PIII_IOP = const(0x44)

_RF95_REG_4B_TCXO = const(0x4B)
_RF95_REG_4D_PA_DAC = const(0x4D)
_RF95_REG_5B_FORMER_TEMP = const(0x5B)
_RF95_REG_5B_BIT_RATE_FRAC = const(0x5D)
_RF95_REG_61_AGC_REF = const(0x61)
_RF95_REG_62_AGC_THRESH1 = const(0x62)
_RF95_REG_63_AGC_THRESH2 = const(0x63)
_RF95_REG_64_AGC_THRESH3 = const(0x64)


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
# pylint: disable=too-many-public-methods
class RFM9xFSK(RFMSPI):
    """Interface to a RFM95/6/7/8 FSK radio module.  Allows sending and
    receiving bytes of data in FSK  mode at a support board frequency
    (433/915mhz).

    :param busio.SPI spi: The SPI bus connected to the chip.  Ensure SCK, MOSI, and MISO are
        connected.
    :param ~digitalio.DigitalInOut cs: A DigitalInOut object connected to the chip's CS/chip select
        line.
    :param ~digitalio.DigitalInOut reset: A DigitalInOut object connected to the chip's RST/reset
        line.
    :param int frequency: The center frequency to configure for radio transmission and reception.
        Must be a frequency supported by your hardware (i.e. either 433 or 915mhz).
    :param bytes sync_word: A byte string up to 8 bytes long which represents the syncronization
        word used by received and transmitted packets. Read the datasheet for a full understanding
        of this value! However by default the library will set a value that matches the RadioHead
        Arduino library.
    :param int preamble_length: The number of bytes to pre-pend to a data packet as a preamble.
        This is by default 4 to match the RadioHead library.
    :param bool high_power: Indicate if the chip is a high power variant that supports boosted
        transmission power.  The default is True as it supports the common RFM69HCW modules sold by
        Adafruit.

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
    modulation_shaping = RFMSPI.RegisterBits(_RF95_REG_0A_PA_RAMP, offset=5, bits=2)
    # Long range/LoRa mode can only be set in sleep mode!
    long_range_mode = RFMSPI.RegisterBits(_RF95_REG_01_OP_MODE, offset=7, bits=1)
    sync_on = RFMSPI.RegisterBits(_RF95_REG_27_SYNC_CONFIG, offset=4, bits=1)
    sync_size = RFMSPI.RegisterBits(_RF95_REG_27_SYNC_CONFIG, offset=0, bits=3)
    output_power = RFMSPI.RegisterBits(_RF95_REG_09_PA_CONFIG, bits=4)
    max_power = RFMSPI.RegisterBits(_RF95_REG_09_PA_CONFIG, offset=4, bits=3)
    pa_select = RFMSPI.RegisterBits(_RF95_REG_09_PA_CONFIG, offset=7, bits=1)
    pa_dac = RFMSPI.RegisterBits(_RF95_REG_4D_PA_DAC, bits=3)
    dio0_mapping = RFMSPI.RegisterBits(_RF95_REG_40_DIO_MAPPING1, offset=6, bits=2)
    lna_boost_hf = RFMSPI.RegisterBits(_RF95_REG_0C_LNA, offset=0, bits=2)
    rx_bw_mantissa = RFMSPI.RegisterBits(_RF95_REG_12_RX_BW, offset=3, bits=2)
    rx_bw_exponent = RFMSPI.RegisterBits(_RF95_REG_12_RX_BW, offset=0, bits=3)
    afc_bw_mantissa = RFMSPI.RegisterBits(_RF95_REG_13_AFC_BW, offset=3, bits=2)
    afc_bw_exponent = RFMSPI.RegisterBits(_RF95_REG_13_AFC_BW, offset=0, bits=3)
    packet_format = RFMSPI.RegisterBits(_RF95_REG_30_PACKET_CONFIG_1, offset=7, bits=1)
    dc_free = RFMSPI.RegisterBits(_RF95_REG_30_PACKET_CONFIG_1, offset=5, bits=2)
    crc_on = RFMSPI.RegisterBits(_RF95_REG_30_PACKET_CONFIG_1, offset=4, bits=1)
    crc_auto_clear_off = RFMSPI.RegisterBits(_RF95_REG_30_PACKET_CONFIG_1, offset=3, bits=1)
    address_filter = RFMSPI.RegisterBits(_RF95_REG_30_PACKET_CONFIG_1, offset=1, bits=2)
    crc_type = RFMSPI.RegisterBits(_RF95_REG_30_PACKET_CONFIG_1, offset=0, bits=1)
    mode_ready = RFMSPI.RegisterBits(_RF95_REG_3E_IRQ_FLAGS_1, offset=7)
    ook_bit_sync_on = RFMSPI.RegisterBits(_RF95_REG_14_OOK_PEAK, offset=5, bits=1)
    ook_thresh_type = RFMSPI.RegisterBits(_RF95_REG_14_OOK_PEAK, offset=4, bits=2)
    ook_thresh_step = RFMSPI.RegisterBits(_RF95_REG_14_OOK_PEAK, offset=0, bits=3)
    ook_peak_thresh_dec = RFMSPI.RegisterBits(_RF95_REG_16_OOK_AVG, offset=5, bits=3)
    ook_average_offset = RFMSPI.RegisterBits(_RF95_REG_16_OOK_AVG, offset=2, bits=2)
    ook_average_thresh_filt = RFMSPI.RegisterBits(_RF95_REG_16_OOK_AVG, offset=0, bits=2)

    def __init__(  # noqa: PLR0913
        self,
        spi: busio.SPI,
        cs: digitalio.DigitalInOut,  # pylint: disable=invalid-name
        rst: digitalio.DigitalInOut,
        frequency: int,
        *,
        sync_word: bytes = b"\x2d\xd4",
        preamble_length: int = 4,
        high_power: bool = True,
        baudrate: int = 5000000,
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
        self.long_range_mode = False
        if self.operation_mode != SLEEP_MODE or self.long_range_mode:
            raise RuntimeError("Failed to configure radio for FSK mode, check wiring!")
        # clear default setting for access to LF registers if frequency > 525MHz
        if frequency > 525:
            self.low_frequency_mode = 0
        # Set mode idle
        self.idle()
        # Setup the chip in a similar way to the RadioHead RFM69 library.
        # Set FIFO TX condition to not empty and the default FIFO threshold to 15.
        self.write_u8(_RF95_REG_35_FIFO_THRESH, 0b10001111)
        # Set the syncronization word.
        self.sync_word = sync_word
        self.preamble_length = preamble_length  # Set the preamble length.
        self.frequency_mhz = frequency  # Set frequency.
        # Configure modulation for RadioHead library GFSK_Rb250Fd250 mode
        # by default.  Users with advanced knowledge can manually reconfigure
        # for any other mode (consulting the datasheet is absolutely
        # necessary!).
        self.modulation_shaping = 0b01  # Gaussian filter, BT=1.0
        self.bitrate = 250000  # 250kbs
        self.frequency_deviation = 250000  # 250khz
        self.rx_bw_mantissa = 0b00
        self.rx_bw_exponent = 0b000
        self.afc_bw_mantissa = 0b00
        self.afc_bw_exponent = 0b000
        self.packet_format = 1  # Variable length.
        self.dc_free = 0b10  # Whitening
        # Set transmit power to 13 dBm, a safe value any module supports.
        self._tx_power = 13
        self.tx_power = self._tx_power

        # Default to enable CRC checking on incoming packets.
        self.enable_crc = crc
        """CRC Enable state"""
        self.snr = None

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
        self.dio0_mapping = 0b00  # Interrupt on tx done.

    @property
    def sync_word(self) -> bytearray:
        """The synchronization word value.  This is a byte string up to 8 bytes long (64 bits)
        which indicates the synchronization word for transmitted and received packets. Any
        received packet which does not include this sync word will be ignored. The default value
        is 0x2D, 0xD4 which matches the RadioHead RFM69 library. Setting a value of None will
        disable synchronization word matching entirely.
        """
        # Handle when sync word is disabled..
        if not self.sync_on:
            return None
        # Sync word is not disabled so read the current value.
        sync_word_length = self.sync_size + 1  # Sync word size is offset by 1
        # according to datasheet.
        sync_word = bytearray(sync_word_length)
        self.read_into(_RF95_REG_28_SYNC_VALUE_1, sync_word)
        return sync_word

    @sync_word.setter
    def sync_word(self, val: Optional[bytearray]) -> None:
        # Handle disabling sync word when None value is set.
        if val is None:
            self.sync_on = 0
        else:
            # Check sync word is at most 8 bytes.
            assert 1 <= len(val) <= 8
            # Update the value, size and turn on the sync word.
            self.write_from(_RF95_REG_28_SYNC_VALUE_1, val)
            self.sync_size = len(val) - 1  # Again sync word size is offset by
            # 1 according to datasheet.
            self.sync_on = 1

    @property
    def bitrate(self) -> float:
        """The modulation bitrate in bits/second (or chip rate if Manchester encoding is enabled).
        Can be a value from ~489 to 32mbit/s, but see the datasheet for the exact supported
        values.
        """
        msb = self.read_u8(_RF95_REG_02_BITRATE_MSB)
        lsb = self.read_u8(_RF95_REG_03_BITRATE_LSB)
        return _RF95_FXOSC / ((msb << 8) | lsb)

    @bitrate.setter
    def bitrate(self, val: float) -> None:
        assert (_RF95_FXOSC / 65535) <= val <= 32000000.0
        # Round up to the next closest bit-rate value with addition of 0.5.
        bitrate = int((_RF95_FXOSC / val) + 0.5) & 0xFFFF
        self.write_u8(_RF95_REG_02_BITRATE_MSB, bitrate >> 8)
        self.write_u8(_RF95_REG_03_BITRATE_LSB, bitrate & 0xFF)

    @property
    def frequency_deviation(self) -> float:
        """The frequency deviation in Hertz."""
        msb = self.read_u8(_RF95_REG_04_FDEV_MSB)
        lsb = self.read_u8(_RF95_REG_05_FDEV_LSB)
        return _RF95_FSTEP * ((msb << 8) | lsb)

    @frequency_deviation.setter
    def frequency_deviation(self, val: float) -> None:
        assert 0 <= val <= (_RF95_FSTEP * 16383)  # fdev is a 14-bit unsigned value
        # Round up to the next closest integer value with addition of 0.5.
        fdev = int((val / _RF95_FSTEP) + 0.5) & 0x3FFF
        self.write_u8(_RF95_REG_04_FDEV_MSB, fdev >> 8)
        self.write_u8(_RF95_REG_05_FDEV_LSB, fdev & 0xFF)

    @property
    def temperature(self) -> float:
        """The internal temperature of the chip.. See Sec 5.5.7 of the DataSheet
        calibrated or very accurate.
        """
        temp = self.read_u8(_RF95_REG_3C_TEMP)
        return temp

    @property
    def preamble_length(self) -> int:
        """The length of the preamble for sent and received packets, an unsigned
        16-bit value.  Received packets must match this length or they are
        ignored! Set to 4 to match the RF69.
        """
        msb = self.read_u8(_RF95_REG_25_PREAMBLE_MSB)
        lsb = self.read_u8(_RF95_REG_26_PREAMBLE_LSB)
        return ((msb << 8) | lsb) & 0xFFFF

    @preamble_length.setter
    def preamble_length(self, val: int) -> None:
        assert 0 <= val <= 65535
        self.write_u8(_RF95_REG_25_PREAMBLE_MSB, (val >> 8) & 0xFF)
        self.write_u8(_RF95_REG_26_PREAMBLE_LSB, val & 0xFF)

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
        raw_rssi = self.read_u8(_RF95_REG_11_RSSI_VALUE)
        return -raw_rssi / 2.0

    @property
    def enable_crc(self) -> bool:
        """Set to True to enable hardware CRC checking of incoming packets.
        Incoming packets that fail the CRC check are not processed.  Set to
        False to disable CRC checking and process all incoming packets."""
        return self.crc_on

    @enable_crc.setter
    def enable_crc(self, val: bool) -> None:
        # Optionally enable CRC checking on incoming packets.
        if val:
            self.crc_on = 1
            self.crc_type = 0  # use CCITT for RF69 compatibility
        else:
            self.crc_on = 0

    @property
    def crc_error(self) -> bool:
        """crc status"""
        return (self.read_u8(_RF95_REG_3F_IRQ_FLAGS_2) & 0x2) >> 1

    @property
    def enable_address_filter(self) -> bool:
        """Set to True to enable address filtering.
        Incoming packets that do no match the node address  or broadcast address
        will be ignored."""
        return self.address_filter

    @enable_address_filter.setter
    def enable_address_filter(self, val: bool) -> None:
        # Enable address filtering  on incoming packets.
        if val:
            self.address_filter = 2  # accept node address or broadcast address
        else:
            self.address_filter = 0

    @property
    def fsk_node_address(self) -> int:
        """Node Address for Address Filtering"""
        return self.read_u8(_RF95_REG_33_NODE_ADDR)

    @fsk_node_address.setter
    def fsk_node_address(self, val: int) -> None:
        assert 0 <= val <= 255
        self.write_u8(_RF95_REG_33_NODE_ADDR, val)

    @property
    def fsk_broadcast_address(self) -> int:
        """Node Address for Address Filtering"""
        return self.read_u8(_RF95_REG_34_BROADCAST_ADDR)

    @fsk_broadcast_address.setter
    def fsk_broadcast_address(self, val: int) -> None:
        assert 0 <= val <= 255
        self.write_u8(_RF95_REG_34_BROADCAST_ADDR, val)

    @property
    def ook_fixed_threshold(self) -> int:
        """Fixed threshold for data slicer in OOK mode"""
        return self.read_u8(_RF95_REG_15_OOK_FIX)

    @ook_fixed_threshold.setter
    def ook_fixed_threshold(self, val: int) -> None:
        assert 0 <= val <= 255
        self.write_u8(_RF95_REG_15_OOK_FIX, val)

    def packet_sent(self) -> bool:
        """Transmit status"""
        return (self.read_u8(_RF95_REG_3F_IRQ_FLAGS_2) & 0x8) >> 3

    def payload_ready(self) -> bool:
        """Receive status"""
        return (self.read_u8(_RF95_REG_3F_IRQ_FLAGS_2) & 0x4) >> 2

    def clear_interrupt(self) -> None:
        """Clear interrupt Flags"""
        self.write_u8(_RF95_REG_3E_IRQ_FLAGS_1, 0xFF)
        self.write_u8(_RF95_REG_3F_IRQ_FLAGS_2, 0xFF)

    def fill_fifo(self, payload: ReadableBuffer) -> None:
        """Write the payload to the FIFO."""
        complete_payload = bytearray(1)  # prepend packet length to payload
        complete_payload[0] = len(payload)
        # put the payload lengthe in the beginning of the packet for RFM69
        complete_payload = complete_payload + payload
        # Write payload to transmit fifo
        self.write_from(_RF95_REG_00_FIFO, complete_payload)

    def read_fifo(self) -> Optional[bytearray]:
        """Read the data from the FIFO."""
        # Read the length of the FIFO.
        fifo_length = self.read_u8(_RF95_REG_00_FIFO)
        packet = None  # return None if FIFO empty
        if fifo_length > 0:  # read and clear the FIFO if anything in it
            packet = bytearray(fifo_length)
            # read the packet
            self.read_into(_RF95_REG_00_FIFO, packet, fifo_length)
        return packet
