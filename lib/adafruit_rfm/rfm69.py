# SPDX-FileCopyrightText: 2024 Jerry Needell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_rfm.rfm69`
====================================================

CircuitPython RFM69 packet radio module. This supports sending and
receiving of packets with RFM69 series radios (433/915Mhz).

.. warning:: This is NOT for LoRa radios!

.. note:: This is a 'best effort' at receiving data using pure Python code. You might lose packets
    if they're sent too quickly for the board to process them.

* Author(s): Jerry Needell
"""

import time

from micropython import const

from adafruit_rfm.rfm_common import RFMSPI, ticks_diff

HAS_SUPERVISOR = False

try:
    import supervisor

    if hasattr(supervisor, "ticks_ms"):
        HAS_SUPERVISOR = True
except ImportError:
    pass

try:
    from typing import Optional

    import busio
    import digitalio
    from circuitpython_typing import ReadableBuffer

except ImportError:
    pass


__version__ = "1.0.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_RFM.git"


# Internal constants:
_RF69_REG_00_FIFO = const(0x00)
_RF69_REG_01_OP_MODE = const(0x01)
_RF69_REG_02_DATA_MOD = const(0x02)
_RF69_REG_03_BITRATE_MSB = const(0x03)
_RF69_REG_04_BITRATE_LSB = const(0x04)
_RF69_REG_05_FDEV_MSB = const(0x05)
_RF69_REG_06_FDEV_LSB = const(0x06)
_RF69_REG_07_FRF_MSB = const(0x07)
_RF69_REG_08_FRF_MID = const(0x08)
_RF69_REG_09_FRF_LSB = const(0x09)
_RF69_REG_10_VERSION = const(0x10)
_RF69_REG_11_PA_LEVEL = const(0x11)
_RF69_REG_13_OCP = const(0x13)
_RF69_REG_19_RX_BW = const(0x19)
_RF69_REG_1A_AFC_BW = const(0x1A)
_RF69_REG_1B_OOK_PEAK = const(0x1B)
_RF69_REG_1C_OOK_AVG = const(0x1C)
_RF69_REG_1D_OOK_FIX = const(0x1D)
_RF69_REG_24_RSSI_VALUE = const(0x24)
_RF69_REG_25_DIO_MAPPING1 = const(0x25)
_RF69_REG_27_IRQ_FLAGS1 = const(0x27)
_RF69_REG_28_IRQ_FLAGS2 = const(0x28)
_RF69_REG_2C_PREAMBLE_MSB = const(0x2C)
_RF69_REG_2D_PREAMBLE_LSB = const(0x2D)
_RF69_REG_2E_SYNC_CONFIG = const(0x2E)
_RF69_REG_2F_SYNC_VALUE1 = const(0x2F)
_RF69_REG_39_NODE_ADDR = const(0x39)
_RF69_REG_3A_BROADCAST_ADDR = const(0x3A)
_RF69_REG_37_PACKET_CONFIG1 = const(0x37)
_RF69_REG_3C_FIFO_THRESH = const(0x3C)
_RF69_REG_3D_PACKET_CONFIG2 = const(0x3D)
_RF69_REG_3E_AES_KEY1 = const(0x3E)
_RF69_REG_4E_TEMP1 = const(0x4E)
_RF69_REG_4F_TEMP2 = const(0x4F)
_RF69_REG_5A_TEST_PA1 = const(0x5A)
_RF69_REG_5C_TEST_PA2 = const(0x5C)
_RF69_REG_6F_TEST_DAGC = const(0x6F)

_TEST_PA1_NORMAL = const(0x55)
_TEST_PA1_BOOST = const(0x5D)
_TEST_PA2_NORMAL = const(0x70)
_TEST_PA2_BOOST = const(0x7C)
_OCP_NORMAL = const(0x1A)
_OCP_HIGH_POWER = const(0x0F)

# The crystal oscillator frequency and frequency synthesizer step size.
# See the datasheet for details of this calculation.
_FXOSC = 32000000.0
_FSTEP = _FXOSC / 524288

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
FS_MODE = 0b010
TX_MODE = 0b011
RX_MODE = 0b100


# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-public-methods
class RFM69(RFMSPI):
    """Interface to a RFM69 series packet radio.  Allows simple sending and
    receiving of wireless data at supported frequencies of the radio
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
    :param bytes encryption_key: A 16 byte long string that represents the AES encryption key to use
        when encrypting and decrypting packets.  Both the transmitter and receiver MUST have the
        same key value! By default no encryption key is set or used.
    :param bool high_power: Indicate if the chip is a high power variant that supports boosted
        transmission power.  The default is True as it supports the common RFM69HCW modules sold by
        Adafruit.

    Remember this library makes a best effort at receiving packets with pure Python code.  Trying
    to receive packets too quickly will result in lost data so limit yourself to simple scenarios
    of sending and receiving single packets at a time.

    Also note this library defaults to be compatible with RadioHead Arduino library communication.
    This means the library sets up the radio modulation to match RadioHead's default of GFSK
    encoding, 250kbit/s bitrate, and 250khz frequency deviation. To change this requires explicitly
    setting the radio's bitrate and encoding register bits.
    Read the datasheet and study the init function to see an example of this--advanced users only!
    Advanced RadioHead features like address/node specific packets or "reliable datagram" delivery
    are supported however due to the limitations noted, "reliable datagram" is still subject to
    missed packets.
    """

    # Control bits from the registers of the chip:
    data_mode = RFMSPI.RegisterBits(_RF69_REG_02_DATA_MOD, offset=5, bits=2)
    modulation_type = RFMSPI.RegisterBits(_RF69_REG_02_DATA_MOD, offset=3, bits=2)
    modulation_shaping = RFMSPI.RegisterBits(_RF69_REG_02_DATA_MOD, offset=0, bits=2)
    temp_start = RFMSPI.RegisterBits(_RF69_REG_4E_TEMP1, offset=3)
    temp_running = RFMSPI.RegisterBits(_RF69_REG_4E_TEMP1, offset=2)
    sync_on = RFMSPI.RegisterBits(_RF69_REG_2E_SYNC_CONFIG, offset=7)
    sync_size = RFMSPI.RegisterBits(_RF69_REG_2E_SYNC_CONFIG, offset=3, bits=3)
    aes_on = RFMSPI.RegisterBits(_RF69_REG_3D_PACKET_CONFIG2, offset=0)
    pa_0_on = RFMSPI.RegisterBits(_RF69_REG_11_PA_LEVEL, offset=7)
    pa_1_on = RFMSPI.RegisterBits(_RF69_REG_11_PA_LEVEL, offset=6)
    pa_2_on = RFMSPI.RegisterBits(_RF69_REG_11_PA_LEVEL, offset=5)
    output_power = RFMSPI.RegisterBits(_RF69_REG_11_PA_LEVEL, offset=0, bits=5)
    rx_bw_dcc_freq = RFMSPI.RegisterBits(_RF69_REG_19_RX_BW, offset=5, bits=3)
    rx_bw_mantissa = RFMSPI.RegisterBits(_RF69_REG_19_RX_BW, offset=3, bits=2)
    rx_bw_exponent = RFMSPI.RegisterBits(_RF69_REG_19_RX_BW, offset=0, bits=3)
    afc_bw_dcc_freq = RFMSPI.RegisterBits(_RF69_REG_1A_AFC_BW, offset=5, bits=3)
    afc_bw_mantissa = RFMSPI.RegisterBits(_RF69_REG_1A_AFC_BW, offset=3, bits=2)
    afc_bw_exponent = RFMSPI.RegisterBits(_RF69_REG_1A_AFC_BW, offset=0, bits=3)
    packet_format = RFMSPI.RegisterBits(_RF69_REG_37_PACKET_CONFIG1, offset=7, bits=1)
    dc_free = RFMSPI.RegisterBits(_RF69_REG_37_PACKET_CONFIG1, offset=5, bits=2)
    crc_on = RFMSPI.RegisterBits(_RF69_REG_37_PACKET_CONFIG1, offset=4, bits=1)
    crc_auto_clear_off = RFMSPI.RegisterBits(_RF69_REG_37_PACKET_CONFIG1, offset=3, bits=1)
    address_filter = RFMSPI.RegisterBits(_RF69_REG_37_PACKET_CONFIG1, offset=1, bits=2)
    mode_ready = RFMSPI.RegisterBits(_RF69_REG_27_IRQ_FLAGS1, offset=7)
    dio_0_mapping = RFMSPI.RegisterBits(_RF69_REG_25_DIO_MAPPING1, offset=6, bits=2)
    ook_thresh_type = RFMSPI.RegisterBits(_RF69_REG_1B_OOK_PEAK, offset=6, bits=2)
    ook_thresh_step = RFMSPI.RegisterBits(_RF69_REG_1B_OOK_PEAK, offset=5, bits=3)
    ook_peak_thresh_dec = RFMSPI.RegisterBits(_RF69_REG_1B_OOK_PEAK, offset=0, bits=3)
    ook_average_thresh_filt = RFMSPI.RegisterBits(_RF69_REG_1C_OOK_AVG, offset=6, bits=2)

    # pylint: disable=too-many-statements
    # pylint: disable=too-many-arguments
    def __init__(  # noqa: PLR0913
        self,
        spi: busio.SPI,
        cs: digitalio.DigitalInOut,
        rst: digitalio.DigitalInOut,
        frequency: int,
        *,
        sync_word: bytes = b"\x2d\xd4",
        preamble_length: int = 4,
        encryption_key: Optional[bytes] = None,
        high_power: bool = True,
        baudrate: int = 2000000,
        crc: bool = True,
    ) -> None:
        super().__init__(spi, cs, baudrate=baudrate)

        self.module = "RFM69"
        self.max_packet_length = 60
        self.high_power = high_power
        # Device support SPI mode 0 (polarity & phase = 0) up to a max of 10mhz.
        # self._device = spidev.SPIDevice(spi, cs, baudrate=baudrate, polarity=0, phase=0)
        # Setup reset as a digital output that's low.
        self._rst = rst
        self._rst.switch_to_output(value=False)
        self.reset()  # Reset the chip.
        # Check the version of the chip.
        version = self.read_u8(_RF69_REG_10_VERSION)
        if version not in (0x23, 0x24):
            raise RuntimeError("Invalid RFM69 version, check wiring! ID found:", hex(version))
        self.idle()  # Enter idle state.
        # Setup the chip in a similar way to the RadioHead RFM69 library.
        # Set FIFO TX condition to not empty and the default FIFO threshold to 15.
        self.write_u8(_RF69_REG_3C_FIFO_THRESH, 0b10001111)
        # Configure low beta off.
        self.write_u8(_RF69_REG_6F_TEST_DAGC, 0x30)
        # Set the syncronization word.
        self.sync_word = sync_word
        self.preamble_length = preamble_length  # Set the preamble length.
        self.frequency_mhz = frequency  # Set frequency.
        self.encryption_key = encryption_key  # Set encryption key.
        # Configure modulation for RadioHead library GFSK_Rb250Fd250 mode
        # by default.  Users with advanced knowledge can manually reconfigure
        # for any other mode (consulting the datasheet is absolutely
        # necessary!).
        self.modulation_shaping = 0b01  # Gaussian filter, BT=1.0
        self.bitrate = 250000  # 250kbs
        self.frequency_deviation = 250000  # 250khz
        self.rx_bw_dcc_freq = 0b111  # RxBw register = 0xE0
        self.rx_bw_mantissa = 0b00
        self.rx_bw_exponent = 0b000
        self.afc_bw_dcc_freq = 0b111  # AfcBw register = 0xE0
        self.afc_bw_mantissa = 0b00
        self.afc_bw_exponent = 0b000
        self.packet_format = 1  # Variable length.
        self.dc_free = 0b10  # Whitening
        # Set transmit power to 13 dBm, a safe value any module supports.
        self._tx_power = None
        self.tx_power = 13
        # Default to enable CRC checking on incoming packets.
        self.enable_crc = crc
        self.snr = None

    def reset(self) -> None:
        """Perform a reset of the chip."""
        # See section 7.2.2 of the datasheet for reset description.
        self._rst.value = True
        time.sleep(0.0001)  # 100 us
        self._rst.value = False
        time.sleep(0.005)  # 5 ms

    def disable_boost(self) -> None:
        """Disable preamp boost."""
        if self.high_power:
            self.write_u8(_RF69_REG_5A_TEST_PA1, _TEST_PA1_NORMAL)
            self.write_u8(_RF69_REG_5C_TEST_PA2, _TEST_PA2_NORMAL)
            self.write_u8(_RF69_REG_13_OCP, _OCP_NORMAL)

    def idle(self) -> None:
        """Enter idle standby mode (switching off high power amplifiers if necessary)."""
        # Like RadioHead library, turn off high power boost if enabled.
        self.disable_boost()
        self.operation_mode = STANDBY_MODE

    def sleep(self) -> None:
        """Enter sleep mode."""
        self.operation_mode = SLEEP_MODE

    def listen(self) -> None:
        """Listen for packets to be received by the chip.  Use :py:func:`receive` to listen, wait
        and retrieve packets as they're available.
        """
        # Like RadioHead library, turn off high power boost if enabled.
        self.disable_boost()
        # Enable payload ready interrupt for D0 line.
        self.dio_0_mapping = 0b01
        # Enter RX mode (will clear FIFO!).
        self.operation_mode = RX_MODE

    def transmit(self) -> None:
        """Transmit a packet which is queued in the FIFO.  This is a low level function for
        entering transmit mode and more.  For generating and transmitting a packet of data use
        :py:func:`send` instead.
        """
        # Like RadioHead library, turn on high power boost if needed.
        if self.high_power and (self._tx_power >= 18):
            self.write_u8(_RF69_REG_5A_TEST_PA1, _TEST_PA1_BOOST)
            self.write_u8(_RF69_REG_5C_TEST_PA2, _TEST_PA2_BOOST)
            self.write_u8(_RF69_REG_13_OCP, _OCP_HIGH_POWER)
        # Enable packet sent interrupt for D0 line.
        self.dio_0_mapping = 0b00
        # Enter TX mode (will clear FIFO!).
        self.operation_mode = TX_MODE

    @property
    def temperature(self) -> float:
        """The internal temperature of the chip in degrees Celsius. Be warned this is not
        calibrated or very accurate.

        .. warning:: Reading this will STOP any receiving/sending that might be happening!
        """
        # Start a measurement then poll the measurement finished bit.
        self.temp_start = 1
        while self.temp_running > 0:
            pass
        # Grab the temperature value and convert it to Celsius.
        # This uses the same observed value formula from the Radiohead library.
        temp = self.read_u8(_RF69_REG_4F_TEMP2)
        return 166.0 - temp

    @property
    def operation_mode(self) -> int:
        """The operation mode value.  Unless you're manually controlling the chip you shouldn't
        change the operation_mode with this property as other side-effects are required for
        changing logical modes--use :py:func:`idle`, :py:func:`sleep`, :py:func:`transmit`,
        :py:func:`listen` instead to signal intent for explicit logical modes.
        """
        op_mode = self.read_u8(_RF69_REG_01_OP_MODE)
        return (op_mode >> 2) & 0b111

    @operation_mode.setter
    def operation_mode(self, val: int) -> None:
        assert 0 <= val <= 4
        # Set the mode bits inside the operation mode register.
        op_mode = self.read_u8(_RF69_REG_01_OP_MODE)
        op_mode &= 0b11100011
        op_mode |= val << 2
        self.write_u8(_RF69_REG_01_OP_MODE, op_mode)
        # Wait for mode to change by polling interrupt bit.
        if HAS_SUPERVISOR:
            start = supervisor.ticks_ms()
            while not self.mode_ready:
                if ticks_diff(supervisor.ticks_ms(), start) >= 1000:
                    raise TimeoutError("Operation Mode failed to set.")
        else:
            start = time.monotonic()
            while not self.mode_ready:
                if time.monotonic() - start >= 1:
                    raise TimeoutError("Operation Mode failed to set.")

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
        self.read_into(_RF69_REG_2F_SYNC_VALUE1, sync_word)
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
            self.write_from(_RF69_REG_2F_SYNC_VALUE1, val)
            self.sync_size = len(val) - 1  # Again sync word size is offset by
            # 1 according to datasheet.
            self.sync_on = 1

    @property
    def preamble_length(self) -> int:
        """The length of the preamble for sent and received packets, an unsigned 16-bit value.
        Received packets must match this length or they are ignored! Set to 4 to match the
        RadioHead RFM69 library.
        """
        msb = self.read_u8(_RF69_REG_2C_PREAMBLE_MSB)
        lsb = self.read_u8(_RF69_REG_2D_PREAMBLE_LSB)
        return ((msb << 8) | lsb) & 0xFFFF

    @preamble_length.setter
    def preamble_length(self, val: int) -> None:
        assert 0 <= val <= 65535
        self.write_u8(_RF69_REG_2C_PREAMBLE_MSB, (val >> 8) & 0xFF)
        self.write_u8(_RF69_REG_2D_PREAMBLE_LSB, val & 0xFF)

    @property
    def frequency_mhz(self) -> float:
        """The frequency of the radio in Megahertz. Only the allowed values for your radio must be
        specified (i.e. 433 vs. 915 mhz)!
        """
        # FRF register is computed from the frequency following the datasheet.
        # See section 6.2 and FRF register description.
        # Read bytes of FRF register and assemble into a 24-bit unsigned value.
        msb = self.read_u8(_RF69_REG_07_FRF_MSB)
        mid = self.read_u8(_RF69_REG_08_FRF_MID)
        lsb = self.read_u8(_RF69_REG_09_FRF_LSB)
        frf = ((msb << 16) | (mid << 8) | lsb) & 0xFFFFFF
        frequency = (frf * _FSTEP) / 1000000.0
        return frequency

    @frequency_mhz.setter
    def frequency_mhz(self, val: float) -> None:
        assert 290 <= val <= 1020
        # Calculate FRF register 24-bit value using section 6.2 of the datasheet.
        frf = int((val * 1000000.0) / _FSTEP) & 0xFFFFFF
        # Extract byte values and update registers.
        msb = frf >> 16
        mid = (frf >> 8) & 0xFF
        lsb = frf & 0xFF
        self.write_u8(_RF69_REG_07_FRF_MSB, msb)
        self.write_u8(_RF69_REG_08_FRF_MID, mid)
        self.write_u8(_RF69_REG_09_FRF_LSB, lsb)

    @property
    def encryption_key(self) -> bytearray:
        """The AES encryption key used to encrypt and decrypt packets by the chip. This can be set
        to None to disable encryption (the default), otherwise it must be a 16 byte long byte
        string which defines the key (both the transmitter and receiver must use the same key
        value).
        """
        # Handle if encryption is disabled.
        if self.aes_on == 0:
            return None
        # Encryption is enabled so read the key and return it.
        key = bytearray(16)
        self.read_into(_RF69_REG_3E_AES_KEY1, key)
        return key

    @encryption_key.setter
    def encryption_key(self, val: bytearray) -> None:
        # Handle if unsetting the encryption key (None value).
        if val is None:
            self.aes_on = 0
        else:
            # Set the encryption key and enable encryption.
            assert len(val) == 16
            self.write_from(_RF69_REG_3E_AES_KEY1, val)
            self.aes_on = 1

    @property
    def tx_power(self) -> int:
        """The transmit power in dBm. Can be set to a value from -2 to 20 for high power devices
        (RFM69HCW, high_power=True) or -18 to 13 for low power devices. Only integer power
        levels are actually set (i.e. 12.5 will result in a value of 12 dBm).
        """
        # Follow table 10 truth table from the datasheet for determining power
        # level from the individual PA level bits and output power register.
        pa0 = self.pa_0_on
        pa1 = self.pa_1_on
        pa2 = self.pa_2_on
        current_output_power = self.output_power
        if pa0 and not pa1 and not pa2:
            # -18 to 13 dBm range
            return -18 + current_output_power
        if not pa0 and pa1 and not pa2:
            # -2 to 13 dBm range
            return -18 + current_output_power
        if not pa0 and pa1 and pa2 and self.high_power and self._tx_power < 18:
            # 2 to 17 dBm range
            return -14 + current_output_power
        if not pa0 and pa1 and pa2 and self.high_power and self._tx_power >= 18:
            # 5 to 20 dBm range
            return -11 + current_output_power
        raise RuntimeError("Power amps state unknown!")

    @tx_power.setter
    def tx_power(self, val: float):
        val = int(val)
        # Determine power amplifier and output power values depending on
        # high power state and requested power.
        pa_0_on = pa_1_on = pa_2_on = 0
        output_power = 0
        if self.high_power:
            # Handle high power mode.
            assert -2 <= val <= 20
            pa_1_on = 1
            if val <= 13:
                output_power = val + 18
            elif 13 < val <= 17:
                pa_2_on = 1
                output_power = val + 14
            else:  # power >= 18 dBm
                # Note this also needs PA boost enabled separately!
                pa_2_on = 1
                output_power = val + 11
        else:
            # Handle non-high power mode.
            assert -18 <= val <= 13
            # Enable only power amplifier 0 and set output power.
            pa_0_on = 1
            output_power = val + 18
        # Set power amplifiers and output power as computed above.
        self.pa_0_on = pa_0_on
        self.pa_1_on = pa_1_on
        self.pa_2_on = pa_2_on
        self.output_power = output_power
        self._tx_power = val

    @property
    def rssi(self) -> float:
        """The received strength indicator (in dBm).
        May be inaccuate if not read immediatey. last_rssi contains the value read immediately
        receipt of the last packet.
        """
        # Read RSSI register and convert to value using formula in datasheet.
        return -self.read_u8(_RF69_REG_24_RSSI_VALUE) / 2.0

    @property
    def bitrate(self) -> float:
        """The modulation bitrate in bits/second (or chip rate if Manchester encoding is enabled).
        Can be a value from ~489 to 32mbit/s, but see the datasheet for the exact supported
        values.
        """
        msb = self.read_u8(_RF69_REG_03_BITRATE_MSB)
        lsb = self.read_u8(_RF69_REG_04_BITRATE_LSB)
        return _FXOSC / ((msb << 8) | lsb)

    @bitrate.setter
    def bitrate(self, val: float) -> None:
        assert (_FXOSC / 65535) <= val <= 32000000.0
        # Round up to the next closest bit-rate value with addition of 0.5.
        bitrate = int((_FXOSC / val) + 0.5) & 0xFFFF
        self.write_u8(_RF69_REG_03_BITRATE_MSB, bitrate >> 8)
        self.write_u8(_RF69_REG_04_BITRATE_LSB, bitrate & 0xFF)

    @property
    def frequency_deviation(self) -> float:
        """The frequency deviation in Hertz."""
        msb = self.read_u8(_RF69_REG_05_FDEV_MSB)
        lsb = self.read_u8(_RF69_REG_06_FDEV_LSB)
        return _FSTEP * ((msb << 8) | lsb)

    @frequency_deviation.setter
    def frequency_deviation(self, val: float) -> None:
        assert 0 <= val <= (_FSTEP * 16383)  # fdev is a 14-bit unsigned value
        # Round up to the next closest integer value with addition of 0.5.
        fdev = int((val / _FSTEP) + 0.5) & 0x3FFF
        self.write_u8(_RF69_REG_05_FDEV_MSB, fdev >> 8)
        self.write_u8(_RF69_REG_06_FDEV_LSB, fdev & 0xFF)

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
        else:
            self.crc_on = 0

    @property
    def crc_error(self) -> bool:
        """crc status"""
        return (self.read_u8(_RF69_REG_28_IRQ_FLAGS2) & 0x2) >> 1

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
        return self.read_u8(_RF69_REG_39_NODE_ADDR)

    @fsk_node_address.setter
    def fsk_node_address(self, val: int) -> None:
        assert 0 <= val <= 255
        self.write_u8(_RF69_REG_39_NODE_ADDR, val)

    @property
    def fsk_broadcast_address(self) -> int:
        """Node Address for Address Filtering"""
        return self.read_u8(_RF69_REG_3A_BROADCAST_ADDR)

    @fsk_broadcast_address.setter
    def fsk_broadcast_address(self, val: int) -> None:
        assert 0 <= val <= 255
        self.write_u8(_RF69_REG_3A_BROADCAST_ADDR, val)

    @property
    def ook_fixed_threshold(self) -> int:
        """Fixed threshold for data slicer in OOK mode"""
        return self.read_u8(_RF69_REG_1D_OOK_FIX)

    @ook_fixed_threshold.setter
    def ook_fixed_threshold(self, val: int) -> None:
        assert 0 <= val <= 255
        self.write_u8(_RF69_REG_1D_OOK_FIX, val)

    def packet_sent(self) -> bool:
        """Transmit status"""
        return (self.read_u8(_RF69_REG_28_IRQ_FLAGS2) & 0x8) >> 3

    def payload_ready(self) -> bool:
        """Receive status"""
        return (self.read_u8(_RF69_REG_28_IRQ_FLAGS2) & 0x4) >> 2

    def clear_interrupt(self) -> None:
        """Clear interrupt flags"""
        self.write_u8(_RF69_REG_27_IRQ_FLAGS1, 0xFF)
        self.write_u8(_RF69_REG_28_IRQ_FLAGS2, 0xFF)

    def fill_fifo(self, payload: ReadableBuffer) -> None:
        """Write the payload to the FIFO."""
        complete_payload = bytearray(1)  # prepend packet length to payload
        complete_payload[0] = len(payload)
        # put the payload lengthe in the beginning of the packet for RFM69
        complete_payload = complete_payload + payload
        # Write payload to transmit fifo
        self.write_from(_RF69_REG_00_FIFO, complete_payload)

    def read_fifo(self) -> Optional[bytearray]:
        """Read the packet from the FIFO."""
        # Read the length of the FIFO.
        fifo_length = self.read_u8(_RF69_REG_00_FIFO)
        packet = None  # return None if FIFO empty
        if fifo_length > 0:  # read and clear the FIFO if anything in it
            packet = bytearray(fifo_length)
            # read the packet
            self.read_into(_RF69_REG_00_FIFO, packet, fifo_length)
        return packet
